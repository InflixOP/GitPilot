"""
GitPilot Repository Health Monitor
Advanced repository health analysis and monitoring for GitPilot 2.0.0
"""

import json
import os
from typing import Dict, List
from pathlib import Path

from .context_analyzer import ContextAnalyzer
from .ai_engine import AIEngine
from .logger import GitPilotLogger


class RepositoryHealthMonitor:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.context_analyzer = ContextAnalyzer(repo_path)
        self.logger = GitPilotLogger()
        self.health_cache = {}
        
    def get_comprehensive_health_report(self, ai_engine: AIEngine = None, model_choice: str = "1") -> Dict:
        """Generate a comprehensive health report with AI analysis."""
        try:
            # Gather raw statistics
            health_stats = self.context_analyzer.get_repository_health_stats()
            if "error" in health_stats:
                return health_stats
            
            # Add conflict detection
            conflicts = self.context_analyzer.detect_merge_conflicts()
            health_stats["conflicts"] = conflicts
            
            # Add git graph info
            graph_data = self.context_analyzer.get_git_graph_data(max_commits=20)
            health_stats["recent_activity"] = {
                "total_branches": len(graph_data.get("branches", [])),
                "recent_commits": len(graph_data.get("commits", [])),
                "current_branch": graph_data.get("current_branch", "unknown")
            }
            
            # Calculate health scores
            health_scores = self._calculate_health_scores(health_stats)
            health_stats["scores"] = health_scores
            
            # Get AI analysis if available
            if ai_engine:
                ai_analysis = ai_engine.analyze_repository_health(health_stats, model_choice)
                health_stats["ai_analysis"] = ai_analysis
            else:
                health_stats["ai_analysis"] = self._basic_health_analysis(health_stats)
            
            return health_stats
            
        except Exception as e:
            self.logger.log_error(f"Health report generation failed: {str(e)}")
            return {"error": f"Failed to generate health report: {str(e)}"}
    
    def get_security_scan_results(self) -> Dict:
        """Perform security-focused repository scan."""
        try:
            security_issues = []
            repo_path = Path(self.repo_path)
            
            # Check for common security issues
            security_issues.extend(self._scan_for_secrets())
            security_issues.extend(self._scan_for_sensitive_files())
            security_issues.extend(self._check_git_configuration())
            
            return {
                "security_issues": security_issues,
                "security_score": self._calculate_security_score(security_issues),
                "recommendations": self._get_security_recommendations(security_issues)
            }
        except Exception as e:
            return {"error": f"Security scan failed: {str(e)}"}
    
    def get_performance_metrics(self) -> Dict:
        """Get repository performance metrics."""
        try:
            context = self.context_analyzer.analyze_context()
            if "error" in context:
                return context
            
            # Calculate performance metrics
            metrics = {
                "repository_size": self.context_analyzer._get_repo_size(),
                "large_files": len(self.context_analyzer._find_large_files()),
                "tracking_efficiency": self._calculate_tracking_efficiency(),
                "branch_health": self._analyze_branch_health(),
                "commit_patterns": self._analyze_commit_patterns()
            }
            
            return metrics
        except Exception as e:
            return {"error": f"Performance analysis failed: {str(e)}"}
    
    def _calculate_health_scores(self, stats: Dict) -> Dict:
        """Calculate various health scores."""
        scores = {}
        
        try:
            # Repository size score (0-100, higher is better for smaller repos)
            size_mb = stats.get("repo_size", {}).get("total_size_mb", 0)
            if size_mb < 50:
                scores["size_score"] = 100
            elif size_mb < 200:
                scores["size_score"] = 80
            elif size_mb < 500:
                scores["size_score"] = 60
            elif size_mb < 1000:
                scores["size_score"] = 40
            else:
                scores["size_score"] = 20
            
            # Activity score
            activity = stats.get("commit_activity", {})
            recent_commits = activity.get("commits_last_week", 0)
            if recent_commits > 10:
                scores["activity_score"] = 100
            elif recent_commits > 5:
                scores["activity_score"] = 80
            elif recent_commits > 0:
                scores["activity_score"] = 60
            else:
                scores["activity_score"] = 30
            
            # Security score
            security_issues = len(stats.get("security_issues", []))
            if security_issues == 0:
                scores["security_score"] = 100
            elif security_issues < 3:
                scores["security_score"] = 70
            elif security_issues < 6:
                scores["security_score"] = 50
            else:
                scores["security_score"] = 20
            
            # Performance score
            perf_metrics = stats.get("performance_metrics", {})
            has_gitignore = perf_metrics.get("has_gitignore", False)
            tracking_ratio = perf_metrics.get("tracking_ratio", 0)
            
            perf_score = 50
            if has_gitignore:
                perf_score += 25
            if tracking_ratio > 0.8:
                perf_score += 25
            
            scores["performance_score"] = min(perf_score, 100)
            
            # Overall score (weighted average)
            scores["overall_score"] = round(
                (scores["size_score"] * 0.2 + 
                 scores["activity_score"] * 0.3 + 
                 scores["security_score"] * 0.3 + 
                 scores["performance_score"] * 0.2)
            )
            
            return scores
            
        except Exception:
            return {"overall_score": 0, "size_score": 0, "activity_score": 0, "security_score": 0, "performance_score": 0}
    
    def _basic_health_analysis(self, stats: Dict) -> Dict:
        """Basic health analysis when AI is not available."""
        scores = stats.get("scores", {})
        overall_score = scores.get("overall_score", 0)
        
        if overall_score >= 90:
            health_level = "excellent"
        elif overall_score >= 75:
            health_level = "good"
        elif overall_score >= 60:
            health_level = "fair"
        else:
            health_level = "poor"
        
        recommendations = []
        
        # Generate basic recommendations
        if scores.get("size_score", 0) < 60:
            recommendations.append("Consider cleaning up large files or using Git LFS")
        
        if scores.get("security_score", 0) < 80:
            recommendations.append("Review and fix security issues found in the repository")
        
        if not stats.get("performance_metrics", {}).get("has_gitignore", False):
            recommendations.append("Add a .gitignore file to improve repository performance")
        
        return {
            "overall_health": health_level,
            "health_score": overall_score,
            "recommendations": recommendations,
            "summary": f"Repository health is {health_level} with a score of {overall_score}/100",
            "issues": []
        }
    
    def _scan_for_secrets(self) -> List[Dict]:
        """Scan for potential secrets in files."""
        issues = []
        try:
            repo_path = Path(self.repo_path)
            
            # Simple regex patterns for common secrets
            secret_patterns = [
                (r'api[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}', 'API Key'),
                (r'secret[_-]?key[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}', 'Secret Key'),
                (r'password[\'"\s]*[:=][\'"\s]*[^\s\'"]{8,}', 'Password'),
                (r'token[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9]{20,}', 'Token'),
            ]
            
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and file_path.suffix in ['.py', '.js', '.ts', '.env', '.config', '.json', '.yaml', '.yml']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        import re
                        for pattern, secret_type in secret_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append({
                                    "type": "potential_secret",
                                    "severity": "high",
                                    "file": str(file_path.relative_to(repo_path)),
                                    "description": f"Potential {secret_type} found in file",
                                    "recommendation": "Review and remove hardcoded secrets"
                                })
                                break  # Only report once per file
                    except Exception:
                        continue
        except Exception:
            pass
        
        return issues
    
    def _scan_for_sensitive_files(self) -> List[Dict]:
        """Scan for sensitive files that shouldn't be in version control."""
        return self.context_analyzer._check_security_issues()
    
    def _check_git_configuration(self) -> List[Dict]:
        """Check Git configuration for security issues."""
        issues = []
        try:
            # Check if repository has proper remotes configured
            if not self.context_analyzer.repo.remotes:
                issues.append({
                    "type": "configuration",
                    "severity": "medium",
                    "description": "No remote repositories configured",
                    "recommendation": "Consider adding a remote repository for backup"
                })
        except Exception:
            pass
        
        return issues
    
    def _calculate_security_score(self, security_issues: List[Dict]) -> int:
        """Calculate security score based on issues."""
        if not security_issues:
            return 100
        
        high_severity = sum(1 for issue in security_issues if issue.get("severity") == "high")
        medium_severity = sum(1 for issue in security_issues if issue.get("severity") == "medium")
        low_severity = sum(1 for issue in security_issues if issue.get("severity") == "low")
        
        # Deduct points based on severity
        score = 100 - (high_severity * 30) - (medium_severity * 15) - (low_severity * 5)
        return max(score, 0)
    
    def _get_security_recommendations(self, security_issues: List[Dict]) -> List[str]:
        """Get security recommendations based on issues."""
        recommendations = set()
        
        for issue in security_issues:
            if issue.get("recommendation"):
                recommendations.add(issue["recommendation"])
        
        # Add general recommendations
        recommendations.add("Regularly scan for secrets and sensitive data")
        recommendations.add("Use .gitignore to exclude sensitive files")
        recommendations.add("Consider using Git hooks to prevent committing secrets")
        
        return list(recommendations)
    
    def _calculate_tracking_efficiency(self) -> Dict:
        """Calculate how efficiently the repository is tracking files."""
        try:
            perf_metrics = self.context_analyzer._get_performance_metrics()
            return {
                "tracking_ratio": perf_metrics.get("tracking_ratio", 0),
                "untracked_files": perf_metrics.get("untracked_files_count", 0),
                "has_gitignore": perf_metrics.get("has_gitignore", False)
            }
        except Exception:
            return {"tracking_ratio": 0, "untracked_files": 0, "has_gitignore": False}
    
    def _analyze_branch_health(self) -> Dict:
        """Analyze branch management health."""
        try:
            branch_stats = self.context_analyzer._get_branch_statistics()
            total_branches = branch_stats.get("total_local_branches", 0)
            
            health = "good"
            if total_branches > 20:
                health = "poor"
                recommendation = "Consider cleaning up old branches"
            elif total_branches > 10:
                health = "fair"
                recommendation = "Monitor branch count"
            else:
                recommendation = "Branch management looks healthy"
            
            return {
                "total_branches": total_branches,
                "health": health,
                "recommendation": recommendation
            }
        except Exception:
            return {"total_branches": 0, "health": "unknown", "recommendation": "Unable to analyze"}
    
    def _analyze_commit_patterns(self) -> Dict:
        """Analyze commit patterns for insights."""
        try:
            activity = self.context_analyzer._get_commit_activity()
            
            # Determine commit frequency pattern
            commits_per_day = activity.get("avg_commits_per_day", 0)
            
            if commits_per_day > 2:
                pattern = "very_active"
            elif commits_per_day > 0.5:
                pattern = "active"
            elif commits_per_day > 0.1:
                pattern = "moderate"
            else:
                pattern = "inactive"
            
            return {
                "pattern": pattern,
                "avg_commits_per_day": commits_per_day,
                "commits_last_week": activity.get("commits_last_week", 0),
                "commits_last_month": activity.get("commits_last_month", 0)
            }
        except Exception:
            return {"pattern": "unknown", "avg_commits_per_day": 0, "commits_last_week": 0, "commits_last_month": 0}