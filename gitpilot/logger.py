"""
Logging and history management for GitPilot
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


class GitPilotLogger:
    """Manages logging and command history for GitPilot"""
    
    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = Path(log_dir) if log_dir else Path.home() / ".gitpilot"
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup loguru
        log_file = self.log_dir / "gitpilot.log"
        logger.add(
            log_file,
            rotation="10 MB",
            retention="30 days",
            level="INFO",
            format="{time} | {level} | {message}"
        )
        
        self.history_file = self.log_dir / "command_history.json"
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """Load command history from file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_history(self):
        """Save command history to file"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def log_command(self, user_input: str, git_command: str, 
                   success: bool, output: str = "", error: str = ""):
        """Log a command execution"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "git_command": git_command,
            "success": success,
            "output": output,
            "error": error
        }
        
        self.history.append(entry)
        self._save_history()
        
        # Log to file
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{status}: '{user_input}' -> '{git_command}'")
        
        if error:
            logger.error(f"Command failed: {error}")
    
    def log_ai_query(self, query: str, response: str, provider: str):
        """Log AI API interactions"""
        logger.info(f"AI Query [{provider}]: {query[:100]}...")
        logger.debug(f"AI Response: {response}")
    
    def log_error(self, error: str):
        """Log error messages"""
        logger.error(error)
    
    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """Get recent command history"""
        return self.history[-limit:]
    
    def get_history_by_date(self, date: str) -> List[Dict]:
        """Get command history for a specific date"""
        return [
            entry for entry in self.history
            if entry["timestamp"].startswith(date)
        ]
