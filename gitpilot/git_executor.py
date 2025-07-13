"""
Git command execution with safety checks
"""

import shlex
import subprocess
from typing import Dict, List, Optional, Tuple

from .context_analyzer import ContextAnalyzer
from .logger import GitPilotLogger


class GitExecutor:
    """Executes Git commands with safety checks and previews"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.logger = GitPilotLogger()
        self.context_analyzer = ContextAnalyzer(repo_path)
        
        # Define destructive commands that require confirmation
        self.destructive_commands = {
            "reset --hard": "This will discard all uncommitted changes",
            "clean -f": "This will delete untracked files permanently",
            "push --force": "This will overwrite remote history",
            "rebase": "This will rewrite commit history",
            "cherry-pick": "This may create conflicts",
            "merge --no-ff": "This will create a merge commit"
        }
    
    def execute(self, command: str, dry_run: bool = False, 
                auto_confirm: bool = False) -> Dict:
        """Execute Git command with safety checks"""
        
        # Validate command
        if not command or not command.strip().startswith("git"):
            return {
                "success": False,
                "output": "",
                "error": "Invalid Git command",
                "executed": False
            }
        
        # Clean and validate command
        clean_command = self._clean_command(command)
        
        # Check for destructive operations
        warnings = self._check_destructive_operations(clean_command)
        
        # Get context warnings
        context_warnings = self.context_analyzer.get_context_warnings(clean_command)
        all_warnings = warnings + context_warnings
        
        # Return preview if dry run
        if dry_run:
            return {
                "success": True,
                "output": f"Would execute: {clean_command}",
                "error": "",
                "executed": False,
                "warnings": all_warnings,
                "preview": True
            }
        
        # Execute command
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
            
            # Log execution with proper error handling
            if success:
                # Command succeeded - log as success
                self.logger.log_command(
                    user_input="",  # Will be set by CLI
                    git_command=clean_command,
                    success=True,
                    output=result.stdout,
                    error=""  # Don't treat stderr as error if command succeeded
                )
                
                # If there's stderr content but command succeeded, it's just warnings
                if result.stderr:
                    self.logger.log_warning(f"Command warnings: {result.stderr}")
            else:
                # Command failed - log as error
                self.logger.log_command(
                    user_input="",  # Will be set by CLI
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
        """Clean and validate Git command"""
        # Remove extra whitespace
        command = command.strip()
        
        # Ensure command starts with git
        if not command.startswith("git"):
            command = "git " + command
        
        # Basic command injection prevention
        dangerous_chars = [";", "&&", "||", "|", "`", "$", ">", "<"]
        for char in dangerous_chars:
            if char in command:
                raise ValueError(f"Potentially dangerous character detected: {char}")
        
        return command
    
    def _check_destructive_operations(self, command: str) -> List[str]:
        """Check for destructive operations and return warnings"""
        warnings = []
        
        for destructive_cmd, warning in self.destructive_commands.items():
            if destructive_cmd in command.lower():
                warnings.append(f"⚠️  {warning}")
        
        return warnings
    
    def preview_command(self, command: str) -> Dict:
        """Show command preview without execution"""
        return self.execute(command, dry_run=True)
    
    def is_destructive_command(self, command: str) -> bool:
        """Check if command is potentially destructive"""
        return any(
            destructive_cmd in command.lower() 
            for destructive_cmd in self.destructive_commands.keys()
        )