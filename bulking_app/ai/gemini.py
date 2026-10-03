"""Google Gemini implementation."""

import os
from typing import Any

from bulking_app.ai.base import parse_plan, planner_prompt


class GeminiPlanner:
    name = "gemini"

    def __init__(self) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("Set GEMINI_API_KEY in your .env file to generate a plan.")
        from google import genai
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def generate_plan(self, context: dict[str, Any]) -> dict[str, Any]:
        response = self.client.models.generate_content(
            model=self.model, contents=planner_prompt(context),
            config={"response_mime_type": "application/json"})
        return parse_plan(response.text or "")
