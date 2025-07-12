"""
Git context analysis for GitPilot
"""

from pathlib import Path
from typing import Dict, List, Optional

import git
from git import exc


class ContextAnalyzer:
    """Analyzes Git repository context and state"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.repo = None
        self._init_repo()
    
    def _init_repo(self):
        """Initialize Git repository object"""
        try:
            self.repo = git.Repo(self.repo_path)
        except exc.InvalidGitRepositoryError:
            self.repo = None
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository"""
        return self.repo is not None
    
    def analyze_context(self) -> Dict:
        """Analyze current Git repository state"""
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
        """Get current branch name"""
        try:
            if self.repo is None:
                return "unknown"
            if self.repo.head.is_detached:
                return f"HEAD detached at {self.repo.head.commit.hexsha[:7]}"
            return self.repo.active_branch.name
        except:
            return "unknown"
    
    def _get_remote_status(self) -> Dict:
        """Get remote repository status"""
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
        """Get information about the last commit"""
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
        """Generate context-aware warnings"""
        warnings = []
        context = self.analyze_context()
        
        if "error" in context:
            return [context["error"]]
        
        # Check for potentially destructive operations
        destructive_commands = ["reset", "rebase", "force", "clean"]
        if any(cmd in command.lower() for cmd in destructive_commands):
            if context["is_dirty"]:
                warnings.append("You have uncommitted changes. Consider stashing them first.")
            
            if context["remote_status"]["behind"] > 0:
                warnings.append("Your branch is behind remote. Consider pulling first.")
        
        # Check for push/pull operations
        if "push" in command.lower():
            if context["remote_status"]["behind"] > 0:
                warnings.append("Your branch is behind remote. Consider pulling first.")
        
        if "pull" in command.lower():
            if context["is_dirty"]:
                warnings.append("You have uncommitted changes. Consider stashing them first.")
        
        return warnings
