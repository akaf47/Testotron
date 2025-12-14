import os
import shutil
import tempfile
from pathlib import Path
import types
import uuid
import builtins

import pytest

import Testotron
from Testotron import GitHubTestGenerator


def unique_repo_url():
    name = f"unittest-repo-{uuid.uuid4().hex}"
    return f"https://example.com/{name}.git", name


def repo_path_for(name):
    return Path(tempfile.gettempdir()) / name


def cleanup_path(p: Path):
    if p.exists():
        shutil.rmtree(p)


def test_init_sets_fields():
    url = "https://example.com/repo.git"
    gen = GitHubTestGenerator(url, "key")
    assert gen.repo_url == url
    assert gen.claude_api_key == "key"
    assert gen.repo_dir is None
    assert gen.language is None
    assert gen.test_framework is None


def test_clone_repository_fresh_clone_success(monkeypatch):
    repo_url, name = unique_repo_url()
    target_dir = repo_path_for(name)
    cleanup_path(target_dir)

    calls = []

    def fake_clone_from(url, path):
        calls.append((url, str(path)))
        Path(path).mkdir(parents=True, exist_ok=True)

    # Patch Repo.clone_from
    monkeypatch.setattr(Testotron, "Repo", types.SimpleNamespace(clone_from=fake_clone_from))

    gen = GitHubTestGenerator(repo_url, "key")
    ok = gen.clone_repository()

    assert ok is True
    assert gen.repo_dir == target_dir
    assert calls == [(repo_url, str(target_dir))]

    # Cleanup file system
    gen.cleanup()
    assert not target_dir.exists()


def test_clone_repository_repo_already_exists_skips_clone(monkeypatch, capsys):
    repo_url, name = unique_repo_url()
    target_dir = repo_path_for(name)
    cleanup_path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    called = {"clone": False}

    def fake_clone_from(url, path):
        called["clone"] = True
        raise AssertionError("clone_from should not be called when repo already exists")

    monkeypatch.setattr(Testotron, "Repo", types.SimpleNamespace(clone_from=fake_clone_from))

    gen = GitHubTestGenerator(repo_url, "key")
    ok = gen.clone_repository()

    captured = capsys.readouterr()
    assert "skipping clone" in captured.out
    assert ok is True
    assert called["clone"] is False

    gen.cleanup()
    assert not target_dir.exists()


def test_clone_repository_exception_returns_false(monkeypatch, capsys):
    repo_url, name = unique_repo_url()
    target_dir = repo_path_for(name)
    cleanup_path(target_dir)

    def fake_clone_from(url, path):
        raise RuntimeError("network failure")

    monkeypatch.setattr(Testotron, "Repo", types.SimpleNamespace(clone_from=fake_clone_from))

    gen = GitHubTestGenerator(repo_url, "key")
    ok = gen.clone_repository()

    captured = capsys.readouterr()
    assert ok is False
    assert "Error cloning repository" in captured.out
    # Directory should not have been created by our fake
    assert not target_dir.exists()


def test_analyze_repository_sets_language_and_framework():
    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    gen.analyze_repository()
    assert gen.language == "python"
    assert gen.test_framework == "pytest"


def test_generate_tests_dispatch_python_and_unknown(monkeypatch):
    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    gen.repo_dir = Path(tempfile.gettempdir()) / f"dummy-{uuid.uuid4().hex}"

    called = {"python": 0}

    def fake_generate_python_tests(self=None):
        called["python"] += 1

    monkeypatch.setattr(GitHubTestGenerator, "_generate_python_tests", fake_generate_python_tests)

    # Python path
    gen.language = "python"
    result = gen.generate_tests()
    assert result is None  # underlying returns None
    assert called["python"] == 1

    # Unknown language path
    gen.language = "javascript"
    result = gen.generate_tests()
    assert result is None
    assert called["python"] == 1  # unchanged


def test_generate_python_tests_creates_tests_and_skips(monkeypatch):
    # Prepare a fake repository structure
    repo_root = Path(tempfile.gettempdir()) / f"repo-{uuid.uuid4().hex}"
    cleanup_path(repo_root)
    (repo_root / "subdir").mkdir(parents=True)
    (repo_root / "tests").mkdir(parents=True)
    (repo_root / "integration_tests").mkdir(parents=True)
    (repo_root / "subdir" / "nested").mkdir(parents=True)

    # Files to include
    (repo_root / "main.py").write_text("def add(a,b): return a+b")
    (repo_root / "subdir" / "util.py").write_text("def mul(a,b): return a*b")

    # Files to skip
    (repo_root / "tests" / "test_existing.py").write_text("def test_x(): pass")
    (repo_root / "contest.py").write_text("# has 'test' in name -> should skip")
    (repo_root / "integration_tests" / "helper.py").write_text("# path contains 'tests' -> skip")
    (repo_root / "subdir" / "nested" / "data_test_support.py").write_text("# contains 'test' -> skip")

    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    gen.repo_dir = repo_root

    created = []

    def fake_ask(self, source_code, module_name):
        created.append(module_name)
        return f"# generated tests for {module_name}"

    monkeypatch.setattr(GitHubTestGenerator, "_ask_claude_to_generate_tests", fake_ask)

    gen._generate_python_tests()

    test_dir = repo_root / "tests"
    # Only main.py and util.py should have tests generated
    assert (test_dir / "test_main.py").exists()
    assert (test_dir / "test_util.py").exists()
    assert (test_dir / "test_contest.py").exists() is False
    assert (test_dir / "test_helper.py").exists() is False
    assert (test_dir / "test_data_test_support.py").exists() is False

    assert (test_dir / "test_main.py").read_text() == "# generated tests for main"
    assert (test_dir / "test_util.py").read_text() == "# generated tests for util"

    # Cleanup
    cleanup_path(repo_root)


def test_ask_claude_to_generate_tests_prompt_composition(monkeypatch):
    gen = GitHubTestGenerator("https://example.com/repo.git", "key")

    recorded = {}

    def fake_call(self, prompt, max_retries=3, initial_delay=1):
        recorded["prompt"] = prompt
        return "OK-RESULT"

    monkeypatch.setattr(GitHubTestGenerator, "_call_claude_api", fake_call)

    src = "def hello():\n    print('hi')\n"
    mod_name = "mymodule"
    result = gen._ask_claude_to_generate_tests(src, mod_name)

    assert result == "OK-RESULT"
    assert mod_name in recorded["prompt"]
    assert src in recorded["prompt"]
    assert "pytest" in recorded["prompt"]


def test_call_claude_api_happy_path_returns_stripped(monkeypatch):
    # Fake client returning a message with whitespace to ensure strip() is applied
    class FakeMessages:
        def create(self, **kwargs):
            return types.SimpleNamespace(content=[types.SimpleNamespace(text="  test content  \n")])

    class FakeClient:
        def __init__(self, api_key=None):
            self.messages = FakeMessages()

    # Patch Testotron.Anthropic to our fake
    monkeypatch.setattr(Testotron, "Anthropic", FakeClient)

    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    out = gen._call_claude_api("prompt here")
    assert out == "test content"


def test_call_claude_api_retries_with_exponential_backoff_then_success(monkeypatch):
    # Provide fake exception classes via Testotron.anthropic
    class APIConnectionError(Exception):
        pass

    class APIError(Exception):
        pass

    monkeypatch.setattr(Testotron, "anthropic", types.SimpleNamespace(APIConnectionError=APIConnectionError, APIError=APIError))

    # Fake client that fails twice with APIConnectionError then succeeds
    call_counter = {"count": 0}

    class FakeMessages:
        def create(self, **kwargs):
            call_counter["count"] += 1
            if call_counter["count"] <= 2:
                raise APIConnectionError("temporary network issue")
            return types.SimpleNamespace(content=[types.SimpleNamespace(text="ok")])

    class FakeClient:
        def __init__(self, api_key=None):
            self.messages = FakeMessages()

    # Track sleeps
    delays = []

    class FakeTime:
        @staticmethod
        def sleep(d):
            delays.append(d)

    monkeypatch.setattr(Testotron, "Anthropic", FakeClient)
    # Patch the erroneously imported 'time' symbol to something with sleep
    monkeypatch.setattr(Testotron, "time", FakeTime)

    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    result = gen._call_claude_api("prompt", max_retries=3, initial_delay=2)

    assert result == "ok"
    # Expect two sleeps: 2^0*2, 2^1*2 => 2, 4
    assert delays == [2, 4]
    assert call_counter["count"] == 3


def test_call_claude_api_api_error_prints_and_raises(monkeypatch, capsys):
    # Provide fake exception classes via Testotron.anthropic
    class APIConnectionError(Exception):
        pass

    class APIError(Exception):
        pass

    monkeypatch.setattr(Testotron, "anthropic", types.SimpleNamespace(APIConnectionError=APIConnectionError, APIError=APIError))

    def will_raise_api_error(**kwargs):
        raise APIError("bad request")

    class FakeMessages:
        def create(self, **kwargs):
            return will_raise_api_error(**kwargs)

    class FakeClient:
        def __init__(self, api_key=None):
            self.messages = FakeMessages()

    class FakeTime:
        @staticmethod
        def sleep(d):
            raise AssertionError("sleep should not be called on APIError")

    monkeypatch.setattr(Testotron, "Anthropic", FakeClient)
    monkeypatch.setattr(Testotron, "time", FakeTime)

    gen = GitHubTestGenerator("https://example.com/repo.git", "key")

    with pytest.raises(APIError):
        gen._call_claude_api("prompt", max_retries=5, initial_delay=10)

    captured = capsys.readouterr()
    assert "Claude API error" in captured.out


def test_cleanup_with_and_without_existing_repo_dir():
    # Without repo_dir set
    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    gen.cleanup()  # Should not raise

    # With repo_dir set and existing nested structure
    root = Path(tempfile.gettempdir()) / f"repo-{uuid.uuid4().hex}"
    (root / "nested" / "deep").mkdir(parents=True)
    (root / "nested" / "deep" / "file.txt").write_text("data")

    gen.repo_dir = root
    assert root.exists()
    gen.cleanup()
    assert not root.exists()


def test_run_success_flow(monkeypatch, capsys):
    repo_root = Path(tempfile.gettempdir()) / f"repo-{uuid.uuid4().hex}"

    def fake_clone(self):
        self.repo_dir = repo_root
        if not self.repo_dir.exists():
            self.repo_dir.mkdir(parents=True)
        return True

    called = {"gen": 0}

    def fake_generate(self):
        called["gen"] += 1

    monkeypatch.setattr(GitHubTestGenerator, "clone_repository", fake_clone)
    monkeypatch.setattr(GitHubTestGenerator, "_generate_python_tests", fake_generate)

    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    ok = gen.run()
    captured = capsys.readouterr()

    assert ok is True
    assert "Unit tests generated" in captured.out
    assert gen.language == "python"  # set by analyze_repository during run
    assert called["gen"] == 1

    # Cleanup
    gen.cleanup()


def test_run_clone_failure_short_circuits(monkeypatch):
    def fake_clone(self):
        return False

    flags = {"analyze": 0, "gen": 0}

    def fake_analyze(self):
        flags["analyze"] += 1

    def fake_generate(self):
        flags["gen"] += 1

    monkeypatch.setattr(GitHubTestGenerator, "clone_repository", fake_clone)
    monkeypatch.setattr(GitHubTestGenerator, "analyze_repository", fake_analyze)
    monkeypatch.setattr(GitHubTestGenerator, "generate_tests", fake_generate)

    gen = GitHubTestGenerator("https://example.com/repo.git", "key")
    ok = gen.run()

    assert ok is False
    assert flags["analyze"] == 0
    assert flags["gen"] == 0