# Testotron

**Testotron** is a Python tool that automatically generates unit tests for a given GitHub repository using Anthropic's Claude API.

## Features

- Clones a public GitHub repository to a temporary directory
- Analyzes Python code and generates `pytest`-style unit tests using Claude
- Saves generated tests in a `tests/` directory within the cloned repo
- Cleans up after itself

## Requirements

- Python 3.8+
- [Anthropic Python SDK](https://pypi.org/project/anthropic/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [GitPython](https://pypi.org/project/GitPython/)
- [requests](https://pypi.org/project/requests/)


### Install dependencies:
```
pip install -r requirements.txt
```

## Setup

1. **Create a `.env` file in your project root:**  
```
CLAUDE_API_KEY=your-anthropic-api-key-here
```
2. **Ensure `.env` is in your `.gitignore** (already set by default).

## Usage

Run the tool from the command line:
```
python Testotron.py
```
By default, it will attempt to generate tests for the repository specified in the script.  
To use a different repository, modify the `repo_url` in the `if __name__ == "__main__":` block.

## Security

- **Never commit your `.env` file or API keys to version control.**
- The `.env` file is already included in `.gitignore`.

## License

MIT License