"""
GitPilot: AI-Powered Git Assistant
Translates natural language commands into Git operations.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .ai_engine import AIEngine
from .cli import main
from .context_analyzer import ContextAnalyzer
from .git_executor import GitExecutor

__all__ = ["main", "AIEngine", "GitExecutor", "ContextAnalyzer"]
