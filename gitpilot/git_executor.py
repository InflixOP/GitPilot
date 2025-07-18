import shlex
import subprocess
from typing import Dict, List, Optional, Tuple

from .context_analyzer import ContextAnalyzer
from .logger import GitPilotLogger


class GitExecutor:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.logger = GitPilotLogger()
        self.context_analyzer = ContextAnalyzer(repo_path)
        self.destructive_commands = {
            "reset --hard": "This will discard all uncommitted changes",
            "clean -f": "This will delete untracked files permanently",
            "push --force": "This will overwrite remote history",
            "rebase": "This will rewrite commit history",
            "cherry-pick": "This may create conflicts",
            "merge --no-ff": "This will create a merge commit"
        }
    def execute(self, command: str, dry_run: bool = False, auto_confirm: bool = False) -> Dict:
        if not command or not command.strip().startswith("git"):
            return {
                "success": False,
                "output": "",
                "error": "Invalid Git command",
                "executed": False
            }
        clean_command = self._clean_command(command)
        warnings = self._check_destructive_operations(clean_command)
        context_warnings = self.context_analyzer.get_context_warnings(clean_command)
        all_warnings = warnings + context_warnings
        if dry_run:
            return {
                "success": True,
                "output": f"Would execute: {clean_command}",
                "error": "",
                "executed": False,
                "warnings": all_warnings,
                "preview": True
            }
        try:
            result = subprocess.run(
                clean_command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=30
            )
            success = result.returncode == 0
            if success:
                self.logger.log_command(
                    user_input="",
                    git_command=clean_command,
                    success=True,
                    output=result.stdout,
                    error=""
                )
                if result.stderr:
                    self.logger.log_warning(f"Command warnings: {result.stderr}")
            else:
                self.logger.log_command(
                    user_input="",
                    git_command=clean_command,
                    success=False,
                    output=result.stdout,
                    error=result.stderr
                )
            return {
                "success": success,
                "output": result.stdout,
                "error": result.stderr if not success else "",
                "executed": True,
                "warnings": all_warnings,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            error = "Command timed out after 30 seconds"
            self.logger.log_error(error)
            return {
                "success": False,
                "output": "",
                "error": error,
                "executed": False
            }
        except Exception as e:
            error = f"Command execution failed: {str(e)}"
            self.logger.log_error(error)
            return {
                "success": False,
                "output": "",
                "error": error,
                "executed": False
            }
    def _clean_command(self, command: str) -> str:
        command = command.strip()
        if not command.startswith("git"):
            command = "git " + command
        dangerous_chars = [";", "&&", "||", "|", "`", "$", ">", "<"]
        for char in dangerous_chars:
            if char in command:
                raise ValueError(f"Potentially dangerous character detected: {char}")
        return command
    def _check_destructive_operations(self, command: str) -> List[str]:
        warnings = []
        for destructive_cmd, warning in self.destructive_commands.items():
            if destructive_cmd in command.lower():
                warnings.append(f"  {warning}")
        return warnings
    def preview_command(self, command: str) -> Dict:
        return self.execute(command, dry_run=True)
    def is_destructive_command(self, command: str) -> bool:
        return any(
            destructive_cmd in command.lower()
            for destructive_cmd in self.destructive_commands.keys()
        )