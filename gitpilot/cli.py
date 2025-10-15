import os
import sys
import json
from typing import Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markup import escape

from .ai_engine import AIEngine
from .context_analyzer import ContextAnalyzer
from .git_executor import GitExecutor
from .logger import GitPilotLogger
from .repo_health import RepositoryHealthMonitor

console = Console()

def load_config():
    """Load configuration from config file"""
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
    """Display available models and get user selection"""
    models = ai_engine.get_available_models()
    
    table = Table(title="🤖 Available AI Models", show_header=True, header_style="bold magenta")
    table.add_column("Choice", style="cyan", width=8)
    table.add_column("Model", style="green")
    table.add_column("Provider", style="blue")
    
    for choice, model_info in models.items():
        provider_emoji = "🔸" if model_info["provider"] == "gemini" else "⚡"
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
            console.print(f"✅ Selected: {selected_model['name']}", style="green")
            return choice
        console.print("❌ Invalid choice. Please try again.", style="red")

@click.group(invoke_without_command=True)
@click.argument('query', required=False)
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be executed without running')
@click.option('--explain', '-e', is_flag=True, help='Show detailed explanation')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm destructive operations')
@click.option('--history', '-h', is_flag=True, help='Show recent command history')
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--model', '-m', type=str, help='Select AI model (1-4)')
@click.option('--skip-model-selection', is_flag=True, help='Skip model selection and use default')
@click.pass_context
def main(ctx: click.Context, query: Optional[str], dry_run: bool, explain: bool, yes: bool, history: bool, 
         version: bool, model: Optional[str], skip_model_selection: bool):
    """GitPilot - AI-powered Git assistant"""
    
    if version:
        from . import __version__
        console.print(f"GitPilot version {__version__}")
        return

    # If a subcommand was invoked, let Click handle it
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    logger = GitPilotLogger()
    context_analyzer = ContextAnalyzer()

    if history:
        show_history(logger)
        return

    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository. Please run from inside a Git repository.", style="red")
        sys.exit(1)

    console.print("🚀 GitPilot is ready to help you with Git!", style="green")
    
    ai_engine = AIEngine()
    

    selected_model = None
    if model:
        if model in ai_engine.get_available_models():
            selected_model = model
            model_name = ai_engine.get_available_models()[model]["name"]
            console.print(f"🤖 Using model: {model_name}", style="blue")
        else:
            console.print(f"❌ Invalid model choice: {model}", style="red")
            sys.exit(1)
    elif skip_model_selection:
        selected_model = config.get("default_model", "1")
        model_name = ai_engine.get_available_models()[selected_model]["name"]
        console.print(f"🤖 Using default model: {model_name}", style="blue")
    else:
        selected_model = display_model_selection(ai_engine)
    
    if not query:
        query = click.prompt("\n💬 What would you like to do with Git?", type=str)

    context = context_analyzer.analyze_context()

    with console.status("💭 Thinking..."):
        safe_query = query if query is not None else ""
        ai_response = ai_engine.generate_command(safe_query, context, selected_model)

    display_ai_response(ai_response, explain or config.get("explain_by_default", False))

    if not ai_response.get("command"):
        console.print("❌ Could not generate a valid Git command.", style="red")
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
            console.print("❌ Operation cancelled.", style="yellow")

def display_ai_response(response: Dict, show_explanation: bool = False):
    """Display AI response with formatting"""
    if response.get("command"):
        command_text = Text(response["command"], style="bold cyan")
        console.print(Panel(command_text, title="Generated Command", border_style="cyan"))
        
        if show_explanation and response.get("explanation"):
            console.print(Panel(response["explanation"], title="Explanation", border_style="blue"))
        
        if response.get("warning"):
            console.print(Panel(response["warning"], title="Warning", border_style="yellow"))
    else:
        console.print(Panel(
            response.get("explanation", "❌ No command generated"), 
            title="Error", 
            border_style="red"
        ))

def display_execution_result(result: Dict, is_preview: bool = False):
    """Display command execution result"""
    if is_preview:
        console.print(Panel(result["output"], title="Preview", border_style="blue"))
        if result.get("warnings"):
            for warning in result["warnings"]:
                console.print(f"⚠️ Warning: {warning}", style="yellow")
        return

    if result["success"]:
        if result.get("output"):
            console.print(Panel(result["output"], title="Success", border_style="green"))
        else:
            console.print("✅ Command executed successfully", style="green")
    else:
        error_text = result.get("error", "Unknown error")
        console.print(Panel(error_text, title="Error", border_style="red"))

    if result.get("warnings"):
        for warning in result["warnings"]:
            console.print(f"⚠️ Warning: {warning}", style="yellow")

def show_history(logger: GitPilotLogger):
    """Show recent command history"""
    history = logger.get_recent_history(10)
    if not history:
        console.print("❌ No command history found.", style="yellow")
        return

    console.print("🔍 Recent Commands:", style="bold")
    for i, entry in enumerate(reversed(history), 1):
        status = "✅" if entry["success"] else "❌"
        timestamp = entry["timestamp"][:19]
        console.print(f"\n{i}. {status} {timestamp}")
        console.print(f"   Query: {entry['user_input']}")
        console.print(f"   Command: {entry['git_command']}")
        if entry.get("error"):
            console.print(f"   ❌ Error: {entry['error']}", style="red")
        if entry.get("output"):
            console.print(f"   💬 Output: {entry['output']}")

@main.command()
@click.option('--format', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--detailed', is_flag=True, help='Show detailed health analysis')
@click.option('--model', '-m', type=str, help='AI model for analysis (1-4)')
def health(format: str, detailed: bool, model: Optional[str]):
    """Analyze repository health with AI-powered insights"""
    context_analyzer = ContextAnalyzer()
    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository.", style="red")
        sys.exit(1)
    
    health_monitor = RepositoryHealthMonitor()
    
    with console.status("🔍 Analyzing repository health..."):
        if detailed and model:
            ai_engine = AIEngine()
            if model not in ai_engine.get_available_models():
                console.print(f"❌ Invalid model choice: {model}", style="red")
                sys.exit(1)
            report = health_monitor.get_comprehensive_health_report(ai_engine, model)
        else:
            report = health_monitor.get_comprehensive_health_report()
    
    if format == 'json':
        console.print(json.dumps(report, indent=2))
    else:
        display_health_report(report)

@main.command()
@click.argument('search_query')
@click.option('--limit', default=50, help='Maximum number of commits to search')
@click.option('--model', '-m', type=str, help='AI model for search (1-4)')
def search(search_query: str, limit: int, model: Optional[str]):
    """Search commit history using natural language"""
    context_analyzer = ContextAnalyzer()
    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository.", style="red")
        sys.exit(1)
    
    ai_engine = AIEngine()
    selected_model = model or "1"
    
    if selected_model not in ai_engine.get_available_models():
        console.print(f"❌ Invalid model choice: {selected_model}", style="red")
        sys.exit(1)
    
    with console.status(f"🔍 Searching for: {search_query}..."):
        commit_history = context_analyzer.get_commit_history_for_search(limit)
        if not commit_history:
            console.print("❌ No commit history found.", style="red")
            sys.exit(1)
        
        results = ai_engine.semantic_commit_search(search_query, commit_history, selected_model)
    
    display_search_results(results, search_query)

@main.command()
@click.option('--max-commits', default=20, help='Maximum commits to display')
@click.option('--format', type=click.Choice(['tree', 'table', 'json']), default='tree', help='Display format')
def graph(max_commits: int, format: str):
    """Display visual Git commit graph"""
    context_analyzer = ContextAnalyzer()
    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository.", style="red")
        sys.exit(1)
    
    with console.status("📊 Generating Git graph..."):
        graph_data = context_analyzer.get_git_graph_data(max_commits)
    
    if "error" in graph_data:
        console.print(f"❌ {graph_data['error']}", style="red")
        sys.exit(1)
    
    if format == 'json':
        console.print(json.dumps(graph_data, indent=2))
    elif format == 'table':
        display_graph_table(graph_data)
    else:
        display_graph_tree(graph_data)

@main.command()
@click.option('--model', '-m', type=str, help='AI model for conflict resolution (1-4)')
def conflicts(model: Optional[str]):
    """Analyze and get AI assistance for merge conflicts"""
    context_analyzer = ContextAnalyzer()
    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository.", style="red")
        sys.exit(1)
    
    with console.status("🔍 Checking for conflicts..."):
        conflict_info = context_analyzer.detect_merge_conflicts()
    
    if not conflict_info.get("has_conflicts"):
        console.print("✅ No merge conflicts detected.", style="green")
        return
    
    display_conflict_info(conflict_info)
    
    if model and conflict_info.get("conflicted_files"):
        ai_engine = AIEngine()
        if model not in ai_engine.get_available_models():
            console.print(f"❌ Invalid model choice: {model}", style="red")
            sys.exit(1)
        
        # Get conflict content from first conflicted file for AI analysis
        first_file = conflict_info["conflicted_files"][0]["file"]
        try:
            with open(first_file, 'r', encoding='utf-8', errors='ignore') as f:
                conflict_content = f.read()
            
            with console.status("🤖 Analyzing conflicts with AI..."):
                context = context_analyzer.analyze_context()
                resolution = ai_engine.resolve_merge_conflict(conflict_content, context, model)
            
            display_conflict_resolution(resolution)
        except Exception as e:
            console.print(f"❌ Error reading conflict file: {str(e)}", style="red")

@main.command()
@click.option('--security', is_flag=True, help='Focus on security analysis')
@click.option('--performance', is_flag=True, help='Focus on performance metrics')
def analyze(security: bool, performance: bool):
    """Advanced repository analysis"""
    context_analyzer = ContextAnalyzer()
    if not context_analyzer.is_git_repo():
        console.print("❌ Not a Git repository.", style="red")
        sys.exit(1)
    
    health_monitor = RepositoryHealthMonitor()
    
    if security:
        with console.status("🔒 Performing security analysis..."):
            security_results = health_monitor.get_security_scan_results()
        display_security_results(security_results)
    elif performance:
        with console.status("⚡ Analyzing performance metrics..."):
            perf_results = health_monitor.get_performance_metrics()
        display_performance_results(perf_results)
    else:
        console.print("Please specify --security or --performance flag", style="yellow")
        console.print("Usage: gitpilot analyze --security or gitpilot analyze --performance")

def display_health_report(report: Dict):
    """Display formatted health report"""
    if "error" in report:
        console.print(f"❌ {report['error']}", style="red")
        return
    
    # Health scores
    scores = report.get("scores", {})
    overall_score = scores.get("overall_score", 0)
    
    # Health indicator
    if overall_score >= 90:
        health_emoji = "🟢"
        health_color = "green"
    elif overall_score >= 75:
        health_emoji = "🟡"
        health_color = "yellow"
    else:
        health_emoji = "🔴"
        health_color = "red"
    
    console.print(Panel(
        f"{health_emoji} Overall Health Score: {overall_score}/100",
        title="Repository Health",
        border_style=health_color
    ))
    
    # Detailed scores
    if scores:
        table = Table(title="Detailed Scores")
        table.add_column("Category", style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Status")
        
        score_items = [
            ("Size", scores.get("size_score", 0)),
            ("Activity", scores.get("activity_score", 0)),
            ("Security", scores.get("security_score", 0)),
            ("Performance", scores.get("performance_score", 0))
        ]
        
        for category, score in score_items:
            status = "✅ Good" if score >= 80 else "⚠️ Needs attention" if score >= 60 else "❌ Poor"
            table.add_row(category, f"{score}/100", status)
        
        console.print(table)
    
    # AI Analysis if available
    ai_analysis = report.get("ai_analysis", {})
    if ai_analysis.get("summary"):
        console.print(Panel(
            ai_analysis["summary"],
            title="AI Analysis",
            border_style="blue"
        ))
    
    # Recommendations
    recommendations = ai_analysis.get("recommendations", [])
    if recommendations:
        console.print("\n🔧 Recommendations:", style="bold")
        for i, rec in enumerate(recommendations[:5], 1):
            console.print(f"{i}. {rec}")

def display_search_results(results: Dict, query: str):
    """Display search results"""
    console.print(f"🔍 Search results for: '{query}'", style="bold")
    
    matches = results.get("matches", [])
    if not matches:
        console.print("❌ No matches found.", style="yellow")
        return
    
    for i, match in enumerate(matches[:10], 1):
        relevance = match.get("relevance_score", 0)
        relevance_bar = "█" * int(relevance * 10) + "░" * (10 - int(relevance * 10))
        
        console.print(f"\n{i}. [{match.get('commit_sha', 'unknown')}] {match.get('message', 'No message')}")
        console.print(f"   Relevance: {relevance_bar} ({relevance:.2f})")
        if match.get("explanation"):
            console.print(f"   Match: {match['explanation']}", style="dim")

def display_graph_tree(graph_data: Dict):
    """Display Git graph as a tree"""
    tree = Tree("📊 Git Commit Graph")
    
    current_branch = graph_data.get("current_branch", "unknown")
    branches = graph_data.get("branches", [])
    commits = graph_data.get("commits", [])
    
    # Add branch information
    branches_node = tree.add("🌳 Branches")
    for branch in branches[:10]:  # Limit display
        branch_style = "bold green" if branch.get("is_active") else "dim"
        branch_name = branch.get("name", "unknown")
        if branch.get("is_active"):
            branch_name += " (current)"
        branches_node.add(f"{branch_name}", style=branch_style)
    
    # Add recent commits
    commits_node = tree.add("📝 Recent Commits")
    for commit in commits[:10]:  # Show recent 10
        sha = commit.get("sha", "unknown")
        message = commit.get("message", "No message")
        author = commit.get("author", "Unknown")
        is_merge = commit.get("is_merge", False)
        
        commit_icon = "🔀" if is_merge else "📝"
        commits_node.add(f"{commit_icon} [{sha}] {message[:50]} - {author}")
    
    console.print(tree)

def display_graph_table(graph_data: Dict):
    """Display Git graph as a table"""
    commits = graph_data.get("commits", [])
    
    table = Table(title="Git Commit History")
    table.add_column("SHA", style="cyan", width=8)
    table.add_column("Message", style="white")
    table.add_column("Author", style="green")
    table.add_column("Type", style="yellow")
    
    for commit in commits[:20]:  # Show recent 20
        sha = commit.get("sha", "unknown")
        message = commit.get("message", "No message")
        author = commit.get("author", "Unknown")
        commit_type = "Merge" if commit.get("is_merge") else "Commit"
        
        # Truncate long messages
        if len(message) > 60:
            message = message[:57] + "..."
        
        table.add_row(sha, message, author, commit_type)
    
    console.print(table)

def display_conflict_info(conflict_info: Dict):
    """Display conflict information"""
    console.print("🔥 Merge Conflicts Detected", style="bold red")
    
    conflicted_files = conflict_info.get("conflicted_files", [])
    merge_branch = conflict_info.get("merge_branch")
    
    if merge_branch:
        console.print(f"Merging from branch: {merge_branch}", style="yellow")
    
    table = Table(title="Conflicted Files")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="red")
    table.add_column("Conflict Markers", style="yellow")
    
    for file_info in conflicted_files:
        file_path = file_info.get("file", "unknown")
        status = file_info.get("status", "??")
        markers = file_info.get("conflict_markers", 0)
        
        table.add_row(file_path, status, str(markers))
    
    console.print(table)

def display_conflict_resolution(resolution: Dict):
    """Display AI conflict resolution suggestions"""
    console.print("🤖 AI Conflict Resolution Analysis", style="bold blue")
    
    strategy = resolution.get("resolution_strategy", "No strategy provided")
    console.print(Panel(strategy, title="Resolution Strategy", border_style="blue"))
    
    explanation = resolution.get("explanation", "")
    if explanation:
        console.print(Panel(explanation, title="Detailed Explanation", border_style="cyan"))
    
    commands = resolution.get("recommended_commands", [])
    if commands:
        console.print("\n🔧 Recommended Commands:", style="bold")
        for i, cmd in enumerate(commands, 1):
            console.print(f"{i}. {cmd}", style="cyan")
    
    auto_resolvable = resolution.get("auto_resolvable", False)
    if auto_resolvable:
        console.print("\n✅ This conflict may be auto-resolvable", style="green")
    else:
        console.print("\n⚠️ Manual resolution required", style="yellow")

def display_security_results(results: Dict):
    """Display security analysis results"""
    if "error" in results:
        console.print(f"❌ {results['error']}", style="red")
        return
    
    security_score = results.get("security_score", 0)
    console.print(f"🔒 Security Score: {security_score}/100", style="bold")
    
    issues = results.get("security_issues", [])
    if not issues:
        console.print("✅ No security issues detected", style="green")
        return
    
    table = Table(title="Security Issues")
    table.add_column("Type", style="cyan")
    table.add_column("Severity", style="red")
    table.add_column("Description")
    
    for issue in issues:
        severity_color = "red" if issue.get("severity") == "high" else "yellow" if issue.get("severity") == "medium" else "white"
        table.add_row(
            issue.get("type", "unknown"),
            Text(issue.get("severity", "unknown"), style=severity_color),
            issue.get("description", "No description")
        )
    
    console.print(table)

def display_performance_results(results: Dict):
    """Display performance analysis results"""
    if "error" in results:
        console.print(f"❌ {results['error']}", style="red")
        return
    
    console.print("⚡ Performance Analysis", style="bold")
    
    # Repository size info
    repo_size = results.get("repository_size", {})
    if repo_size:
        console.print(f"📦 Total size: {repo_size.get('total_size_mb', 0):.1f} MB")
        console.print(f"📁 Working tree: {repo_size.get('working_tree_size_mb', 0):.1f} MB")
        console.print(f"🗄️ Git database: {repo_size.get('git_size_mb', 0):.1f} MB")
    
    # Tracking efficiency
    tracking = results.get("tracking_efficiency", {})
    if tracking:
        ratio = tracking.get("tracking_ratio", 0)
        console.print(f"📊 Tracking efficiency: {ratio:.1%}")
        
        untracked = tracking.get("untracked_files", 0)
        if untracked > 0:
            console.print(f"⚠️ Untracked files: {untracked}", style="yellow")
    
    # Branch health
    branch_health = results.get("branch_health", {})
    if branch_health:
        total_branches = branch_health.get("total_branches", 0)
        health = branch_health.get("health", "unknown")
        health_color = "green" if health == "good" else "yellow" if health == "fair" else "red"
        console.print(f"🌳 Branches: {total_branches} ({health})", style=health_color)

if __name__ == "__main__":
    main()
