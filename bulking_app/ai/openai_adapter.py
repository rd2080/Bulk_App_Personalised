"""OpenAI implementation for more complex reasoning tasks."""

import os
from typing import Any

from bulking_app.ai.base import parse_plan, planner_prompt


class OpenAIPlanner:
    name = "openai"

    def __init__(self) -> None:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY in your .env file to use OpenAI.")
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    def generate_plan(self, context: dict[str, Any]) -> dict[str, Any]:
        response = self.client.responses.create(
            model=self.model,
            input=planner_prompt(context),
            text={"format": {"type": "json_object"}},
        )
        return parse_plan(response.output_text)
