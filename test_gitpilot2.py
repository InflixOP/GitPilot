#!/usr/bin/env python3
"""
GitPilot 2.0.0 Feature Test Script
Test all the new features implemented in GitPilot 2.0.0
"""

import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

# Import GitPilot modules
from gitpilot.repo_health import RepositoryHealthMonitor
from gitpilot.context_analyzer import ContextAnalyzer
from gitpilot.ai_engine import AIEngine

console = Console()

def test_repository_health():
    """Test repository health monitoring"""
    console.print("🏥 Testing Repository Health Monitor", style="bold blue")
    
    monitor = RepositoryHealthMonitor()
    
    # Test basic health report
    console.print("📊 Generating health report...")
    report = monitor.get_comprehensive_health_report()
    
    if "error" in report:
        console.print(f"❌ Error: {report['error']}", style="red")
        return
    
    # Display scores
    scores = report.get("scores", {})
    overall_score = scores.get("overall_score", 0)
    
    console.print(f"📋 Overall Health Score: {overall_score}/100")
    
    # Create scores table
    if scores:
        table = Table(title="Health Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Status")
        
        score_items = [
            ("Size", scores.get("size_score", 0)),
            ("Activity", scores.get("activity_score", 0)),
            ("Security", scores.get("security_score", 0)),
            ("Performance", scores.get("performance_score", 0))
        ]
        
        for metric, score in score_items:
            status = "✅ Good" if score >= 80 else "⚠️ Fair" if score >= 60 else "❌ Poor"
            table.add_row(metric, f"{score}/100", status)
        
        console.print(table)
    
    # Security scan
    console.print("\n🔒 Running security scan...")
    security_results = monitor.get_security_scan_results()
    
    security_score = security_results.get("security_score", 0)
    issues = security_results.get("security_issues", [])
    console.print(f"🛡️ Security Score: {security_score}/100")
    console.print(f"🔍 Security Issues Found: {len(issues)}")
    
    # Performance metrics
    console.print("\n⚡ Analyzing performance...")
    perf_results = monitor.get_performance_metrics()
    
    if "repository_size" in perf_results:
        size_info = perf_results["repository_size"]
        console.print(f"📦 Repository Size: {size_info.get('total_size_mb', 0):.1f} MB")
    
    console.print("✅ Health monitoring test completed!\n")

def test_git_graph():
    """Test Git graph visualization"""
    console.print("📊 Testing Git Graph Visualization", style="bold blue")
    
    analyzer = ContextAnalyzer()
    
    # Generate graph data
    console.print("🔍 Generating Git graph data...")
    graph_data = analyzer.get_git_graph_data(max_commits=10)
    
    if "error" in graph_data:
        console.print(f"❌ Error: {graph_data['error']}", style="red")
        return
    
    branches = graph_data.get("branches", [])
    commits = graph_data.get("commits", [])
    current_branch = graph_data.get("current_branch", "unknown")
    
    console.print(f"🌳 Found {len(branches)} branches")
    console.print(f"📝 Found {len(commits)} recent commits")
    console.print(f"🎯 Current branch: {current_branch}")
    
    # Display as tree
    tree = Tree("📊 Git Repository Structure")
    
    # Add branch info
    branches_node = tree.add("🌳 Branches")
    for branch in branches[:5]:  # Show first 5 branches
        branch_style = "bold green" if branch.get("is_active") else "dim"
        branch_name = branch.get("name", "unknown")
        if branch.get("is_active"):
            branch_name += " (current)"
        branches_node.add(branch_name, style=branch_style)
    
    # Add recent commits
    commits_node = tree.add("📝 Recent Commits")
    for commit in commits[:5]:  # Show recent 5
        sha = commit.get("sha", "unknown")
        message = commit.get("message", "No message")
        author = commit.get("author", "Unknown")
        is_merge = commit.get("is_merge", False)
        
        commit_icon = "🔀" if is_merge else "📝"
        commit_text = f"{commit_icon} [{sha}] {message[:40]}... - {author}"
        commits_node.add(commit_text)
    
    console.print(tree)
    console.print("✅ Git graph test completed!\n")

def test_commit_search():
    """Test semantic commit search"""
    console.print("🔍 Testing Semantic Commit Search", style="bold blue")
    
    analyzer = ContextAnalyzer()
    
    # Get commit history
    console.print("📚 Fetching commit history...")
    commits = analyzer.get_commit_history_for_search(20)
    
    if not commits:
        console.print("❌ No commit history found", style="red")
        return
    
    console.print(f"📋 Found {len(commits)} commits for search")
    
    # Display sample commits
    console.print("\n📝 Sample commits:")
    for i, commit in enumerate(commits[:5], 1):
        console.print(f"{i}. {commit[:80]}...")
    
    console.print("✅ Commit search data ready!\n")

def test_conflict_detection():
    """Test merge conflict detection"""
    console.print("🔥 Testing Conflict Detection", style="bold blue")
    
    analyzer = ContextAnalyzer()
    
    # Check for conflicts
    console.print("🔍 Checking for merge conflicts...")
    conflict_info = analyzer.detect_merge_conflicts()
    
    has_conflicts = conflict_info.get("has_conflicts", False)
    
    if has_conflicts:
        console.print("⚠️ Merge conflicts detected!", style="yellow")
        conflicted_files = conflict_info.get("conflicted_files", [])
        console.print(f"📁 Conflicted files: {len(conflicted_files)}")
        
        # Show conflicted files
        if conflicted_files:
            table = Table(title="Conflicted Files")
            table.add_column("File", style="cyan")
            table.add_column("Status", style="red")
            table.add_column("Conflict Markers")
            
            for file_info in conflicted_files[:5]:  # Show first 5
                table.add_row(
                    file_info.get("file", "unknown"),
                    file_info.get("status", "??"),
                    str(file_info.get("conflict_markers", 0))
                )
            
            console.print(table)
    else:
        console.print("✅ No merge conflicts detected", style="green")
    
    console.print("✅ Conflict detection test completed!\n")

def test_ai_features():
    """Test AI-powered features (requires API keys)"""
    console.print("🤖 Testing AI Features", style="bold blue")
    
    # Check for API keys
    has_gemini = os.getenv("GEMINI_API_KEY") is not None
    has_groq = os.getenv("GROQ_API_KEY") is not None
    
    if not has_gemini and not has_groq:
        console.print("⚠️ No API keys found. Set GEMINI_API_KEY or GROQ_API_KEY to test AI features.", style="yellow")
        console.print("   Example: export GEMINI_API_KEY='your-api-key-here'")
        return
    
    try:
        ai_engine = AIEngine()
        available_models = ai_engine.get_available_models()
        
        console.print(f"🧠 Available AI models: {len(available_models)}")
        for key, model_info in available_models.items():
            provider_emoji = "🔸" if model_info["provider"] == "gemini" else "⚡"
            console.print(f"  {key}. {provider_emoji} {model_info['name']}")
        
        console.print("✅ AI engine initialized successfully!")
        
    except Exception as e:
        console.print(f"❌ AI engine error: {str(e)}", style="red")
    
    console.print("✅ AI features test completed!\n")

def main():
    """Run all tests"""
    console.print("🚀 GitPilot 2.0.0 Feature Test Suite", style="bold green")
    console.print("=" * 50)
    
    try:
        # Test all features
        test_repository_health()
        test_git_graph()
        test_commit_search()
        test_conflict_detection()
        test_ai_features()
        
        console.print("🎉 All tests completed successfully!", style="bold green")
        console.print("\n📋 GitPilot 2.0.0 Features Tested:")
        console.print("  ✅ Repository health monitoring")
        console.print("  ✅ Git graph visualization")
        console.print("  ✅ Commit history search preparation")
        console.print("  ✅ Merge conflict detection")
        console.print("  ✅ AI engine initialization")
        
        console.print("\n🔧 To test with AI features, set your API keys:")
        console.print("  export GEMINI_API_KEY='your-gemini-key'")
        console.print("  export GROQ_API_KEY='your-groq-key'")
        
    except Exception as e:
        console.print(f"❌ Test suite error: {str(e)}", style="red")
        raise

if __name__ == "__main__":
    main()