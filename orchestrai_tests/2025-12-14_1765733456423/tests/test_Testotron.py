import sys
import types
import builtins
from pathlib import Path
import pytest


@pytest.fixture(scope="module")
def testotron_module():
    # Create stub modules to avoid external dependencies at import time
    anth = types.ModuleType("anthropic")

    class APIConnectionError(Exception):
        pass

    class APIError(Exception):
        pass

    # Minimal constants expected by the module
    anth.APIConnectionError = APIConnectionError
    anth.APIError = APIError
    anth.HUMAN_PROMPT = "Human:"
    anth.AI_PROMPT = "Assistant:"

    # Provide a default Anthropic stub; tests will override as needed
    class AnthropicStub:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.messages = types.SimpleNamespace(create=lambda **kwargs: None)

    anth.Anthropic = AnthropicStub

    # Stub dotenv.load_dotenv
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None

    # Stub git.Repo
    git = types.ModuleType("git")

    class RepoStub:
        @classmethod
        def clone_from(cls, url, path):
            raise NotImplementedError("RepoStub.clone_from not overridden in test")

    git.Repo = RepoStub

    # Inject stubs before importing the module under test
    sys.modules["anthropic"] = anth
    sys.modules["dotenv"] = dotenv
    sys.modules["git"] = git

    import importlib
    mod = importlib.import_module("Testotron")
    return mod


def test_clone_repository_skips_when_already_present(tmp_path, monkeypatch, testotron_module):
    mod = testotron_module

    # Point gettempdir to our tmp_path
    monkeypatch.setattr(mod.tempfile, "gettempdir", lambda: str(tmp_path))

    # Create the directory to simulate already-cloned repo
    repo_url = "https://github.com/owner/sample-repo.git"
    expected_repo_dir = tmp_path / "sample-repo"
    expected_repo_dir.mkdir(parents=True, exist_ok=True)

    # Ensure Repo.clone_from would raise if called (should not be called)
    called = {"called": False}

    class RepoDummy:
        @classmethod
        def clone_from(cls, url, path):
            called["called"] = True
            raise AssertionError("clone_from should not be called when repo already present")

    monkeypatch.setattr(mod, "Repo", RepoDummy)

    gen = mod.GitHubTestGenerator(repo_url, "fake-key")
    assert gen.clone_repository() is True
    assert gen.repo_dir == expected_repo_dir
    assert called["called"] is False


def test_clone_repository_clones_when_not_present(tmp_path, monkeypatch, testotron_module):
    mod = testotron_module
    monkeypatch.setattr(mod.tempfile, "gettempdir", lambda: str(tmp_path))

    repo_url = "https://github.com/owner/new-repo.git"
    expected_repo_dir = tmp_path / "new-repo"

    calls = []

    class RepoDummy:
        @classmethod
        def clone_from(cls, url, path):
            calls.append((url, Path(path)))

    monkeypatch.setattr(mod, "Repo", RepoDummy)

    gen = mod.GitHubTestGenerator(repo_url, "fake-key")
    assert gen.clone_repository() is True
    assert gen.repo_dir == expected_repo_dir
    assert calls == [(repo_url, expected_repo_dir)]


def test_clone_repository_returns_false_on_exception(tmp_path, monkeypatch, testotron_module):
    mod = testotron_module
    monkeypatch.setattr(mod.tempfile, "gettempdir", lambda: str(tmp_path))
    repo_url = "https://github.com/owner/repo.git"

    class RepoDummy:
        @classmethod
        def clone_from(cls, url, path):
            raise RuntimeError("clone failed")

    monkeypatch.setattr(mod, "Repo", RepoDummy)

    gen = mod.GitHubTestGenerator(repo_url, "fake-key")
    assert gen.clone_repository() is False


def test_analyze_repository_sets_language_and_framework(testotron_module):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")
    gen.analyze_repository()
    assert gen.language == "python"
    assert gen.test_framework == "pytest"


def test_generate_python_tests_creates_tests_for_multiple_and_nested_files(tmp_path, monkeypatch, testotron_module):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")
    gen.repo_dir = tmp_path

    # Create source Python files
    (tmp_path / "a.py").write_text("def add(a,b):\n    return a+b\n")
    nested_dir = tmp_path / "pkg" / "sub"
    nested_dir.mkdir(parents=True, exist_ok=True)
    (nested_dir / "b.py").write_text("def mul(a,b):\n    return a*b\n")

    # Files that should be skipped
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_existing.py").write_text("# existing test")
    (tmp_path / "contest.py").write_text("x=1")  # contains 'test' -> should be skipped

    generated = []

    def fake_ask(source_code, module_name):
        generated.append(module_name)
        return f"# generated test for {module_name}"

    monkeypatch.setattr(gen, "_ask_claude_to_generate_tests", fake_ask)

    gen._generate_python_tests()

    # Verify generated tests placed in repo_root/tests and only for a.py and b.py
    test_files = sorted((tests_dir).glob("test_*.py"))
    assert [p.name for p in test_files] == ["test_a.py", "test_b.py"]
    assert (tests_dir / "test_a.py").read_text() == "# generated test for a"
    assert (tests_dir / "test_b.py").read_text() == "# generated test for b"
    # Confirm that files containing 'test' in path are skipped (contest.py and existing tests)
    assert "contest" not in generated
    assert "test_existing" not in generated


def test_ask_claude_to_generate_tests_builds_prompt_and_delegates(monkeypatch, testotron_module):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")

    captured = {"prompt": None}

    def fake_call(prompt, max_retries=3, initial_delay=1):
        captured["prompt"] = prompt
        return "OK"

    monkeypatch.setattr(gen, "_call_claude_api", fake_call)

    result = gen._ask_claude_to_generate_tests("SOME_CODE", "mymodule")
    assert result == "OK"
    assert "mymodule" in captured["prompt"]
    assert "SOME_CODE" in captured["prompt"]
    assert "pytest" in captured["prompt"]


def test_call_claude_api_success(monkeypatch, testotron_module):
    mod = testotron_module

    class MessageObj:
        def __init__(self, text):
            self.text = text

    class ResponseObj:
        def __init__(self, text):
            self.content = [MessageObj(text)]

    class AnthropicDummy:
        def __init__(self, api_key=None):
            self.messages = types.SimpleNamespace(
                create=lambda **kwargs: ResponseObj(" success text ")
            )

    monkeypatch.setattr(mod, "Anthropic", AnthropicDummy)

    gen = mod.GitHubTestGenerator("url", "key")
    out = gen._call_claude_api("prompt")
    assert out == "success text"


def test_call_claude_api_retries_on_connection_error_then_succeeds(monkeypatch, testotron_module):
    mod = testotron_module

    # Mock time.sleep despite incorrect import (module has datetime.time). Override with stub providing sleep.
    sleep_calls = []

    class TimeStub:
        @staticmethod
        def sleep(d):
            sleep_calls.append(d)

    monkeypatch.setattr(mod, "time", TimeStub)

    class MessageObj:
        def __init__(self, text):
            self.text = text

    class ResponseObj:
        def __init__(self, text):
            self.content = [MessageObj(text)]

    # Fail once then succeed
    state = {"calls": 0}

    def create_side_effect(**kwargs):
        if state["calls"] == 0:
            state["calls"] += 1
            raise mod.anthropic.APIConnectionError("temporary network issue")
        return ResponseObj("done")

    class AnthropicDummy:
        def __init__(self, api_key=None):
            self.messages = types.SimpleNamespace(create=create_side_effect)

    monkeypatch.setattr(mod, "Anthropic", AnthropicDummy)

    gen = mod.GitHubTestGenerator("url", "key")
    out = gen._call_claude_api("prompt", max_retries=3, initial_delay=2)
    assert out == "done"
    # One retry -> one sleep with initial delay (2 * 2**0)
    assert sleep_calls == [2]


def test_call_claude_api_exhausts_retries_and_raises(monkeypatch, testotron_module):
    mod = testotron_module

    sleep_calls = []

    class TimeStub:
        @staticmethod
        def sleep(d):
            sleep_calls.append(d)

    monkeypatch.setattr(mod, "time", TimeStub)

    def always_fail(**kwargs):
        raise mod.anthropic.APIConnectionError("still failing")

    class AnthropicDummy:
        def __init__(self, api_key=None):
            self.messages = types.SimpleNamespace(create=always_fail)

    monkeypatch.setattr(mod, "Anthropic", AnthropicDummy)

    gen = mod.GitHubTestGenerator("url", "key")
    with pytest.raises(mod.anthropic.APIConnectionError):
        gen._call_claude_api("prompt", max_retries=3, initial_delay=1)

    # Two sleeps for 3 attempts (before final attempt)
    assert sleep_calls == [1, 2]


def test_call_claude_api_apierror_is_raised(monkeypatch, testotron_module, capsys):
    mod = testotron_module

    def fail_api(**kwargs):
        raise mod.anthropic.APIError("bad request")

    class AnthropicDummy:
        def __init__(self, api_key=None):
            self.messages = types.SimpleNamespace(create=fail_api)

    monkeypatch.setattr(mod, "Anthropic", AnthropicDummy)

    gen = mod.GitHubTestGenerator("url", "key")
    with pytest.raises(mod.anthropic.APIError):
        gen._call_claude_api("prompt")

    # Optional: ensure it printed error message
    captured = capsys.readouterr()
    assert "Claude API error" in captured.out


def test_cleanup_removes_repo_dir(tmp_path, testotron_module):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / "file.txt").write_text("data")
    gen.repo_dir = repo_dir
    gen.cleanup()
    assert not repo_dir.exists()


def test_cleanup_handles_none_or_missing_dir(tmp_path, testotron_module):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")
    # None
    gen.cleanup()
    # Missing path
    gen.repo_dir = tmp_path / "not_exists"
    gen.cleanup()
    assert True  # No exceptions


def test_generate_tests_noop_when_non_python(testotron_module, tmp_path, monkeypatch):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")
    gen.repo_dir = tmp_path
    gen.language = "javascript"
    # Should not raise or do anything
    assert gen.generate_tests() is None


def test_run_flow_success(tmp_path, monkeypatch, testotron_module):
    mod = testotron_module

    gen = mod.GitHubTestGenerator("url", "key")

    # Prepare a fake repo dir with source files
    repo_dir = tmp_path / "myrepo"
    repo_dir.mkdir()
    (repo_dir / "x.py").write_text("def f():\n    return 1\n")
    (repo_dir / "tests").mkdir()

    def fake_clone():
        gen.repo_dir = repo_dir
        return True

    monkeypatch.setattr(gen, "clone_repository", fake_clone)

    # Avoid calling actual API
    monkeypatch.setattr(gen, "_ask_claude_to_generate_tests", lambda code, name: f"# test for {name}")

    assert gen.run() is True
    # Tests should have been generated
    assert (repo_dir / "tests" / "test_x.py").exists()
    assert (repo_dir / "tests" / "test_x.py").read_text() == "# test for x"


def test_run_flow_clone_fails(testotron_module, monkeypatch):
    mod = testotron_module
    gen = mod.GitHubTestGenerator("url", "key")
    monkeypatch.setattr(gen, "clone_repository", lambda: False)
    assert gen.run() is False