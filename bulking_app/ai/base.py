"""Provider-agnostic planner contract and shared prompt."""

from typing import Any, Protocol


class Planner(Protocol):
    name: str
    def generate_plan(self, context: dict[str, Any]) -> dict[str, Any]: ...


def planner_prompt(context: dict[str, Any]) -> str:
    return f"""Create a practical one-day muscle-gain plan using the user's information.
Return only a JSON object with keys: summary (string), meals (array of objects with
time, name, ingredients, and protein_g), workout (string), recovery (string), and
assumptions (array of strings). Be conservative, avoid inventing food quantities,
and state when information is missing. This is general wellness guidance, not medical
advice. User check-in: {context!r}"""


def parse_plan(text: str) -> dict[str, Any]:
    import json
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("The AI provider returned an invalid plan format.")
    return value
