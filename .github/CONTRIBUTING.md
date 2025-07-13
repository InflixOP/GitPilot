# Contributing to GitPilot 🚁

Thank you for your interest in contributing to GitPilot! We welcome contributions from developers of all experience levels. This guide will help you get started with contributing to our AI-powered Git assistant.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Release Process](#release-process)
- [Community](#community)

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read and follow it in all your interactions with the project.

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, nationality, personal appearance, race, religion
- Sexual identity and orientation

### Expected Behavior

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher
- Git installed and configured
- A Google Gemini API key for testing
- Basic understanding of Git workflows

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/InflixOP/GitPilot.git
   cd gitpilot
   ```

## 🛠️ Development Setup

### 1. Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e .[dev]
```

### 3. Set Up Environment Variables

Create a `.env` file in the project root:
```bash
GEMINI_API_KEY=your-api-key-here
GITPILOT_LOG_LEVEL=DEBUG
```

### 4. Verify Installation

```bash
# Run tests to ensure everything works
pytest

# Test the CLI
gitpilot --version
```

## 🤝 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new functionality
- **Code Contributions**: Fix bugs or implement features
- **Documentation**: Improve docs, examples, or tutorials
- **Testing**: Add or improve test coverage
- **UI/UX**: Enhance the command-line interface

### Areas for Contribution

1. **AI Engine Improvements**
   - Better prompt engineering
   - Support for additional AI models
   - Enhanced context understanding

2. **Git Operations**
   - Support for more Git commands
   - Better error handling
   - Advanced Git workflow support

3. **Safety Features**
   - Enhanced destructive command detection
   - Better context-aware warnings
   - Improved validation

4. **User Experience**
   - Better terminal output formatting
   - Interactive features
   - Configuration options

5. **Performance**
   - Faster command generation
   - Reduced memory usage
   - Better caching

## 📝 Code Style Guidelines

### Python Style

We follow PEP 8 with some modifications:

- **Line Length**: 88 characters (Black default)
- **Quotes**: Use double quotes for strings
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Type Hints**: Use type hints for all functions and methods

### Code Formatting

We use the following tools for code quality:

```bash
# Format code
black gitpilot/

# Sort imports
isort gitpilot/

# Lint code
flake8 gitpilot/

# Type checking
mypy gitpilot/
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

### Documentation Style

- Use Google-style docstrings
- Include type information in docstrings
- Provide examples for public functions
- Keep README and docs up to date

Example docstring:
```python
def generate_command(self, user_input: str, context: Dict) -> Dict:
    """Generate Git command from natural language input.
    
    Args:
        user_input: The user's natural language request
        context: Repository context information
        
    Returns:
        Dictionary containing:
            - command: Generated Git command
            - explanation: Human-readable explanation
            - warning: Any safety warnings
            
    Raises:
        AIEngineError: If command generation fails
        
    Example:
        >>> engine = AIEngine()
        >>> result = engine.generate_command("create a branch", {})
        >>> print(result["command"])
        git checkout -b new-branch
    """
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gitpilot --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run tests with specific markers
pytest -m "not slow"
```

### Test Categories

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **AI Tests**: Test AI engine responses (mocked)

### Writing Tests

- Use descriptive test names
- Follow the Arrange-Act-Assert pattern
- Mock external dependencies (AI API calls, Git operations)
- Test both success and failure cases

Example test:
```python
def test_generate_command_success(mock_ai_engine):
    """Test successful command generation."""
    # Arrange
    engine = AIEngine()
    user_input = "create a new branch"
    context = {"branch": "main", "is_dirty": False}
    
    # Act
    result = engine.generate_command(user_input, context)
    
    # Assert
    assert result["command"] == "git checkout -b new-branch"
    assert "explanation" in result
    assert result["warning"] is None
```

## 📤 Submitting Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-stash-support`
- `bugfix/fix-context-parsing`
- `docs/update-installation-guide`
- `test/add-cli-tests`

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes
- `perf`: Performance improvements

Examples:
```
feat(ai): add support for OpenAI GPT-4
fix(cli): resolve issue with command history
docs(readme): update installation instructions
test(executor): add tests for destructive command detection
```

### Pull Request Process

1. **Update your fork**:
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation if needed

4. **Test your changes**:
   ```bash
   pytest
   black gitpilot/
   flake8 gitpilot/
   mypy gitpilot/
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(scope): your change description"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

## 🐛 Issue Guidelines

### Before Creating an Issue

- Search existing issues to avoid duplicates
- Check if the issue exists in the latest version
- Gather relevant information (OS, Python version, etc.)

### Bug Reports

Include:
- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happened
- **Environment**: OS, Python version, GitPilot version
- **Logs**: Relevant log output or error messages

### Feature Requests

Include:
- **Description**: Clear description of the feature
- **Use Case**: Why this feature would be useful
- **Proposed Solution**: How you think it should work
- **Alternatives**: Any alternative solutions considered

## 🔄 Pull Request Guidelines

### Before Submitting

- [ ] Code follows the style guidelines
- [ ] Tests are added/updated and passing
- [ ] Documentation is updated if needed
- [ ] Commit messages follow the convention
- [ ] Branch is up to date with main

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: Maintainers review the code
3. **Feedback**: Address any review comments
4. **Approval**: Once approved, changes are merged

## 📦 Release Process

### Version Numbering

We use Semantic Versioning (SemVer):
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Steps

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create release PR
4. Tag release after merge
5. Publish to PyPI

## 🌍 Community

### Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and community discussions
- **Discord**: For real-time chat (if available)

### Contributing Beyond Code

- **Documentation**: Help improve docs and tutorials
- **Community**: Answer questions and help other users
- **Advocacy**: Share GitPilot with others
- **Testing**: Test new features and report issues

## 📚 Resources

- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Git Workflow](https://guides.github.com/introduction/flow/)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🙏 Recognition

All contributors are recognized in our:
- `CONTRIBUTORS.md` file
- Release notes
- GitHub contributor list

Thank you for making GitPilot better for everyone! 🚀

---

**Questions?** Feel free to reach out by creating an issue or starting a discussion. We're here to help!
