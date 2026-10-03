"""Select the configured AI planner."""

from __future__ import annotations

import os

from bulking_app.ai.base import Planner


def get_planner(provider: str | None = None) -> Planner:
    selected = (provider or os.getenv("AI_PROVIDER", "gemini")).strip().lower()
    if selected == "gemini":
        from bulking_app.ai.gemini import GeminiPlanner
        return GeminiPlanner()
    if selected == "openai":
        from bulking_app.ai.openai_adapter import OpenAIPlanner
        return OpenAIPlanner()
    raise ValueError("AI_PROVIDER must be either 'gemini' or 'openai'.")
