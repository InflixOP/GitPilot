import os
import sys
from typing import Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .ai_engine import AIEngine
from .context_analyzer import ContextAnalyzer
from .git_executor import GitExecutor
from .logger import GitPilotLogger

console = Console()

def load_config():
    config_path = os.path.expanduser("~/.gitpilot/config.yaml")
    default_config = {
        "auto_confirm": False,
        "explain_by_default": False,
        "log_level": "INFO",
        "default_model": "1"
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

def display_model_selection(ai_engine: AIEngine) -> str:
    models = ai_engine.get_available_models()
    table = Table(title=" Available AI Models", show_header=True, header_style="bold magenta")
    table.add_column("Choice", style="cyan", width=8)
    table.add_column("Model", style="green")
    table.add_column("Provider", style="blue")
    for choice, model_info in models.items():
        provider_emoji = " " if model_info["provider"] == "gemini" else " "
        table.add_row(
            choice,
            model_info["name"],
            f"{provider_emoji} {model_info['provider'].title()}"
        )
    console.print(table)
    while True:
        choice = Prompt.ask(
            "Select a model",
            choices=list(models.keys()),
            default="1"
        )
        if choice in models:
            selected_model = models[choice]
            console.print(f" Selected: {selected_model['name']}", style="green")
            return choice
        console.print(" Invalid choice. Please try again.", style="red")

@click.command()
@click.argument('query', required=False)
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be executed without running')
@click.option('--explain', '-e', is_flag=True, help='Show detailed explanation')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm destructive operations')
@click.option('--history', '-h', is_flag=True, help='Show recent command history')
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--model', '-m', type=str, help='Select AI model (1-4)')
@click.option('--skip-model-selection', is_flag=True, help='Skip model selection and use default')
def main(query: Optional[str], dry_run: bool, explain: bool, yes: bool, history: bool,
         version: bool, model: Optional[str], skip_model_selection: bool):
    if version:
        from . import __version__
        console.print(f"GitPilot version {__version__}")
        return
    config = load_config()
    logger = GitPilotLogger()
    context_analyzer = ContextAnalyzer()
    if history:
        show_history(logger)
        return
    if not context_analyzer.is_git_repo():
        console.print(" Not a Git repository. Please run from inside a Git repository.", style="red")
        sys.exit(1)
    console.print(" GitPilot is ready to help you with Git!", style="green")
    ai_engine = AIEngine()
    selected_model = None
    if model:
        if model in ai_engine.get_available_models():
            selected_model = model
            model_name = ai_engine.get_available_models()[model]["name"]
            console.print(f" Using model: {model_name}", style="blue")
        else:
            console.print(f" Invalid model choice: {model}", style="red")
            sys.exit(1)
    elif skip_model_selection:
        selected_model = config.get("default_model", "1")
        model_name = ai_engine.get_available_models()[selected_model]["name"]
        console.print(f" Using default model: {model_name}", style="blue")
    else:
        selected_model = display_model_selection(ai_engine)
    if not query:
        query = click.prompt("\n What would you like to do with Git?", type=str)
    context = context_analyzer.analyze_context()
    with console.status(" Thinking..."):
        safe_query = query if query is not None else ""
        ai_response = ai_engine.generate_command(safe_query, context, selected_model)
    display_ai_response(ai_response, explain or config.get("explain_by_default", False))
    if not ai_response.get("command"):
        console.print(" Could not generate a valid Git command.", style="red")
        sys.exit(1)
    git_executor = GitExecutor()
    if dry_run:
        result = git_executor.preview_command(ai_response["command"])
        display_execution_result(result, is_preview=True)
    else:
        should_execute = True
        if git_executor.is_destructive_command(ai_response["command"]) and not yes:
            should_execute = Confirm.ask(
                f"Execute potentially destructive command: {ai_response['command']}?"
            )
        if should_execute:
            result = git_executor.execute(ai_response["command"], auto_confirm=yes)
            display_execution_result(result)
            logger.log_command(
                user_input=safe_query,
                git_command=ai_response["command"],
                success=result["success"],
                output=result.get("output", ""),
                error=result.get("error", "")
            )
        else:
            console.print(" Operation cancelled.", style="yellow")

def display_ai_response(response: Dict, show_explanation: bool = False):
    if response.get("command"):
        command_text = Text(response["command"], style="bold cyan")
        console.print(Panel(command_text, title="Generated Command", border_style="cyan"))
        if show_explanation and response.get("explanation"):
            console.print(Panel(response["explanation"], title="Explanation", border_style="blue"))
        if response.get("warning"):
            console.print(Panel(response["warning"], title="Warning", border_style="yellow"))
    else:
        console.print(Panel(
            response.get("explanation", " No command generated"),
            title="Error",
            border_style="red"
        ))

def display_execution_result(result: Dict, is_preview: bool = False):
    if is_preview:
        console.print(Panel(result["output"], title="Preview", border_style="blue"))
        if result.get("warnings"):
            for warning in result["warnings"]:
                console.print(f" Warning: {warning}", style="yellow")
        return
    if result["success"]:
        if result.get("output"):
            console.print(Panel(result["output"], title="Success", border_style="green"))
        else:
            console.print(" Command executed successfully", style="green")
    else:
        error_text = result.get("error", "Unknown error")
        console.print(Panel(error_text, title="Error", border_style="red"))
    if result.get("warnings"):
        for warning in result["warnings"]:
            console.print(f" Warning: {warning}", style="yellow")

def show_history(logger: GitPilotLogger):
    history = logger.get_recent_history(10)
    if not history:
        console.print(" No command history found.", style="yellow")
        return
    console.print(" Recent Commands:", style="bold")
    for i, entry in enumerate(reversed(history), 1):
        status = " " if entry["success"] else " "
        timestamp = entry["timestamp"][:19]
        console.print(f"\n{i}. {status} {timestamp}")
        console.print(f"   Query: {entry['user_input']}")
        console.print(f"   Command: {entry['git_command']}")
        if entry.get("error"):
            console.print(f"    Error: {entry['error']}", style="red")
        if entry.get("output"):
            console.print(f"    Output: {entry['output']}")

if __name__ == "__main__":
    main()