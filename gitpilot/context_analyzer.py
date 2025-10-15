from pathlib import Path
from typing import Dict, List, Optional
import os
import subprocess
from datetime import datetime, timedelta

import git
from git import exc


class ContextAnalyzer:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.repo = None
        self._init_repo()
    def _init_repo(self):
        try:
            self.repo = git.Repo(self.repo_path)
        except exc.InvalidGitRepositoryError:
            self.repo = None
    def is_git_repo(self) -> bool:
        return self.repo is not None
    def analyze_context(self) -> Dict:
        if not self.is_git_repo() or self.repo is None:
            return {"error": "Not a Git repository"}
        try:
            context = {
                "branch": self._get_current_branch(),
                "is_dirty": self.repo.is_dirty() if self.repo else False,
                "staged_files": len(list(self.repo.index.diff("HEAD"))) if self.repo else 0,
                "unstaged_files": len(list(self.repo.index.diff(None))) if self.repo else 0,
                "untracked_files": len(self.repo.untracked_files) if self.repo else 0,
                "is_detached": self.repo.head.is_detached if self.repo else False,
                "remote_status": self._get_remote_status(),
                "last_commit": self._get_last_commit_info(),
                "stash_count": len(self.repo.git.stash("list").splitlines()) if self.repo and self.repo.git.stash("list") else 0
            }
            return context
        except Exception as e:
            return {"error": f"Failed to analyze context: {str(e)}"}
    def _get_current_branch(self) -> str:
        try:
            if self.repo is None:
                return "unknown"
            if self.repo.head.is_detached:
                return f"HEAD detached at {self.repo.head.commit.hexsha[:7]}"
            return self.repo.active_branch.name
        except:
            return "unknown"
    def _get_remote_status(self) -> Dict:
        try:
            if self.repo is None:
                return {"has_remote": False}
            origin = self.repo.remotes.origin
            origin.fetch()
            local_commit = self.repo.head.commit
            remote_commit = origin.refs[self.repo.active_branch.name].commit
            behind = len(list(self.repo.iter_commits(f"{local_commit.hexsha}..{remote_commit.hexsha}")))
            ahead = len(list(self.repo.iter_commits(f"{remote_commit.hexsha}..{local_commit.hexsha}")))
            return {
                "has_remote": True,
                "ahead": ahead,
                "behind": behind,
                "up_to_date": ahead == 0 and behind == 0
            }
        except:
            return {"has_remote": False}
    def _get_last_commit_info(self) -> Dict:
        try:
            if self.repo is None:
                return {}
            last_commit = self.repo.head.commit
            return {
                "sha": last_commit.hexsha[:7],
                "message": last_commit.message.strip(),
                "author": last_commit.author.name,
                "date": last_commit.committed_datetime.isoformat()
            }
        except:
            return {}
    def get_context_warnings(self, command: str) -> List[str]:
        warnings = []
        context = self.analyze_context()
        if "error" in context:
            return [context["error"]]
        destructive_commands = ["reset", "rebase", "force", "clean"]
        if any(cmd in command.lower() for cmd in destructive_commands):
            if context["is_dirty"]:
                warnings.append("You have uncommitted changes. Consider stashing them first.")
            if context["remote_status"]["behind"] > 0:
                warnings.append("Your branch is behind remote. Consider pulling first.")
        if "push" in command.lower():
            if context["remote_status"]["behind"] > 0:
                warnings.append("Your branch is behind remote. Consider pulling first.")
        if "pull" in command.lower():
            if context["is_dirty"]:
                warnings.append("You have uncommitted changes. Consider stashing them first.")
        return warnings

    def get_repository_health_stats(self) -> Dict:
        """Gather comprehensive repository health statistics."""
        if not self.is_git_repo() or self.repo is None:
            return {"error": "Not a Git repository"}
        
        try:
            stats = {
                "repo_size": self._get_repo_size(),
                "large_files": self._find_large_files(),
                "commit_activity": self._get_commit_activity(),
                "branch_info": self._get_branch_statistics(),
                "file_types": self._analyze_file_types(),
                "security_issues": self._check_security_issues(),
                "performance_metrics": self._get_performance_metrics()
            }
            return stats
        except Exception as e:
            return {"error": f"Failed to gather health stats: {str(e)}"}

    def get_commit_history_for_search(self, limit: int = 100) -> List[str]:
        """Get formatted commit history for semantic search."""
        if not self.is_git_repo() or self.repo is None:
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commit_info = f"{commit.hexsha[:8]} | {commit.author.name} | {commit.committed_datetime.strftime('%Y-%m-%d %H:%M')} | {commit.message.strip()}"
                commits.append(commit_info)
            return commits
        except Exception:
            return []

    def get_git_graph_data(self, max_commits: int = 50) -> Dict:
        """Generate data for visual Git graph representation."""
        if not self.is_git_repo() or self.repo is None:
            return {"error": "Not a Git repository"}
        
        try:
            branches = []
            commits = []
            
            # Get all branches
            for branch in self.repo.branches:
                branches.append({
                    "name": branch.name,
                    "is_active": branch == self.repo.active_branch,
                    "last_commit": branch.commit.hexsha[:8],
                    "last_commit_date": branch.commit.committed_datetime.isoformat()
                })
            
            # Get commit graph data
            for commit in self.repo.iter_commits(max_count=max_commits, all=True):
                parent_shas = [parent.hexsha[:8] for parent in commit.parents]
                commits.append({
                    "sha": commit.hexsha[:8],
                    "full_sha": commit.hexsha,
                    "message": commit.message.strip(),
                    "author": commit.author.name,
                    "date": commit.committed_datetime.isoformat(),
                    "parents": parent_shas,
                    "is_merge": len(parent_shas) > 1
                })
            
            return {
                "branches": branches,
                "commits": commits,
                "current_branch": self._get_current_branch(),
                "head_commit": self.repo.head.commit.hexsha[:8] if self.repo.head.commit else None
            }
        except Exception as e:
            return {"error": f"Failed to generate graph data: {str(e)}"}

    def detect_merge_conflicts(self) -> Dict:
        """Detect and analyze merge conflicts."""
        if not self.is_git_repo() or self.repo is None:
            return {"has_conflicts": False}
        
        try:
            # Check if we're in a merge state
            git_dir = Path(self.repo.git_dir)
            merge_head_file = git_dir / "MERGE_HEAD"
            
            if not merge_head_file.exists():
                return {"has_conflicts": False}
            
            # Get conflicted files
            conflicted_files = []
            status = self.repo.git.status("--porcelain").split("\n")
            
            for line in status:
                if line.strip() and ("UU" in line[:2] or "AA" in line[:2] or "DD" in line[:2]):
                    file_path = line[3:].strip()
                    conflicted_files.append({
                        "file": file_path,
                        "status": line[:2],
                        "conflict_markers": self._count_conflict_markers(file_path)
                    })
            
            return {
                "has_conflicts": len(conflicted_files) > 0,
                "conflicted_files": conflicted_files,
                "merge_branch": self._get_merge_branch_name()
            }
        except Exception as e:
            return {"has_conflicts": False, "error": str(e)}

    def _get_repo_size(self) -> Dict:
        """Calculate repository size metrics."""
        try:
            repo_path = Path(self.repo.working_dir)
            total_size = sum(f.stat().st_size for f in repo_path.rglob('*') if f.is_file() and '.git' not in str(f))
            git_size = sum(f.stat().st_size for f in (repo_path / '.git').rglob('*') if f.is_file())
            
            return {
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "git_size_mb": round(git_size / (1024 * 1024), 2),
                "working_tree_size_mb": round((total_size - git_size) / (1024 * 1024), 2)
            }
        except Exception:
            return {"total_size_mb": 0, "git_size_mb": 0, "working_tree_size_mb": 0}

    def _find_large_files(self, threshold_mb: float = 10.0) -> List[Dict]:
        """Find large files in the repository."""
        try:
            repo_path = Path(self.repo.working_dir)
            large_files = []
            
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and '.git' not in str(file_path):
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > threshold_mb:
                        large_files.append({
                            "file": str(file_path.relative_to(repo_path)),
                            "size_mb": round(size_mb, 2)
                        })
            
            return sorted(large_files, key=lambda x: x["size_mb"], reverse=True)[:20]
        except Exception:
            return []

    def _get_commit_activity(self) -> Dict:
        """Analyze recent commit activity."""
        try:
            now = datetime.now()
            last_week = now - timedelta(days=7)
            last_month = now - timedelta(days=30)
            
            recent_commits = 0
            weekly_commits = 0
            monthly_commits = 0
            
            for commit in self.repo.iter_commits(max_count=200):
                commit_date = commit.committed_datetime.replace(tzinfo=None)
                if commit_date > last_month:
                    monthly_commits += 1
                    if commit_date > last_week:
                        weekly_commits += 1
                        if commit_date > now - timedelta(days=1):
                            recent_commits += 1
            
            return {
                "commits_last_24h": recent_commits,
                "commits_last_week": weekly_commits,
                "commits_last_month": monthly_commits,
                "avg_commits_per_day": round(monthly_commits / 30, 2)
            }
        except Exception:
            return {"commits_last_24h": 0, "commits_last_week": 0, "commits_last_month": 0, "avg_commits_per_day": 0}

    def _get_branch_statistics(self) -> Dict:
        """Get branch-related statistics."""
        try:
            total_branches = len(list(self.repo.branches))
            remote_branches = len(list(self.repo.remote().refs)) if self.repo.remotes else 0
            
            return {
                "total_local_branches": total_branches,
                "total_remote_branches": remote_branches,
                "current_branch": self._get_current_branch()
            }
        except Exception:
            return {"total_local_branches": 0, "total_remote_branches": 0, "current_branch": "unknown"}

    def _analyze_file_types(self) -> Dict:
        """Analyze file types in the repository."""
        try:
            repo_path = Path(self.repo.working_dir)
            file_types = {}
            total_files = 0
            
            for file_path in repo_path.rglob('*'):
                if file_path.is_file() and '.git' not in str(file_path):
                    total_files += 1
                    extension = file_path.suffix.lower()
                    if not extension:
                        extension = 'no_extension'
                    file_types[extension] = file_types.get(extension, 0) + 1
            
            # Sort by count and take top 10
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                "total_files": total_files,
                "file_types": dict(sorted_types)
            }
        except Exception:
            return {"total_files": 0, "file_types": {}}

    def _check_security_issues(self) -> List[Dict]:
        """Check for potential security issues."""
        issues = []
        
        try:
            repo_path = Path(self.repo.working_dir)
            
            # Check for sensitive file patterns
            sensitive_patterns = [
                ('*.key', 'Private key file'),
                ('*.pem', 'Certificate file'),
                ('.env', 'Environment file with secrets'),
                ('*.p12', 'Certificate file'),
                ('id_rsa', 'SSH private key'),
                ('*.pfx', 'Certificate file')
            ]
            
            for pattern, description in sensitive_patterns:
                matching_files = list(repo_path.rglob(pattern))
                if matching_files:
                    issues.append({
                        "type": "sensitive_files",
                        "severity": "high",
                        "description": f"Found {description}: {[str(f.relative_to(repo_path)) for f in matching_files[:5]]}",
                        "count": len(matching_files)
                    })
            
            return issues
        except Exception:
            return []

    def _get_performance_metrics(self) -> Dict:
        """Get performance-related metrics."""
        try:
            # Check for .gitignore
            repo_path = Path(self.repo.working_dir)
            has_gitignore = (repo_path / '.gitignore').exists()
            
            # Count untracked files
            untracked_count = len(self.repo.untracked_files) if self.repo.untracked_files else 0
            
            # Estimate working tree files
            working_tree_files = sum(1 for f in repo_path.rglob('*') if f.is_file() and '.git' not in str(f))
            
            return {
                "has_gitignore": has_gitignore,
                "untracked_files_count": untracked_count,
                "working_tree_files": working_tree_files,
                "tracking_ratio": round((working_tree_files - untracked_count) / max(working_tree_files, 1), 2)
            }
        except Exception:
            return {"has_gitignore": False, "untracked_files_count": 0, "working_tree_files": 0, "tracking_ratio": 0}

    def _count_conflict_markers(self, file_path: str) -> int:
        """Count conflict markers in a file."""
        try:
            full_path = Path(self.repo.working_dir) / file_path
            if not full_path.exists():
                return 0
            
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return content.count('<<<<<<< ') + content.count('>>>>>>> ') + content.count('=======')
        except Exception:
            return 0

    def _get_merge_branch_name(self) -> Optional[str]:
        """Get the name of the branch being merged."""
        try:
            git_dir = Path(self.repo.git_dir)
            merge_head_file = git_dir / "MERGE_HEAD"
            
            if merge_head_file.exists():
                merge_msg_file = git_dir / "MERGE_MSG"
                if merge_msg_file.exists():
                    with open(merge_msg_file, 'r') as f:
                        first_line = f.readline().strip()
                        # Extract branch name from merge message
                        if "branch '" in first_line:
                            start = first_line.find("branch '") + 8
                            end = first_line.find("'", start)
                            return first_line[start:end]
            return None
        except Exception:
            return None
