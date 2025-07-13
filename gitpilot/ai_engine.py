"""
AI Engine for GitPilot - handles AI model integration
"""

import json
import os
import time
from typing import Dict, Optional, Tuple

import google.generativeai as genai
import openai

from .logger import GitPilotLogger
from .prompts import CONTEXT_PROMPT, SYSTEM_PROMPT


class AIEngine:
    """Handles AI model integration for command generation"""
    def __init__(self, provider: str = "gemini", api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.logger = GitPilotLogger()
        # Initialize AI client
        if self.provider == "gemini":
            genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
            self.client = genai
        elif self.provider == "openai":
            openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.client = openai
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def generate_command(self, user_input: str, context: Dict) -> Dict:
        """Generate Git command from natural language input"""
        try:
            if self.provider == "gemini":
                return self._generate_with_gemini(user_input, context)
            elif self.provider == "openai":
                return self._generate_with_openai(user_input, context)
        except Exception as e:
            self.logger.log_error(f"AI generation failed: {str(e)}")
            return {
                "command": None,
                "explanation": f"Failed to generate command: {str(e)}",
                "warning": "Please try again or use manual Git commands"
            }
        # Fallback return for linter
        return {"command": None, "explanation": "Unknown error", "warning": None}
    
    def _generate_with_gemini(self, user_input: str, context: Dict) -> Dict:
        """Generate command using Gemini"""
        prompt = self._build_prompt(user_input, context)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        self.logger.log_ai_query(user_input, response_text, "gemini")
        return self._parse_ai_response(response_text)
    
    def _generate_with_openai(self, user_input: str, context: Dict) -> Dict:
        """Generate command using OpenAI"""
        prompt = self._build_prompt(user_input, context)
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content or ""
        self.logger.log_ai_query(user_input, response_text, "openai")
        
        return self._parse_ai_response(response_text)
    
    def _build_prompt(self, user_input: str, context: Dict) -> str:
        """Build AI prompt with context"""
        context_str = self._format_context(context)
        
        return CONTEXT_PROMPT.format(
            branch=context.get("branch", "unknown"),
            is_dirty=context.get("is_dirty", False),
            staged_files=context.get("staged_files", 0),
            unstaged_files=context.get("unstaged_files", 0),
            is_detached=context.get("is_detached", False),
            remote_status=context.get("remote_status", {}),
            user_input=user_input
        )
    
    def _format_context(self, context: Dict) -> str:
        """Format context for AI prompt"""
        if "error" in context:
            return f"Error: {context['error']}"
        
        lines = [
            f"Branch: {context.get('branch', 'unknown')}",
            f"Dirty: {context.get('is_dirty', False)}",
            f"Staged files: {context.get('staged_files', 0)}",
            f"Unstaged files: {context.get('unstaged_files', 0)}",
            f"Untracked files: {context.get('untracked_files', 0)}",
        ]
        
        if context.get("remote_status", {}).get("has_remote"):
            remote = context["remote_status"]
            lines.append(f"Remote: {remote.get('ahead', 0)} ahead, {remote.get('behind', 0)} behind")
        
        return "\n".join(lines)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured format"""
        try:
            # Try to parse as JSON first
            if response.strip().startswith("{"):
                return json.loads(response)
            
            # Fallback: extract command from text
            lines = response.strip().split("\n")
            command = None
            explanation = ""
            warning = None
            
            for line in lines:
                line = line.strip()
                if line.startswith("git "):
                    command = line
                elif line.startswith("Warning:") or line.startswith("Note:"):
                    warning = line
                elif line and not command:
                    explanation += line + " "
            
            return {
                "command": command,
                "explanation": explanation.strip(),
                "warning": warning
            }
        
        except json.JSONDecodeError:
            # If parsing fails, return the raw response
            return {
                "command": None,
                "explanation": response,
                "warning": "Failed to parse AI response"
            }
