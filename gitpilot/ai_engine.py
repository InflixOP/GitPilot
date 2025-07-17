import json
import os
from typing import Dict, Optional

import google.generativeai as genai
from groq import Groq

from .logger import GitPilotLogger
from .prompts import CONTEXT_PROMPT


class AIEngine:
    def __init__(self, api_key: Optional[str] = None, groq_api_key: Optional[str] = None):
        self.logger = GitPilotLogger()
        
        # Configure Gemini
        genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.gemini_client = genai
        
        # Configure Groq
        self.groq_client = Groq(api_key=groq_api_key or os.getenv("GROQ_API_KEY"))
        
        # Available models
        self.available_models = {
            "1": {"name": "Gemini 2.0 Flash", "provider": "gemini", "model": "gemini-2.0-flash"},
            "2": {"name": "Llama 3.1 8B Instant", "provider": "groq", "model": "llama-3.1-8b-instant"},
            "3": {"name": "Llama 3.3 70B Versatile", "provider": "groq", "model": "llama-3.3-70b-versatile"},
            "4": {"name": "DeepSeek R1 Distill Llama 70B", "provider": "groq", "model": "deepseek-r1-distill-llama-70b"}
        }

    def get_available_models(self) -> Dict:
        """Return available models for selection"""
        return self.available_models

    def generate_command(self, user_input: str, context: Dict, model_choice: str = "1") -> Dict:
        """Generate Git command using selected model"""
        try:
            model_info = self.available_models.get(model_choice, self.available_models["1"])
            
            if model_info["provider"] == "gemini":
                return self._generate_with_gemini(user_input, context, model_info["model"])
            elif model_info["provider"] == "groq":
                return self._generate_with_groq(user_input, context, model_info["model"])
            else:
                raise ValueError(f"Unknown provider: {model_info['provider']}")
                
        except Exception as e:
            self.logger.log_error(f"AI generation failed: {str(e)}")
            return {
                "command": None,
                "explanation": f"Failed to generate command: {str(e)}",
                "warning": "Please try again or use manual Git commands"
            }

    def _generate_with_gemini(self, user_input: str, context: Dict, model_name: str) -> Dict:
        """Generate command using Gemini API"""
        prompt = self._build_prompt(user_input, context)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        self.logger.log_ai_query(user_input, response_text, "gemini")
        return self._parse_ai_response(response_text)

    def _generate_with_groq(self, user_input: str, context: Dict, model_name: str) -> Dict:
        """Generate command using Groq API"""
        prompt = self._build_prompt(user_input, context)
        
        response = self.groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are GitPilot, an AI assistant that converts natural language to Git commands. Always respond with a JSON object containing 'command', 'explanation', and optionally 'warning' fields. The command should be a valid Git command or null if no command can be generated."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        response_text = response.choices[0].message.content or ""
        self.logger.log_ai_query(user_input, response_text, f"groq-{model_name}")
        return self._parse_ai_response(response_text)

    def _build_prompt(self, user_input: str, context: Dict) -> str:
        """Build prompt for AI model"""
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
        """Format context information for the prompt"""
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
            
            # Fallback to text parsing
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
            return {
                "command": None,
                "explanation": response,
                "warning": "Failed to parse AI response"
            }