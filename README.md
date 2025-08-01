# GitPilot 

**GitPilot** is an intelligent AI-powered Git assistant that bridges the gap between natural language and Git commands. It's designed to make Git more accessible and efficient by allowing developers to express their intentions in plain English, while providing context-aware suggestions and safety checks.

## 🌟 Key Features

### 🧠 AI-Powered Command Generation
- **Natural Language Processing**: Converts plain English requests into precise Git commands
- **Context-Aware Intelligence**: Analyzes your repository state to provide relevant suggestions
- **Multi-Model Support**: Choose from multiple AI providers and models:
  - **Google Gemini**: Gemini 2.0 Flash for fast, accurate responses
  - **Groq**: Lightning-fast inference with Llama 3.1 8B Instant, Llama 3.3 70B Versatile
  - **DeepSeek**: Advanced reasoning with R1 Distill Llama 70B
- **Intelligent Response Parsing**: Enhanced parsing handles various response formats from different AI models

### 🛡️ Safety & Security
- **Destructive Operation Detection**: Identifies potentially dangerous commands and requires confirmation
- **Command Validation**: Prevents command injection and validates Git syntax
- **Dry-Run Mode**: Preview commands before execution
- **Context Warnings**: Alerts about uncommitted changes, remote status, and other potential issues

### 📊 Repository Analysis
- **Branch Status**: Current branch, detached HEAD detection
- **Working Directory State**: Staged, unstaged, and untracked files
- **Remote Synchronization**: Ahead/behind status with remote repositories
- **Stash Management**: Stash count and status
- **Commit History**: Last commit information and analysis

### 🎯 User Experience
- **Rich Terminal Interface**: Beautiful, colorized output with progress indicators
- **Command History**: Track and review previously executed commands
- **Detailed Explanations**: Optional explanations for generated commands
- **Interactive Prompts**: Confirmation dialogs for destructive operations

## 🏗️ Architecture

GitPilot is built with a modular architecture:

```
├── cli.py              # Command-line interface and user interaction
├── ai_engine.py        # Multi-model AI integration (Gemini, Groq, DeepSeek)
├── context_analyzer.py # Git repository state analysis
├── git_executor.py     # Safe Git command execution
├── logger.py          # Logging and command history
└── prompts.py         # AI prompt templates
```

### Core Components

1. **CLI Interface**: Rich terminal interface with colorized output and interactive prompts
2. **AI Engine**: Multi-provider AI integration supporting:
   - Google Gemini (gemini-2.0-flash)
   - Groq (llama-3.1-8b-instant, llama-3.3-70b-versatile)
   - DeepSeek (deepseek-r1-distill-llama-70b)
3. **Context Analyzer**: Analyzes Git repository state and provides contextual information
4. **Git Executor**: Safely executes Git commands with validation and safety checks
5. **Logger**: Tracks command history and provides debugging information

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Git installed and configured
- At least one AI provider API key:
  - Google Gemini API key (set as `GEMINI_API_KEY` environment variable)
  - Groq API key (set as `GROQ_API_KEY` environment variable) - for Groq models
  - Both keys can be used simultaneously for maximum flexibility

### From PyPI (Recommended)
```bash
pip install gitpilot
```

### From Source
```bash
git clone https://github.com/InflixOp/gitpilot.git
cd gitpilot
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/InflixOp/gitpilot.git
cd gitpilot
pip install -e .[dev]
```

## 🎨 VS Code Extension

**GitPilot is also available as a VS Code extension!** Get the same AI-powered Git assistance directly integrated into your favorite editor.

### 🚀 Install from VS Code Marketplace

#### Method 1: VS Code Extensions Tab
1. Open VS Code
2. Go to the Extensions view (`Ctrl+Shift+X`)
3. Search for **"GitPilot"**
4. Click **"Install"** on the GitPilot - AI Git Assistant extension

#### Method 2: Direct Link
**[Install GitPilot Extension](https://marketplace.visualstudio.com/items?itemName=InflixOP.gitpilot)**

#### Method 3: Command Line
```bash
code --install-extension InflixOP.gitpilot
```

### ✨ VS Code Extension Features
- **🤖 AI-Powered Panel**: Beautiful integrated sidebar panel
- **📋 Command Palette Integration**: Access via `Ctrl+Shift+P`
- **🎯 Context Menu**: Right-click integration in Explorer
- **⚙️ Settings Integration**: Configure API keys in VS Code settings
- **🔄 Real-time Repository Status**: Live Git status display
- **🎨 VS Code Theming**: Matches your VS Code theme perfectly

### 🛠️ VS Code Extension Setup
1. **Install the extension** (see methods above)
2. **Configure API keys**:
   - Go to VS Code Settings (`Ctrl+,`)
   - Search for "GitPilot"
   - Add your Gemini or Groq API key
3. **Start using**:
   - Click the robot icon 🤖 in the Activity Bar
   - Or use `Ctrl+Shift+P` → "GitPilot: Execute Command"

### 💬 VS Code Extension Usage
```
"create a new branch for user authentication"
→ git checkout -b feature/user-authentication

"commit all changes with message 'Add login functionality'"
→ git add . && git commit -m "Add login functionality"

"show commits from last week"
→ git log --since="1 week ago" --oneline
```

## 🚀 Quick Start

1. **Set up your API keys**:
   ```bash
   # For Google Gemini (default)
   export GEMINI_API_KEY="your-gemini-api-key"
   
   # For Groq models (optional)
   export GROQ_API_KEY="your-groq-api-key"
   ```

2. **Navigate to a Git repository**:
   ```bash
   cd your-git-project
   ```

3. **Start using GitPilot**:
   ```bash
   # Use default model (Gemini)
   gitpilot "create a new branch for user authentication"
   
   # Or select a specific model
   gitpilot --model 2 "show me the current status"  # Groq Llama 3.1 8B
   gitpilot --model 3 "commit all changes"          # Groq Llama 3.3 70B
   ```

## 📋 Usage Examples

### Branch Management
```bash
# Create and switch to a new branch
gitpilot "create a new branch called feature-auth"

# Switch to an existing branch
gitpilot "switch to main branch"

# Delete a branch
gitpilot "delete the old-feature branch"
```

### Commit Operations
```bash
# Stage and commit changes
gitpilot "commit all changes with message 'Add user authentication'"

# Undo last commit but keep changes
gitpilot "undo last commit but keep the changes"

# Amend the last commit
gitpilot "modify the last commit message"
```

### Remote Operations
```bash
# Push to remote repository
gitpilot "push changes to origin"

# Pull latest changes
gitpilot "pull latest changes from remote"

# Sync with remote branch
gitpilot "sync with remote main branch"
```

### Repository Status
```bash
# Check repository status
gitpilot "show me the current status"

# View commit history
gitpilot "show commits from last week"

# Check differences
gitpilot "show what changed in the last commit"
```

## 🔧 Command Line Options

```bash
gitpilot [OPTIONS] [QUERY]
```

### Options
- `--dry-run, -d`: Show what would be executed without running the command
- `--explain, -e`: Show detailed explanation of the generated command
- `--yes, -y`: Auto-confirm destructive operations
- `--history, -h`: Show recent command history
- `--version`: Show version information
- `--model, -m`: Select AI model (1: Gemini, 2: Llama 3.1 8B, 3: Llama 3.3 70B, 4: DeepSeek R1)
- `--skip-model-selection`: Skip interactive model selection and use default

### Examples with Options
```bash
# Preview command without execution
gitpilot "reset to last commit" --dry-run

# Get explanation of the command
gitpilot "merge feature branch" --explain

# Auto-confirm destructive operation
gitpilot "force push to remote" --yes

# View command history
gitpilot --history

# Use specific AI models
gitpilot --model 2 "show me recent commits"        # Groq Llama 3.1 8B
gitpilot --model 3 "create a hotfix branch"         # Groq Llama 3.3 70B
gitpilot --model 4 "help me resolve merge conflicts" # DeepSeek R1

# Skip model selection for automation
gitpilot --skip-model-selection "add all files"
```

## ⚙️ Configuration

### Configuration File
Create a configuration file at `~/.gitpilot/config.yaml`:

```yaml
# Auto-confirm destructive operations
auto_confirm: false

# Always show detailed explanations
explain_by_default: false

# Logging level (INFO, DEBUG, ERROR)
log_level: INFO
```

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required for Gemini models)
- `GROQ_API_KEY`: Your Groq API key (required for Groq models)
- `GITPILOT_LOG_LEVEL`: Override log level (optional)

## 🔒 Safety Features

### Destructive Command Detection
GitPilot automatically detects potentially destructive operations:
- `git reset --hard`: Discards uncommitted changes
- `git clean -f`: Permanently deletes untracked files
- `git push --force`: Overwrites remote history
- `git rebase`: Rewrites commit history

### Context-Aware Warnings
- **Uncommitted Changes**: Warns before operations that might lose work
- **Remote Status**: Alerts when branch is behind remote
- **Detached HEAD**: Notifies about detached HEAD state
- **Stash Status**: Considers stashed changes in recommendations

## 📊 Dependencies

### Core Dependencies
- `click>=8.0.0`: Command-line interface framework
- `rich>=13.0.0`: Rich terminal formatting
- `google-generativeai>=0.3.0`: Google Gemini AI integration
- `gitpython>=3.1.0`: Git repository interaction
- `pyyaml>=6.0.0`: Configuration file parsing
- `loguru>=0.7.0`: Advanced logging

### Development Dependencies
- `pytest>=7.0.0`: Testing framework
- `pytest-cov>=4.0.0`: Coverage reporting
- `black>=23.0.0`: Code formatting
- `flake8>=6.0.0`: Code linting
- `mypy>=1.0.0`: Type checking

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gitpilot

# Run specific test file
pytest tests/test_cli.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](.github/CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -e .[dev]`
5. Run commands starting with "gitpilot"


## 🐛 Issue Reporting

Found a bug? Please report it on our [GitHub Issues](https://github.com/InflixOp/GitPilot/issues) page.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


