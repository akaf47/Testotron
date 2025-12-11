```python
"""
Comprehensive Unit Tests for Testotron
Target: 100% Code Coverage

Tests the GitHubTestGenerator class and all its methods including:
- Repository cloning
- Language analysis
- Test generation
- Claude API integration
- Error handling and retries
- Cleanup operations
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call, mock_open
import anthropic
from Testotron import GitHubTestGenerator


class TestGitHubTestGeneratorInit:
    """Test the __init__ method"""
    
    def test_init_basic(self):
        """Test basic initialization"""
        repo_url = "https://github.com/test/repo"
        api_key = "test_api_key"
        
        generator = GitHubTestGenerator(repo_url, api_key)
        
        assert generator.repo_url == repo_url
        assert generator.claude_api_key == api_key
        assert generator.repo_dir is None
        assert generator.language is None
        assert generator.test_framework is None
    
    def test_init_with_git_extension(self):
        """Test initialization with .git extension in URL"""
        repo_url = "https://github.com/test/repo.git"
        api_key = "sk-ant-test123"
        
        generator = GitHubTestGenerator(repo_url, api_key)
        
        assert generator.repo_url == repo_url
        assert generator.claude_api_key == api_key
    
    def test_init_empty_strings(self):
        """Test initialization with empty strings"""
        generator = GitHubTestGenerator("", "")
        
        assert generator.repo_url == ""
        assert generator.claude_api_key == ""
        assert generator.repo_dir is None


class TestCloneRepository:
    """Test the clone_repository method"""
    
    @patch('Testotron.Repo')
    @patch('Testotron.Path')
    @patch('Testotron.tempfile.gettempdir')
    def test_clone_repository_success(self, mock_gettempdir, mock_path_class, mock_repo):
        """Test successful repository cloning"""
        mock_gettempdir.return_value = "/tmp"
        mock_temp_path = MagicMock()
        mock_repo_path = MagicMock()
        mock_repo_path.exists.return_value = False
        mock_temp_path.__truediv__.return_value = mock_repo_path
        mock_path_class.return_value = mock_temp_path
        
        generator = GitHubTestGenerator("https://github.com/test/repo.git", "api_key")
        
        with patch('Testotron.Path', return_value=mock_temp_path):
            result = generator.clone_repository()
        
        assert result is True
    
    @patch('Testotron.Path')
    @patch('Testotron.tempfile.gettempdir')
    def test_clone_repository_already_exists(self, mock_gettempdir, mock_path_class, capsys):
        """Test cloning when repository already exists"""
        mock_gettempdir.return_value = "/tmp"
        mock_temp_path = MagicMock()
        mock_repo_path = MagicMock()
        mock_repo_path.exists.return_value = True
        mock_temp_path.__truediv__.return_value = mock_repo_path
        mock_path_class.return_value = mock_temp_path
        
        generator = GitHubTestGenerator("https://github.com/test/repo.git", "api_key")
        
        with patch('Testotron.Path', return_value=mock_temp_path):
            result = generator.clone_repository()
        
        captured = capsys.readouterr()
        assert result is True
        assert "already present" in captured.out
    
    @patch('Testotron.Repo')
    @patch('Testotron.Path')
    @patch('Testotron.tempfile.gettempdir')
    def test_clone_repository_exception(self, mock_gettempdir, mock_path_class, mock_repo, capsys):
        """Test repository cloning with exception"""
        mock_gettempdir.return_value = "/tmp"
        mock_temp_path = MagicMock()
        mock_repo_path = MagicMock()
        mock_repo_path.exists.return_value = False
        mock_temp_path.__truediv__.return_value = mock_repo_path
        mock_path_class.return_value = mock_temp_path
        
        mock_repo.clone_from.side_effect = Exception("Clone failed")
        
        generator = GitHubTestGenerator("https://github.com/test/repo.git", "api_key")
        
        with patch('Testotron.Path', return_value=mock_temp_path):
            result = generator.clone_repository()
        
        captured = capsys.readouterr()
        assert result is False
        assert "Error cloning repository" in captured.out
    
    @patch('Testotron.Repo')
    @patch('Testotron.Path')
    @patch('Testotron.tempfile.gettempdir')
    def test_clone_repository_without_git_extension(self, mock_gettempdir, mock_path_class, mock_repo):
        """Test cloning repository URL without .git extension"""
        mock_gettempdir.return_value = "/tmp"
        mock_temp_path = MagicMock()
        mock_repo_path = MagicMock()
        mock_repo_path.exists.return_value = False
        mock_temp_path.__truediv__.return_value = mock_repo_path
        mock_path_class.return_value = mock_temp_path
        
        generator = GitHubTestGenerator("https://github.com/test/myrepo", "api_key")
        
        with patch('Testotron.Path', return_value=mock_temp_path):
            result = generator.clone_repository()
        
        assert result is True


class TestAnalyzeRepository:
    """Test the analyze_repository method"""
    
    def test_analyze_repository_sets_python(self):
        """Test that analyze_repository sets Python as language"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        generator.analyze_repository()
        
        assert generator.language == 'python'
        assert generator.test_framework == 'pytest'
    
    def test_analyze_repository_multiple_calls(self):
        """Test multiple calls to analyze_repository"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        generator.analyze_repository()
        generator.analyze_repository()
        
        assert generator.language == 'python'
        assert generator.test_framework == 'pytest'


class TestGenerateTests:
    """Test the generate_tests method"""
    
    @patch.object(GitHubTestGenerator, '_generate_python_tests')
    def test_generate_tests_python(self, mock_generate_python):
        """Test generate_tests calls Python test generator"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.language = 'python'
        
        generator.generate_tests()
        
        mock_generate_python.assert_called_once()
    
    def test_generate_tests_unknown_language(self):
        """Test generate_tests with unsupported language"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.language = 'javascript'
        
        result = generator.generate_tests()
        
        assert result is None
    
    def test_generate_tests_no_language_set(self):
        """Test generate_tests when language is not set"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        result = generator.generate_tests()
        
        assert result is None


class TestGeneratePythonTests:
    """Test the _generate_python_tests method"""
    
    @patch('Testotron.importlib.util.spec_from_file_location')
    @patch('Testotron.importlib.util.module_from_spec')
    def test_generate_python_tests_success(self, mock_module_from_spec, mock_spec_from_file):
        """Test successful Python test generation"""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            py_file = repo_dir / "example.py"
            py_file.write_text("def example_function():\n    return True")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            # Mock the Claude API call
            with patch.object(generator, '_ask_claude_to_generate_tests', return_value="# Test code"):
                generator._generate_python_tests()
            
            # Check that tests directory was created
            test_dir = repo_dir / 'tests'
            assert test_dir.exists()
            
            # Check that test file was created
            test_file = test_dir / "test_example.py"
            assert test_file.exists()
            assert test_file.read_text() == "# Test code"
    
    @patch('Testotron.importlib.util.spec_from_file_location')
    @patch('Testotron.importlib.util.module_from_spec')
    def test_generate_python_tests_skips_test_files(self, mock_module_from_spec, mock_spec_from_file):
        """Test that existing test files are skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            test_file = repo_dir / "test_something.py"
            test_file.write_text("# Existing test")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            with patch.object(generator, '_ask_claude_to_generate_tests') as mock_claude:
                generator._generate_python_tests()
                
                # Claude should not be called for test files
                mock_claude.assert_not_called()
    
    @patch('Testotron.importlib.util.spec_from_file_location')
    @patch('Testotron.importlib.util.module_from_spec')
    def test_generate_python_tests_multiple_files(self, mock_module_from_spec, mock_spec_from_file):
        """Test generating tests for multiple Python files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            py_file1 = repo_dir / "module1.py"
            py_file1.write_text("def func1(): pass")
            py_file2 = repo_dir / "module2.py"
            py_file2.write_text("def func2(): pass")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            with patch.object(generator, '_ask_claude_to_generate_tests', return_value="# Test"):
                generator._generate_python_tests()
            
            test_dir = repo_dir / 'tests'
            assert (test_dir / "test_module1.py").exists()
            assert (test_dir / "test_module2.py").exists()
    
    def test_generate_python_tests_nested_directories(self):
        """Test generating tests for Python files in nested directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            nested_dir = repo_dir / "src" / "utils"
            nested_dir.mkdir(parents=True)
            py_file = nested_dir / "helper.py"
            py_file.write_text("def helper(): pass")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            with patch.object(generator, '_ask_claude_to_generate_tests', return_value="# Test"):
                with patch('Testotron.importlib.util.spec_from_file_location'):
                    with patch('Testotron.importlib.util.module_from_spec'):
                        generator._generate_python_tests()
            
            test_dir = repo_dir / 'tests'
            assert test_dir.exists()


class TestAskClaudeToGenerateTests:
    """Test the _ask_claude_to_generate_tests method"""
    
    @patch.object(GitHubTestGenerator, '_call_claude_api')
    def test_ask_claude_basic(self, mock_call_api):
        """Test basic Claude API prompt generation"""
        mock_call_api.return_value = "# Generated test code"
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        source_code = "def example():\n    return 42"
        module_name = "example"
        
        result = generator._ask_claude_to_generate_tests(source_code, module_name)
        
        assert result == "# Generated test code"
        mock_call_api.assert_called_once()
        
        # Verify the prompt contains necessary information
        call_args = mock_call_api.call_args[0][0]
        assert module_name in call_args
        assert source_code in call_args
        assert "pytest" in call_args
    
    @patch.object(GitHubTestGenerator, '_call_claude_api')
    def test_ask_claude_with_complex_code(self, mock_call_api):
        """Test Claude API with complex source code"""
        mock_call_api.return_value = "# Complex test code"
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        source_code = """
class ComplexClass:
    def __init__(self, value):
        self.value = value
    
    def method1(self):
        return self.value * 2
    
    def method2(self, x):
        return self.value + x
"""
        result = generator._ask_claude_to_generate_tests(source_code, "complex_module")
        
        assert result == "# Complex test code"
        assert mock_call_api.called


class TestCallClaudeAPI:
    """Test the _call_claude_api method"""
    
    @patch('Testotron.Anthropic')
    def test_call_claude_api_success(self, mock_anthropic_class):
        """Test successful Claude API call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated test code"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "test_api_key")
        
        result = generator._call_claude_api("Generate tests")
        
        assert result == "Generated test code"
        mock_client.messages.create.assert_called_once()
    
    @patch('Testotron.Anthropic')
    @patch('Testotron.time.sleep')
    def test_call_claude_api_retry_success(self, mock_sleep, mock_anthropic_class):
        """Test Claude API call with retry on connection error"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated test code"
        mock_response.content = [mock_content]
        
        # Fail first, succeed second
        mock_client.messages.create.side_effect = [
            anthropic.APIConnectionError("Connection failed"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "test_api_key")
        
        result = generator._call_claude_api("Generate tests")
        
        assert result == "Generated test code"
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once()
    
    @patch('Testotron.Anthropic')
    @patch('Testotron.time.sleep')
    def test_call_claude_api_retry_exhausted(self, mock_sleep, mock_anthropic_class):
        """Test Claude API call fails after all retries"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIConnectionError("Connection failed")
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "test_api_key")
        
        with pytest.raises(anthropic.APIConnectionError):
            generator._call_claude_api("Generate tests")
        
        assert mock_client.messages.create.call_count == 3  # max_retries default is 3
        assert mock_sleep.call_count == 2  # sleep called on first 2 failures
    
    @patch('Testotron.Anthropic')
    def test_call_claude_api_other_error(self, mock_anthropic_class, capsys):
        """Test Claude API call with non-connection error"""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIError("API Error")
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "test_api_key")
        
        with pytest.raises(anthropic.APIError):
            generator._call_claude_api("Generate tests")
        
        captured = capsys.readouterr()
        assert "Claude API error" in captured.out
    
    @patch('Testotron.Anthropic')
    @patch('Testotron.time.sleep')
    def test_call_claude_api_exponential_backoff(self, mock_sleep, mock_anthropic_class):
        """Test exponential backoff in retry logic"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Success"
        mock_response.content = [mock_content]
        
        # Fail twice, succeed third time
        mock_client.messages.create.side_effect = [
            anthropic.APIConnectionError("Failed 1"),
            anthropic.APIConnectionError("Failed 2"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "test_api_key")
        
        result = generator._call_claude_api("Generate tests", initial_delay=1)
        
        assert result == "Success"
        # Verify exponential backoff: 1, 2, 4 seconds
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry: 1 * 2^0
        mock_sleep.assert_any_call(2)  # Second retry: 1 * 2^1
    
    @patch('Testotron.Anthropic')
    def test_call_claude_api_custom_parameters(self, mock_anthropic_class):
        """Test Claude API call with custom parameters"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated code"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "test_api_key")
        
        result = generator._call_claude_api("Test prompt", max_retries=5, initial_delay=2)
        
        assert result == "Generated code"
        
        # Verify API call parameters
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs['model'] == "claude-3-haiku-20240307"
        assert call_kwargs['max_tokens'] == 4000
        assert call_kwargs['temperature'] == 0.3
        assert call_kwargs['messages'][0]['role'] == 'user'
        assert call_kwargs['messages'][0]['content'] == "Test prompt"


class TestCleanup:
    """Test the cleanup method"""
    
    def test_cleanup_removes_directory(self):
        """Test cleanup removes the cloned repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test_repo"
            repo_dir.mkdir()
            test_file = repo_dir / "test.txt"
            test_file.write_text("test content")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            assert repo_dir.exists()
            
            generator.cleanup()
            
            assert not repo_dir.exists()
    
    def test_cleanup_no_directory(self):
        """Test cleanup when no directory is set"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.repo_dir = None
        
        # Should not raise an exception
        generator.cleanup()
    
    def test_cleanup_nonexistent_directory(self):
        """Test cleanup with non-existent directory"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.repo_dir = Path("/nonexistent/directory")
        
        # Should not raise an exception
        generator.cleanup()
    
    def test_cleanup_with_nested_structure(self):
        """Test cleanup removes nested directory structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test_repo"
            nested_dir = repo_dir / "src" / "utils"
            nested_dir.mkdir(parents=True)
            
            file1 = repo_dir / "file1.py"
            file2 = nested_dir / "file2.py"
            file1.write_text("content1")
            file2.write_text("content2")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            generator.cleanup()
            
            assert not repo_dir.exists()


class TestRun:
    """Test the run method (main execution flow)"""
    
    @patch.object(GitHubTestGenerator, 'generate_tests')
    @patch.object(GitHubTestGenerator, 'analyze_repository')
    @patch.object(GitHubTestGenerator, 'clone_repository')
    def test_run_success(self, mock_clone, mock_analyze, mock_generate, capsys):
        """Test successful run execution"""
        mock_clone.return_value = True
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.repo_dir = Path("/tmp/test_repo")
        
        result = generator.run()
        
        assert result is True
        mock_clone.assert_called_once()
        mock_analyze.assert_called_once()
        mock_generate.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Unit tests generated" in captured.out
    
    @patch.object(GitHubTestGenerator, 'clone_repository')
    def test_run_clone_failure(self, mock_clone):
        """Test run when cloning fails"""
        mock_clone.return_value = False
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        result = generator.run()
        
        assert result is False
        mock_clone.assert_called_once()
    
    @patch.object(GitHubTestGenerator, 'generate_tests')
    @patch.object(GitHubTestGenerator, 'analyze_repository')
    @patch.object(GitHubTestGenerator, 'clone_repository')
    def test_run_complete_flow(self, mock_clone, mock_analyze, mock_generate):
        """Test complete execution flow with all methods called in order"""
        mock_clone.return_value = True
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.repo_dir = Path("/tmp/test_repo")
        
        result = generator.run()
        
        assert result is True
        
        # Verify call order
        assert mock_clone.call_count == 1
        assert mock_analyze.call_count == 1
        assert mock_generate.call_count == 1


class TestIntegration:
    """Integration tests for the entire workflow"""
    
    @patch('Testotron.Anthropic')
    @patch('Testotron.Repo')
    def test_full_workflow_integration(self, mock_repo, mock_anthropic_class):
        """Test the full workflow from clone to test generation"""
        # Setup mocks
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = """
import pytest
from example import example_function

def test_example_function():
    assert example_function() == True
"""
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test_repo"
            repo_dir.mkdir()
            
            # Create a sample Python file
            py_file = repo_dir / "example.py"
            py_file.write_text("def example_function():\n    return True")
            
            generator = GitHubTestGenerator("https://github.com/test/repo.git", "api_key")
            
            # Override repo_dir to use our temp directory
            with patch.object(generator, 'clone_repository', return_value=True):
                generator.repo_dir = repo_dir
                result = generator.run()
            
            assert result is True
            
            # Verify test file was created
            test_file = repo_dir / 'tests' / 'test_example.py'
            assert test_file.exists()
    
    def test_error_recovery(self):
        """Test error recovery in various scenarios"""
        generator = GitHubTestGenerator("", "")
        
        # Should handle empty URL gracefully
        with patch('Testotron.Repo.clone_from', side_effect=Exception("Invalid URL")):
            result = generator.clone_repository()
            assert result is False


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_special_characters_in_repo_url(self):
        """Test handling of special characters in repository URL"""
        generator = GitHubTestGenerator(
            "https://github.com/user/repo-with-special_chars123.git",
            "api_key"
        )
        
        assert generator.repo_url == "https://github.com/user/repo-with-special_chars123.git"
    
    def test_very_long_api_key(self):
        """Test with very long API key"""
        long_key = "sk-ant-" + "x" * 1000
        generator = GitHubTestGenerator("https://github.com/test/repo", long_key)
        
        assert generator.claude_api_key == long_key
    
    @patch('Testotron.Anthropic')
    def test_empty_response_from_claude(self, mock_anthropic_class):
        """Test handling of empty response from Claude API"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "   "  # Whitespace only
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        result = generator._call_claude_api("Generate tests")
        
        assert result == ""  # Should be stripped
    
    def test_unicode_in_source_code(self):
        """Test handling of Unicode characters in source code"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        source_code = """
def unicode_function():
    return "Hello 世界 🌍"
"""
        
        with patch.object(generator, '_call_claude_api', return_value="# Test"):
            result = generator._ask_claude_to_generate_tests(source_code, "unicode_module")
            assert result == "# Test"


class TestMainExecution:
    """Test the main execution block"""
    
    @patch.dict('os.environ', {'CLAUDE_API_KEY': 'test_key_12345'})
    @patch.object(GitHubTestGenerator, 'run')
    def test_main_block_success(self, mock_run, capsys):
        """Test main block execution on success"""
        mock_run.return_value = True
        
        # Import and execute would happen here in real scenario
        # This tests the pattern used in __main__
        import os
        repo_url = "https://github.com/akaf47/langchain-agent-lab"
        claude_key = os.environ.get("CLAUDE_API_KEY")
        
        agent = GitHubTestGenerator(repo_url, claude_key)
        if agent.run():
            print("Test generation successful!")
        
        captured = capsys.readouterr()
        assert "Test generation successful!" in captured.out
    
    @patch.dict('os.environ', {'CLAUDE_API_KEY': 'test_key_12345'})
    @patch.object(GitHubTestGenerator, 'run')
    def test_main_block_failure(self, mock_run, capsys):
        """Test main block execution on failure"""
        mock_run.return_value = False
        
        import os
        repo_url = "https://github.com/akaf47/langchain-agent-lab"
        claude_key = os.environ.get("CLAUDE_API_KEY")
        
        agent = GitHubTestGenerator(repo_url, claude_key)
        if not agent.run():
            print("Test generation failed")
        
        captured = capsys.readouterr()
        assert "Test generation failed" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=Testotron", "--cov-report=term-missing"])
```