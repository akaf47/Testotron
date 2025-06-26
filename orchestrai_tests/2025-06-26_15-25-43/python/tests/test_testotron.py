```python
import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
from Testotron import (
    analyze_repository,
    generate_tests,
    get_supported_files,
    write_tests_to_file,
    main
)

@pytest.fixture
def mock_repo_path():
    return Path("/test/repo/path")

@pytest.fixture
def mock_file_list():
    return [
        Path("/test/repo/path/file1.py"),
        Path("/test/repo/path/file2.js"),
        Path("/test/repo/path/file3.java")
    ]

def test_analyze_repository(mock_repo_path):
    with patch('Testotron.Path.glob') as mock_glob:
        mock_glob.return_value = [
            Path("/test/repo/path/file1.py"),
            Path("/test/repo/path/file2.js")
        ]
        
        result = analyze_repository(mock_repo_path)
        
        assert isinstance(result, dict)
        assert "total_files" in result
        assert "supported_files" in result
        assert "file_types" in result

def test_get_supported_files(mock_repo_path, mock_file_list):
    with patch('Testotron.Path.glob') as mock_glob:
        mock_glob.return_value = mock_file_list
        
        supported_files = get_supported_files(mock_repo_path)
        
        assert isinstance(supported_files, dict)
        assert "PYTHON" in supported_files
        assert len(supported_files["PYTHON"]) == 1

@pytest.mark.parametrize("file_type,expected_framework", [
    ("PYTHON", "pytest"),
    ("JAVASCRIPT", "jest"),
    ("JAVA", "junit"),
])
def test_generate_tests(file_type, expected_framework):
    test_files = [Path("/test/path/file1.ext")]
    
    with patch('Testotron.openai.ChatCompletion.create') as mock_chat:
        mock_chat.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test content"))]
        )
        
        result = generate_tests(file_type, test_files, "test-key")
        
        assert isinstance(result, list)
        assert len(result) > 0

def test_write_tests_to_file(tmp_path):
    test_content = "Test content"
    file_path = tmp_path / "test_output.py"
    
    write_tests_to_file(str(file_path), test_content)
    
    assert file_path.exists()
    assert file_path.read_text() == test_content

@patch('Testotron.analyze_repository')
@patch('Testotron.generate_tests')
@patch('Testotron.write_tests_to_file')
def test_main_success(mock_write, mock_generate, mock_analyze, mock_repo_path):
    mock_analyze.return_value = {
        "total_files": 3,
        "supported_files": {"PYTHON": [Path("test.py")]},
        "file_types": ["PYTHON"]
    }
    mock_generate.return_value = ["Test content"]
    
    with patch('sys.argv', ['testotron.py', str(mock_repo_path), 'test-key']):
        main()
        
        mock_analyze.assert_called_once()
        mock_generate.assert_called_once()
        mock_write.assert_called_once()

def test_main_missing_args():
    with patch('sys.argv', ['testotron.py']):
        with pytest.raises(SystemExit):
            main()

def test_main_invalid_repo_path():
    with patch('sys.argv', ['testotron.py', '/invalid/path', 'test-key']):
        with pytest.raises(SystemExit):
            main()

@pytest.mark.parametrize("test_files,expected_count", [
    ([], 0),
    ([Path("test1.py")], 1),
    ([Path("test1.py"), Path("test2.py")], 2),
])
def test_supported_files_count(mock_repo_path, test_files, expected_count):
    with patch('Testotron.Path.glob') as mock_glob:
        mock_glob.return_value = test_files
        
        result = get_supported_files(mock_repo_path)
        
        if test_files:
            assert len(result.get("PYTHON", [])) == expected_count
        else:
            assert not result.get("PYTHON")

def test_analyze_repository_empty(mock_repo_path):
    with patch('Testotron.Path.glob') as mock_glob:
        mock_glob.return_value = []
        
        result = analyze_repository(mock_repo_path)
        
        assert result["total_files"] == 0
        assert not result["supported_files"]
        assert not result["file_types"]

```