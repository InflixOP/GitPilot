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
        genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.gemini_client = genai
        self.groq_client = Groq(api_key=groq_api_key or os.getenv("GROQ_API_KEY"))
        self.available_models = {
            "1": {"name": "Gemini 2.0 Flash", "provider": "gemini", "model": "gemini-2.0-flash"},
            "2": {"name": "Llama 3.1 8B Instant", "provider": "groq", "model": "llama-3.1-8b-instant"},
            "3": {"name": "Llama 3.3 70B Versatile", "provider": "groq", "model": "llama-3.3-70b-versatile"},
            "4": {"name": "DeepSeek R1 Distill Llama 70B", "provider": "groq", "model": "deepseek-r1-distill-llama-70b"}
        }
    def get_available_models(self) -> Dict:
        return self.available_models
    def generate_command(self, user_input: str, context: Dict, model_choice: str = "1") -> Dict:
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
        prompt = self._build_prompt(user_input, context)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        self.logger.log_ai_query(user_input, response_text, "gemini")
        return self._parse_ai_response(response_text)
    def _generate_with_groq(self, user_input: str, context: Dict, model_name: str) -> Dict:
        prompt = self._build_prompt(user_input, context)
        response = self.groq_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are GitPilot, an AI assistant that converts natural language to Git commands. CRITICAL: Always respond with ONLY a valid JSON object in this exact format: {\"command\": \"git ...\", \"explanation\": \"...\", \"warning\": \"...\" or null}. The command should be a valid Git command or null if no command can be generated. Do not include any text before or after the JSON object."
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
        import re
        try:
            response_clean = response.strip()
            json_match = re.search(r'{[^}]*"command"[^}]*}', response_clean, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            if response_clean.startswith("{"):
                try:
                    return json.loads(response_clean)
                except json.JSONDecodeError:
                    pass
            lines = response_clean.split("\n")
            command = None
            explanation = ""
            warning = None
            for line in lines:
                line = line.strip()
                if not command:
                    if line.startswith("git "):
                        command = line
                    elif "`git " in line:
                        git_match = re.search(r'`(git [^`]+)`', line)
                        if git_match:
                            command = git_match.group(1)
                    elif line.startswith("```") and "git " in line:
                        git_match = re.search(r'git [^\n]+', line)
                        if git_match:
                            command = git_match.group()
                    elif ":" in line and "git " in line:
                        git_match = re.search(r'git [^\n]+', line)
                        if git_match:
                            command = git_match.group()
                if line.startswith(("Warning:", "Note:", "⚠️", "WARNING:")):
                    warning = line
                elif "warning" in line.lower() and not warning:
                    warning = line
                elif line and not command and not line.startswith(("```", "`", "Warning:", "Note:")):
                    if "git " not in line:
                        explanation += line + " "
            if command:
                command = command.strip().strip('`').strip()
                if not command.startswith("git "):
                    command = "git " + command
            return {
                "command": command,
                "explanation": explanation.strip(),
                "warning": warning
            }
        except Exception as e:
            self.logger.log_error(f"Error parsing AI response: {str(e)}")
            self.logger.log_error(f"Raw response: {response[:200]}...")
            return {
                "command": None,
                "explanation": response,
                "warning": "Failed to parse AI response"
            }

    def resolve_merge_conflict(self, conflict_content: str, context: Dict, model_choice: str = "1") -> Dict:
        """AI-powered merge conflict resolution."""
        try:
            prompt = f"""
You are GitPilot, an expert Git assistant. A merge conflict has occurred. 
Analyze the conflict and provide a resolution strategy.

Conflict content:
```
{conflict_content[:2000]}  # Limit content size
```

Repository context:
{self._format_context(context)}

Provide a JSON response with:
{{
    "resolution_strategy": "detailed explanation of how to resolve",
    "recommended_commands": ["list", "of", "git commands"],
    "explanation": "step by step explanation",
    "auto_resolvable": true/false
}}
"""
            model_info = self.available_models.get(model_choice, self.available_models["1"])
            if model_info["provider"] == "gemini":
                model = genai.GenerativeModel(model_info["model"])
                response = model.generate_content(prompt)
                response_text = response.text if hasattr(response, 'text') else str(response)
            else:
                response = self.groq_client.chat.completions.create(
                    model=model_info["model"],
                    messages=[
                        {"role": "system", "content": "You are GitPilot, an expert Git merge conflict resolver. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1500
                )
                response_text = response.choices[0].message.content or ""
            
            self.logger.log_ai_query(f"Conflict resolution for {len(conflict_content)} chars", response_text, f"{model_info['provider']}-conflict")
            return self._parse_conflict_response(response_text)
        except Exception as e:
            self.logger.log_error(f"Conflict resolution failed: {str(e)}")
            return {
                "resolution_strategy": "Manual resolution required",
                "recommended_commands": ["git status", "git add <resolved-files>", "git commit"],
                "explanation": f"AI resolution failed: {str(e)}. Please resolve manually.",
                "auto_resolvable": False
            }

    def semantic_commit_search(self, search_query: str, commit_history: List[str], model_choice: str = "1") -> Dict:
        """Search commits using natural language."""
        try:
            commits_text = "\n".join(commit_history[:50])  # Limit to recent commits
            prompt = f"""
You are GitPilot. Search through the commit history using natural language.

Search query: "{search_query}"

Commit history:
```
{commits_text}
```

Find commits that match the search intent. Provide a JSON response:
{{
    "matches": [
        {{
            "commit_sha": "abc1234",
            "message": "commit message",
            "relevance_score": 0.95,
            "explanation": "why this matches"
        }}
    ],
    "summary": "brief summary of search results"
}}
"""
            model_info = self.available_models.get(model_choice, self.available_models["1"])
            if model_info["provider"] == "gemini":
                model = genai.GenerativeModel(model_info["model"])
                response = model.generate_content(prompt)
                response_text = response.text if hasattr(response, 'text') else str(response)
            else:
                response = self.groq_client.chat.completions.create(
                    model=model_info["model"],
                    messages=[
                        {"role": "system", "content": "You are GitPilot, a semantic commit search assistant. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                response_text = response.choices[0].message.content or ""
            
            self.logger.log_ai_query(search_query, response_text, f"{model_info['provider']}-search")
            return self._parse_search_response(response_text)
        except Exception as e:
            self.logger.log_error(f"Semantic search failed: {str(e)}")
            return {
                "matches": [],
                "summary": f"Search failed: {str(e)}"
            }

    def analyze_repository_health(self, repo_stats: Dict, model_choice: str = "1") -> Dict:
        """AI-powered repository health analysis."""
        try:
            prompt = f"""
You are GitPilot, a repository health expert. Analyze the repository statistics and provide health recommendations.

Repository statistics:
{json.dumps(repo_stats, indent=2)}

Provide a JSON response:
{{
    "overall_health": "excellent|good|fair|poor",
    "health_score": 85,
    "issues": [
        {{
            "type": "large_files|security|performance|maintenance",
            "severity": "high|medium|low",
            "description": "issue description",
            "recommendation": "how to fix"
        }}
    ],
    "recommendations": ["list of general recommendations"],
    "summary": "brief health summary"
}}
"""
            model_info = self.available_models.get(model_choice, self.available_models["1"])
            if model_info["provider"] == "gemini":
                model = genai.GenerativeModel(model_info["model"])
                response = model.generate_content(prompt)
                response_text = response.text if hasattr(response, 'text') else str(response)
            else:
                response = self.groq_client.chat.completions.create(
                    model=model_info["model"],
                    messages=[
                        {"role": "system", "content": "You are GitPilot, a repository health analyst. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1200
                )
                response_text = response.choices[0].message.content or ""
            
            self.logger.log_ai_query("Repository health analysis", response_text, f"{model_info['provider']}-health")
            return self._parse_health_response(response_text)
        except Exception as e:
            self.logger.log_error(f"Health analysis failed: {str(e)}")
            return {
                "overall_health": "unknown",
                "health_score": 0,
                "issues": [],
                "recommendations": [],
                "summary": f"Analysis failed: {str(e)}"
            }

    def _parse_conflict_response(self, response: str) -> Dict:
        """Parse conflict resolution response."""
        try:
            import re
            json_match = re.search(r'{.*}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {
                "resolution_strategy": response,
                "recommended_commands": [],
                "explanation": "Manual parsing of AI response",
                "auto_resolvable": False
            }
        except:
            return {
                "resolution_strategy": "Manual resolution required",
                "recommended_commands": [],
                "explanation": "Failed to parse conflict resolution",
                "auto_resolvable": False
            }

    def _parse_search_response(self, response: str) -> Dict:
        """Parse semantic search response."""
        try:
            import re
            json_match = re.search(r'{.*}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {
                "matches": [],
                "summary": "No matches found"
            }
        except:
            return {
                "matches": [],
                "summary": "Failed to parse search results"
            }

    def _parse_health_response(self, response: str) -> Dict:
        """Parse health analysis response."""
        try:
            import re
            json_match = re.search(r'{.*}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {
                "overall_health": "unknown",
                "health_score": 0,
                "issues": [],
                "recommendations": [],
                "summary": "Failed to parse health analysis"
            }
        except:
            return {
                "overall_health": "unknown",
                "health_score": 0,
                "issues": [],
                "recommendations": [],
                "summary": "Failed to parse health analysis"
            }
