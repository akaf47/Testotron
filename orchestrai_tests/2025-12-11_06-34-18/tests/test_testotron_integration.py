```python
"""
Integration Tests for Testotron
Tests complete workflows and interactions between components
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import anthropic
from Testotron import GitHubTestGenerator


class TestCompleteWorkflows:
    """Test complete end-to-end workflows"""
    
    @patch('Testotron.Anthropic')
    @patch('Testotron.Repo')
    def test_complete_success_workflow(self, mock_repo, mock_anthropic_class):
        """Test complete successful workflow from start to finish"""
        # Setup Claude mock
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "import pytest\n\ndef test_example():\n    assert True"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create fake repository structure
            repo_dir = Path(tmpdir) / "test_repo"
            repo_dir.mkdir()
            
            src_dir = repo_dir / "src"
            src_dir.mkdir()
            
            module_file = src_dir / "calculator.py"
            module_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
""")
            
            generator = GitHubTestGenerator(
                "https://github.com/test/calculator.git",
                "test_api_key"
            )
            
            # Mock clone to use our temp directory
            with patch.object(generator, 'clone_repository') as mock_clone:
                mock_clone.return_value = True
                generator.repo_dir = repo_dir
                
                result = generator.run()
            
            assert result is True
            
            # Verify tests were generated
            tests_dir = repo_dir / "tests"
            assert tests_dir.exists()
            
            test_file = tests_dir / "test_calculator.py"
            assert test_file.exists()
            assert "pytest" in test_file.read_text()
    
    @patch('Testotron.Repo')
    def test_workflow_with_clone_failure(self, mock_repo):
        """Test workflow when repository cloning fails"""
        mock_repo.clone_from.side_effect = Exception("Network error")
        
        generator = GitHubTestGenerator(
            "https://github.com/test/nonexistent.git",
            "test_api_key"
        )
        
        result = generator.run()
        
        assert result is False
    
    @patch('Testotron.Anthropic')
    @patch('Testotron.Repo')
    def test_workflow_with_api_failures_and_retries(self, mock_repo, mock_anthropic_class):
        """Test workflow with API failures that eventually succeed"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "# Generated tests"
        mock_response.content = [mock_content]
        
        # Fail twice, then succeed
        mock_client.messages.create.side_effect = [
            anthropic.APIConnectionError("Timeout 1"),
            anthropic.APIConnectionError("Timeout 2"),
            mock_response
        ]
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "test_repo"
            repo_dir.mkdir()
            
            py_file = repo_dir / "module.py"
            py_file.write_text("def function(): pass")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            
            with patch.object(generator, 'clone_repository', return_value=True):
                with patch('Testotron.time.sleep'):  # Speed up test
                    generator.repo_dir = repo_dir
                    result = generator.run()
            
            assert result is True


class TestRepositoryStructureScenarios:
    """Test different repository structure scenarios"""
    
    @patch('Testotron.Anthropic')
    def test_flat_repository_structure(self, mock_anthropic_class):
        """Test repository with flat structure (all files in root)"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "# Test code"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            
            # Create multiple Python files in root
            for i in range(3):
                py_file = repo_dir / f"module{i}.py"
                py_file.write_text(f"def function{i}(): pass")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            with patch('Testotron.importlib.util.spec_from_file_location'):
                with patch('Testotron.importlib.util.module_from_spec'):
                    generator._generate_python_tests()
            
            tests_dir = repo_dir / "tests"
            assert tests_dir.exists()
            assert (tests_dir / "test_module0.py").exists()
            assert (tests_dir / "test_module1.py").exists()
            assert (tests_dir / "test_module2.py").exists()
    
    @patch('Testotron.Anthropic')
    def test_deeply_nested_repository(self, mock_anthropic_class):
        """Test repository with deeply nested directory structure"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "# Test code"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            
            # Create deeply nested structure
            nested_path = repo_dir / "src" / "core" / "utils" / "helpers"
            nested_path.mkdir(parents=True)
            
            py_file = nested_path / "helper.py"
            py_file.write_text("def help_function(): pass")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            with patch('Testotron.importlib.util.spec_from_file_location'):
                with patch('Testotron.importlib.util.module_from_spec'):
                    generator._generate_python_tests()
            
            tests_dir = repo_dir / "tests"
            assert tests_dir.exists()
    
    @patch('Testotron.Anthropic')
    def test_repository_with_mixed_files(self, mock_anthropic_class):
        """Test repository with Python and non-Python files"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "# Test code"
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            
            # Create mixed file types
            (repo_dir / "module.py").write_text("def func(): pass")
            (repo_dir / "README.md").write_text("# README")
            (repo_dir / "config.json").write_text("{}")
            (repo_dir / "script.sh").write_text("#!/bin/bash")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            with patch('Testotron.importlib.util.spec_from_file_location'):
                with patch('Testotron.importlib.util.module_from_spec'):
                    generator._generate_python_tests()
            
            # Should only generate tests for Python files
            tests_dir = repo_dir / "tests"
            assert (tests_dir / "test_module.py").exists()
            assert not (tests_dir / "test_README.py").exists()
            assert not (tests_dir / "test_config.py").exists()


class TestErrorRecovery:
    """Test error recovery and resilience"""
    
    def test_recovery_from_file_system_errors(self):
        """Test recovery from file system errors"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        generator.repo_dir = Path("/nonexistent/path")
        
        # Should not crash when cleaning up non-existent directory
        generator.cleanup()
    
    @patch('Testotron.Anthropic')
    def test_recovery_from_partial_test_generation(self, mock_anthropic_class):
        """Test recovery when some test generations fail"""
        mock_client = MagicMock()
        
        # First call succeeds, second fails, third succeeds
        mock_response1 = MagicMock()
        mock_content1 = MagicMock()
        mock_content1.text = "# Test 1"
        mock_response1.content = [mock_content1]
        
        mock_response3 = MagicMock()
        mock_content3 = MagicMock()
        mock_content3.text = "# Test 3"
        mock_response3.content = [mock_content3]
        
        mock_client.messages.create.side_effect = [
            mock_response1,
            anthropic.APIError("Temporary error"),
            mock_response3
        ]
        mock_anthropic_class.return_value = mock_client
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir)
            
            (repo_dir / "module1.py").write_text("def func1(): pass")
            (repo_dir / "module2.py").write_text("def func2(): pass")
            (repo_dir / "module3.py").write_text("def func3(): pass")
            
            generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
            generator.repo_dir = repo_dir
            
            # This should handle the error gracefully
            try:
                with patch('Testotron.importlib.util.spec_from_file_location'):
                    with patch('Testotron.importlib.util.module_from_spec'):
                        generator._generate_python_tests()
            except anthropic.APIError:
                pass  # Expected to fail on second file


class TestConcurrentOperations:
    """Test scenarios involving concurrent or repeated operations"""
    
    def test_multiple_run_calls(self):
        """Test calling run() multiple times"""
        generator = GitHubTestGenerator("https://github.com/test/repo", "api_key")
        
        with patch.object(generator, 'clone_repository', return_value=False