"""Build fresh, structured AI inputs from repository data.

This module only prepares request context. It does not call an AI provider or
generate/save meal plans.
"""

from __future__ import annotations

from typing import Any

from bulking_app.repositories import user_profile

SYSTEM_INSTRUCTION = (
    "You are a helpful personal nutrition planning assistant. Use the supplied "
    "profile as context and do not assume health information that is not provided."
)


def build_profile_request(task: str) -> dict[str, Any]:
    """Read the latest profile and return a structured request envelope."""
    task = task.strip()
    if not task:
        raise ValueError("Task must not be empty.")
    # Repository read happens on every call: no persistent profile copy or cache.
    profile = user_profile.get_user_profile()
    if profile is None:
        raise RuntimeError("Save a user profile before building an AI request.")
    return {
        "system_instruction": SYSTEM_INSTRUCTION,
        "context": {"user_profile": profile},
        "task": task,
        "available_context_sources": [
            "user_profile", "food_preferences", "food_inventory", "morning_checkin",
            "supplements", "workout_profile", "nutrition_data",
        ],
    }
