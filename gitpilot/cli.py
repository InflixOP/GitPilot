"""
Main CLI interface for GitPilot
"""

import os
import sys
from typing import Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.text import Text

from .ai_engine import AIEngine
from .context_analyzer import ContextAnalyzer
from .git_executor import GitExecutor
from .logger import GitPilotLogger

console = Console()


def load_config():
    """Load configuration from ~/.gitpilot/config.yaml"""
    config_path = os.path.expanduser("~/.gitpilot/config.yaml")
    default_config = {
        "ai_provider": "gemini",
        "auto_confirm": False,
        "explain_by_default": False,
        "log_level": "INFO"
    }
    try:
        import yaml
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return {**default_config, **config}
    except ImportError:
        pass
    return default_config


@click.command()
@click.argument('query', required=False)
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be executed without running')
@click.option('--explain', '-e', is_flag=True, help='Show detailed explanation')
@click.option('--provider', '-p', default=None, help='AI provider (gemini/openai)')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm destructive operations')
@click.option('--history', '-h', is_flag=True, help='Show recent command history')
@click.option('--version', is_flag=True, help='Show version information')
def main(query: Optional[str], dry_run: bool, explain: bool, 
         provider: Optional[str], yes: bool, history: bool, version: bool):
    """
    GitPilot: AI-Powered Git Assistant
    
    Translates natural language into Git commands.
    
    Examples:
        gitpilot "create a new branch for feature login"
        gitpilot "undo last commit but keep changes" --dry-run
        gitpilot "show commits from last week" --explain
    """
    
    if version:
        from . import __version__
        console.print(f"GitPilot version {__version__}")
        return
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    logger = GitPilotLogger()
    context_analyzer = ContextAnalyzer()
    
    # Show history if requested
    if history:
        show_history(logger)
        return
    
    # Check if we're in a Git repository
    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository. Please run from inside a Git repository.", style="red")
        sys.exit(1)
    
    # Get query interactively if not provided
    if not query:
        query = click.prompt("What would you like to do with Git?", type=str)
    
    # Initialize AI engine
    ai_provider = provider or config.get("ai_provider", "gemini")
    try:
        ai_engine = AIEngine(provider=ai_provider)
    except ValueError as e:
        console.print(f"❌ {e}", style="red")
        sys.exit(1)
    
    # Analyze context
    context = context_analyzer.analyze_context()
    
    # Generate command
    with console.status("🤖 Thinking..."):
        safe_query = query if query is not None else ""
        ai_response = ai_engine.generate_command(safe_query, context)
    
    # Display results
    display_ai_response(ai_response, explain or config.get("explain_by_default", False))
    
    if not ai_response.get("command"):
        console.print("❌ Could not generate a valid Git command.", style="red")
        sys.exit(1)
    
    # Execute command
    git_executor = GitExecutor()
    
    if dry_run:
        result = git_executor.preview_command(ai_response["command"])
        display_execution_result(result, is_preview=True)
    else:
        # Check for confirmation
        should_execute = True
        if git_executor.is_destructive_command(ai_response["command"]) and not yes:
            should_execute = Confirm.ask(
                f"Execute potentially destructive command: {ai_response['command']}?"
            )
        
        if should_execute:
            result = git_executor.execute(ai_response["command"], auto_confirm=yes)
            display_execution_result(result)
            
            # Log the complete interaction
            logger.log_command(
                user_input=safe_query,
                git_command=ai_response["command"],
                success=result["success"],
                output=result.get("output", ""),
                error=result.get("error", "")
            )
        else:
            console.print("Operation cancelled.", style="yellow")


def display_ai_response(response: Dict, show_explanation: bool = False):
    """Display AI response with formatting"""
    if response.get("command"):
        # Show command
        command_text = Text(response["command"], style="bold cyan")
        console.print(Panel(command_text, title="🎯 Generated Command", border_style="cyan"))
        
        # Show explanation if requested
        if show_explanation and response.get("explanation"):
            console.print(Panel(response["explanation"], title="💡 Explanation", border_style="blue"))
        
        # Show warnings
        if response.get("warning"):
            console.print(Panel(response["warning"], title="⚠️  Warning", border_style="yellow"))
    else:
        console.print(Panel(response.get("explanation", "No command generated"), 
                          title="❌ Error", border_style="red"))


def display_execution_result(result: Dict, is_preview: bool = False):
    """Display command execution result"""
    if is_preview:
        console.print(Panel(result["output"], title="👀 Preview", border_style="blue"))
        if result.get("warnings"):
            for warning in result["warnings"]:
                console.print(f"⚠️  {warning}", style="yellow")
        return
    
    if result["success"]:
        if result.get("output"):
            console.print(Panel(result["output"], title="✅ Success", border_style="green"))
        else:
            console.print("✅ Command executed successfully", style="green")
    else:
        error_text = result.get("error", "Unknown error")
        console.print(Panel(error_text, title="❌ Error", border_style="red"))
    
    # Show warnings
    if result.get("warnings"):
        for warning in result["warnings"]:
            console.print(f"⚠️  {warning}", style="yellow")


def show_history(logger: GitPilotLogger):
    """Show recent command history"""
    history = logger.get_recent_history(10)
    
    if not history:
        console.print("No command history found.", style="yellow")
        return
    
    console.print("\n📜 Recent Commands:", style="bold")
    
    for i, entry in enumerate(reversed(history), 1):
        status = "✅" if entry["success"] else "❌"
        timestamp = entry["timestamp"][:19]  # Remove microseconds
        
        console.print(f"\n{i}. {status} {timestamp}")
        console.print(f"   Query: {entry['user_input']}")
        console.print(f"   Command: {entry['git_command']}")
        
        if entry.get("error"):
            console.print(f"   Error: {entry['error']}", style="red")


if __name__ == "__main__":
    main()