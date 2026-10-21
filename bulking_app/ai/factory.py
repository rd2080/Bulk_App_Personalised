"""Select the configured AI planner."""

from __future__ import annotations

import os

from bulking_app.ai.base import Planner


def get_planner(provider: str | None = None, guarded: bool = True) -> Planner:
    planner = _build_planner(provider)
    if not guarded:
        return planner
    from bulking_app.ai.budget import GuardedPlanner
    return GuardedPlanner(planner)


def _build_planner(provider: str | None) -> Planner:
    selected = (provider or os.getenv("AI_PROVIDER", "gemini")).strip().lower()
    if selected == "gemini":
        from bulking_app.ai.gemini import GeminiPlanner
        return GeminiPlanner()
    raise ValueError("AI_PROVIDER must be 'gemini' (the only supported provider).")
