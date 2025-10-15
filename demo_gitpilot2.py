#!/usr/bin/env python3
"""
GitPilot 2.0.0 Manual Test Demonstration
Shows how to use the new features interactively
"""

import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Import GitPilot modules
from gitpilot.repo_health import RepositoryHealthMonitor
from gitpilot.context_analyzer import ContextAnalyzer
from gitpilot.ai_engine import AIEngine
from gitpilot.cli import display_health_report, display_graph_tree

console = Console()

def demo_health_check():
    """Demonstrate repository health checking"""
    console.print("\n🏥 [bold blue]Repository Health Check Demo[/bold blue]")
    console.print("=" * 50)
    
    monitor = RepositoryHealthMonitor()
    
    with console.status("🔍 Analyzing repository health..."):
        report = monitor.get_comprehensive_health_report()
    
    display_health_report(report)
    
    return Confirm.ask("\n🔄 Continue to next demo?")

def demo_git_graph():
    """Demonstrate Git graph visualization"""
    console.print("\n📊 [bold blue]Git Graph Visualization Demo[/bold blue]")
    console.print("=" * 50)
    
    analyzer = ContextAnalyzer()
    
    with console.status("📊 Generating Git graph..."):
        graph_data = analyzer.get_git_graph_data(max_commits=15)
    
    if "error" not in graph_data:
        display_graph_tree(graph_data)
    else:
        console.print(f"❌ Error: {graph_data['error']}", style="red")
    
    return Confirm.ask("\n🔄 Continue to next demo?")

def demo_security_scan():
    """Demonstrate security scanning"""
    console.print("\n🔒 [bold blue]Security Scan Demo[/bold blue]")
    console.print("=" * 50)
    
    monitor = RepositoryHealthMonitor()
    
    with console.status("🔍 Running security scan..."):
        security_results = monitor.get_security_scan_results()
    
    if "error" in security_results:
        console.print(f"❌ Error: {security_results['error']}", style="red")
        return True
    
    security_score = security_results.get("security_score", 0)
    issues = security_results.get("security_issues", [])
    
    # Display security score
    console.print(Panel(
        f"🛡️ Security Score: {security_score}/100\\n"
        f"🔍 Issues Found: {len(issues)}",
        title="Security Analysis Results",
        border_style="blue"
    ))
    
    # Show sample issues
    if issues:
        console.print("\n⚠️ [bold yellow]Sample Security Issues:[/bold yellow]")
        for i, issue in enumerate(issues[:3], 1):
            severity_color = "red" if issue.get("severity") == "high" else "yellow"
            console.print(f"{i}. [{severity_color}]{issue.get('type', 'unknown')}[/{severity_color}]: {issue.get('description', 'No description')[:80]}...")
    
    return Confirm.ask("\n🔄 Continue to next demo?")

def demo_commit_history():
    """Demonstrate commit history analysis"""
    console.print("\n📚 [bold blue]Commit History Analysis Demo[/bold blue]")
    console.print("=" * 50)
    
    analyzer = ContextAnalyzer()
    
    with console.status("📚 Analyzing commit history..."):
        commits = analyzer.get_commit_history_for_search(10)
        
        # Also get detailed analysis
        context = analyzer.analyze_context()
        last_commit = context.get("last_commit", {})
    
    console.print(f"📋 Found {len(commits)} recent commits")
    
    if last_commit:
        console.print(Panel(
            f"🔄 Last Commit: [{last_commit.get('sha', 'unknown')}]\\n"
            f"📝 Message: {last_commit.get('message', 'No message')}\\n"
            f"👤 Author: {last_commit.get('author', 'Unknown')}\\n"
            f"📅 Date: {last_commit.get('date', 'Unknown')[:19]}",
            title="Latest Commit Info",
            border_style="green"
        ))
    
    # Show recent commit messages
    console.print("\n📝 [bold cyan]Recent Commit Messages:[/bold cyan]")
    for i, commit in enumerate(commits[:5], 1):
        parts = commit.split(" | ")
        if len(parts) >= 4:
            sha, author, date, message = parts[:4]
            console.print(f"{i}. [{sha[:8]}] {message[:60]}... ({author}, {date})")
    
    return True

def demo_performance_analysis():
    """Demonstrate performance analysis"""
    console.print("\n⚡ [bold blue]Performance Analysis Demo[/bold blue]")
    console.print("=" * 50)
    
    monitor = RepositoryHealthMonitor()
    
    with console.status("⚡ Analyzing performance..."):
        perf_results = monitor.get_performance_metrics()
    
    if "error" in perf_results:
        console.print(f"❌ Error: {perf_results['error']}", style="red")
        return True
    
    # Repository size info
    repo_size = perf_results.get("repository_size", {})
    if repo_size:
        console.print("📦 [bold]Repository Size Analysis:[/bold]")
        console.print(f"  • Total size: {repo_size.get('total_size_mb', 0):.1f} MB")
        console.print(f"  • Working tree: {repo_size.get('working_tree_size_mb', 0):.1f} MB")
        console.print(f"  • Git database: {repo_size.get('git_size_mb', 0):.1f} MB")
    
    # Tracking efficiency
    tracking = perf_results.get("tracking_efficiency", {})
    if tracking:
        ratio = tracking.get("tracking_ratio", 0)
        untracked = tracking.get("untracked_files", 0)
        has_gitignore = tracking.get("has_gitignore", False)
        
        console.print("\n📊 [bold]Tracking Efficiency:[/bold]")
        console.print(f"  • Tracking ratio: {ratio:.1%}")
        console.print(f"  • Untracked files: {untracked}")
        console.print(f"  • Has .gitignore: {'✅ Yes' if has_gitignore else '❌ No'}")
    
    # Branch health
    branch_health = perf_results.get("branch_health", {})
    if branch_health:
        total_branches = branch_health.get("total_branches", 0)
        health = branch_health.get("health", "unknown")
        recommendation = branch_health.get("recommendation", "No recommendation")
        
        console.print("\n🌳 [bold]Branch Health:[/bold]")
        console.print(f"  • Total branches: {total_branches}")
        console.print(f"  • Health status: {health}")
        console.print(f"  • Recommendation: {recommendation}")
    
    return True

def main():
    """Run the demonstration"""
    console.print("🚀 [bold green]Welcome to GitPilot 2.0.0 Interactive Demo![/bold green]")
    console.print("This demo showcases the new features in GitPilot 2.0.0")
    console.print("=" * 60)
    
    demos = [
        ("Repository Health Check", demo_health_check),
        ("Git Graph Visualization", demo_git_graph),
        ("Security Analysis", demo_security_scan),
        ("Commit History Analysis", demo_commit_history),
        ("Performance Analysis", demo_performance_analysis)
    ]
    
    for demo_name, demo_func in demos:
        try:
            if not demo_func():
                console.print("\n👋 Demo ended by user choice.")
                break
        except KeyboardInterrupt:
            console.print("\n👋 Demo interrupted by user.")
            break
        except Exception as e:
            console.print(f"❌ Error in {demo_name}: {str(e)}", style="red")
            if not Confirm.ask("Continue with next demo?"):
                break
    
    console.print("\n🎉 [bold green]Demo completed! Here's what GitPilot 2.0.0 offers:[/bold green]")
    console.print("  ✅ Comprehensive repository health monitoring")
    console.print("  ✅ Visual Git graph with branch relationships")
    console.print("  ✅ Advanced security scanning and recommendations")
    console.print("  ✅ Detailed commit history analysis")
    console.print("  ✅ Performance metrics and optimization suggestions")
    console.print("  ✅ AI-powered conflict resolution (with API keys)")
    console.print("  ✅ Semantic commit search (with AI)")
    
    console.print("\\n🔧 [bold cyan]Next steps:[/bold cyan]")
    console.print("  1. Set up API keys for AI features:")
    console.print("     • export GEMINI_API_KEY='your-key'")
    console.print("     • export GROQ_API_KEY='your-key'")
    console.print("  2. Try the new CLI commands:")
    console.print("     • gitpilot health --detailed")
    console.print("     • gitpilot graph --format table")
    console.print("     • gitpilot analyze --security")
    console.print("  3. Use in VS Code with the GitPilot extension")

if __name__ == "__main__":
    main()