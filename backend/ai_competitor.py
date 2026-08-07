"""
AI Competitor — spawns Hermes subagents to compete in coding battles.
Each agent gets the problem, writes code, submits it to the arena.
"""

import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Optional


class AICompetitor:
    """Spawns AI agents to solve coding problems and submit to the arena."""

    def __init__(self, api_base: str = "http://localhost:8420"):
        self.api_base = api_base
        self.active_competitions: dict[str, asyncio.Task] = {}

    def _call_agent(self, agent_name: str, problem: str, test_cases: list[dict]) -> str:
        """
        Call Hermes to generate code for a problem.
        Uses the terminal to run `hermes chat -q` for code generation.
        Returns the generated code string.
        """
        test_case_str = "\n".join(
            f"  {tc['name']}: input={tc['input']} → expected={tc['expected']}"
            for tc in test_cases
        )

        prompt = f"""You are {agent_name}, competing in a coding battle.

PROBLEM:
{problem}

TEST CASES:
{test_case_str}

RULES:
- Write ONLY valid Python code — no explanations, no markdown
- Must define a function that solves the problem
- The function will be called with test inputs directly
- Output ONLY the code block, nothing else

Your code:"""

        try:
            result = subprocess.run(
                ["hermes", "chat", "-q", prompt],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(Path.home()),
            )
            output = result.stdout.strip()

            # Extract code from the response
            code = self._extract_code(output)
            return code if code else output

        except subprocess.TimeoutExpired:
            return "def solution(x):\n    pass  # timeout"
        except Exception as e:
            return f"# Error: {e}\ndef solution(x):\n    pass"

    def call_agent_via_api(
        self, agent_name: str, model: str, problem: str, test_cases: list[dict]
    ) -> str:
        """
        Call the configured LLM API for code generation.
        Auto-detects DeepSeek, OpenAI, or any OpenAI-compatible provider.
        Falls back to local Hermes if no API key.
        """
        from api_resolver import get_api_config, call_llm

        config = get_api_config()
        if not config["api_key"]:
            return self._call_agent(agent_name, problem, test_cases)

        test_case_str = "\n".join(
            f"  {tc['name']}: input={tc['input']} → expected={tc['expected']}"
            for tc in test_cases
        )

        system_prompt = f"""You are {agent_name}, competing in a coding battle.
Write ONLY valid Python code. No explanations, no markdown.
The code must define a callable function that solves the problem.
Output nothing but the code."""

        user_prompt = f"""PROBLEM:
{problem}

TEST CASES (your code must pass these):
{test_case_str}

Output ONLY the Python code:"""

        try:
            output = call_llm(system_prompt, user_prompt, temperature=0.1, max_tokens=2000, model_override=model)
            code = self._extract_code(output)
            return code if code else output
        except Exception as e:
            print(f"⚠️ LLM call failed ({e}), falling back to local Hermes")
            return self._call_agent(agent_name, problem, test_cases)

    def _extract_code(self, text: str) -> str:
        """Extract Python code from LLM output, removing markdown fences."""
        # Try to extract from ```python blocks
        if "```python" in text:
            parts = text.split("```python", 1)
            if len(parts) > 1:
                code_block = parts[1].split("```", 1)[0]
                return code_block.strip()
        if "```" in text:
            parts = text.split("```", 1)
            if len(parts) > 1:
                code_block = parts[1].split("```", 1)[0]
                return code_block.strip()

        # Remove common prefixes
        lines = text.strip().split("\n")
        code_lines = []
        in_code = False
        for line in lines:
            if line.strip().startswith("def ") or line.strip().startswith("class "):
                in_code = True
            if in_code:
                code_lines.append(line)

        if code_lines:
            return "\n".join(code_lines)

        return text.strip()

    def start_competition(
        self,
        tournament_id: str,
        match_id: str,
        player1: str,
        player2: str,
        problem: str,
        test_cases: list[dict],
        model1: str = "gpt-4o",
        model2: str = "gpt-4o",
    ):
        """
        Start an AI-vs-AI competition for a tournament match.
        Spawns both agents concurrently. They submit to the API.
        """
        import threading

        def compete():
            import urllib.request

            def post(path, body):
                data = json.dumps(body).encode()
                req = urllib.request.Request(
                    f"{self.api_base}{path}",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                return urllib.request.urlopen(req, timeout=30)

            # Agent 1
            try:
                code1 = self.call_agent_via_api(player1, model1, problem, test_cases)
                post("/api/tournaments/submit", {
                    "tournament_id": tournament_id,
                    "match_id": match_id,
                    "agent_name": player1,
                    "code": code1,
                })
                print(f"🤖 {player1} submitted ({len(code1)} chars)")
            except Exception as e:
                print(f"❌ {player1} failed: {e}")

            # Agent 2
            try:
                code2 = self.call_agent_via_api(player2, model2, problem, test_cases)
                post("/api/tournaments/submit", {
                    "tournament_id": tournament_id,
                    "match_id": match_id,
                    "agent_name": player2,
                    "code": code2,
                })
                print(f"🤖 {player2} submitted ({len(code2)} chars)")
            except Exception as e:
                print(f"❌ {player2} failed: {e}")

        thread = threading.Thread(target=compete, daemon=True)
        thread.start()
        return thread


# Singleton
ai_competitor = AICompetitor()
