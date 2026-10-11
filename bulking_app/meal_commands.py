"""Deterministic parsing and application of common meal-plan commands.

This module intentionally has no LLM/provider dependency. It supports a small,
explicit command vocabulary and asks for clarification when the target is unclear.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from bulking_app.repositories.meal_plan import (
    MEAL_TYPES,
    delete_meal,
    list_meals,
    save_meal,
)

_SLOT_ALIASES = {
    "breakfast": "Breakfast",
    "morning snack": "Morning snack",
    "lunch": "Lunch",
    "afternoon snack": "Afternoon snack",
    "evening snack": "Afternoon snack",
    "dinner": "Dinner",
    "other": "Other",
}
_SLOT_PATTERN = re.compile(
    r"(?<!\w)(?:(?:for|at|my)\s+)?"
    r"(morning\s+snack|afternoon\s+snack|evening\s+snack|"
    r"breakfast|lunch|dinner|snack|other)(?!\w)",
    re.IGNORECASE,
)
_LEADING_FILLER = re.compile(
    r"^\s*(?:(?:,|:|\-|then)\s*)?"
    r"(?:(?:i\s+)?(?:will\s+have|am\s+having|plan\s+to\s+have|"
    r"would\s+like|want|will\s+eat|am\s+eating|\x27ll\s+have|"
    r"\x27ll\s+eat|have|is|will\s+be)\s+)?",
    re.IGNORECASE,
)


def _slot(value: str) -> str | None:
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    if normalized == "snack":
        return None
    return _SLOT_ALIASES.get(normalized)


def _clean_content(value: str) -> str:
    value = _LEADING_FILLER.sub("", value.strip())
    value = value.strip(" \t\n,.;:")
    return re.sub(r"\s+", " ", value)


def _operation(action: str, slot_name: str, content: str = "") -> dict[str, str]:
    return {"action": action, "meal_type": slot_name, "content": content}


def parse_meal_commands(text: str) -> dict[str, Any]:
    """Parse supported commands without making database changes."""
    source = re.sub(r"\s+", " ", (text or "").strip())
    if not source:
        return {"operations": [], "clarification": "Please dictate or enter a meal description first."}

    # Explicit single-slot removal.
    remove_match = re.fullmatch(
        r"(?:please\s+)?(?:remove|delete|clear|skip)\s+(?:my\s+)?"
        r"(morning\s+snack|afternoon\s+snack|evening\s+snack|"
        r"breakfast|lunch|dinner|snack|other)(?:\s+meal)?[.!]?",
        source,
        re.IGNORECASE,
    )
    if remove_match:
        target = _slot(remove_match.group(1))
        if target is None:
            return {"operations": [], "clarification": "Which snack do you mean: morning or afternoon?"}
        return {"operations": [_operation("remove", target)]}

    # Explicit replacement/update.
    replace_match = re.fullmatch(
        r"(?:please\s+)?(?:change|replace|update|set)\s+(?:my\s+)?"
        r"(morning\s+snack|afternoon\s+snack|evening\s+snack|"
        r"breakfast|lunch|dinner|snack|other)\s+"
        r"(?:to|with|as)\s+(.+?)[.!]?",
        source,
        re.IGNORECASE,
    )
    if replace_match:
        target = _slot(replace_match.group(1))
        content = _clean_content(replace_match.group(2))
        if target is None:
            return {"operations": [], "clarification": "Which snack do you mean: morning or afternoon?"}
        if not content:
            return {"operations": [], "clarification": "What should I put in that meal?"}
        return {"operations": [_operation("replace", target, content)]}

    # Explicit addition to a slot.
    add_match = re.fullmatch(
        r"(?:please\s+)?add\s+(.+?)\s+to\s+(?:my\s+)?"
        r"(morning\s+snack|afternoon\s+snack|evening\s+snack|"
        r"breakfast|lunch|dinner|snack|other)[.!]?",
        source,
        re.IGNORECASE,
    )
    if add_match:
        content = _clean_content(add_match.group(1))
        target = _slot(add_match.group(2))
        if target is None:
            return {"operations": [], "clarification": "Which snack do you mean: morning or afternoon?"}
        if not content:
            return {"operations": [], "clarification": "What would you like to add?"}
        return {"operations": [_operation("add", target, content)]}

    # Initial day plan / multiple slot declarations, e.g. "Breakfast: eggs.
    # For lunch, three rotis. Dinner will be dal rice."
    matches = list(_SLOT_PATTERN.finditer(source))
    if not matches:
        return {
            "operations": [],
            "clarification": (
                "I couldn't identify a meal slot. Mention breakfast, lunch, dinner, "
                "morning snack, or evening snack."
            ),
        }

    operations: list[dict[str, str]] = []
    seen_slots: set[str] = set()
    for index, match in enumerate(matches):
        target = _slot(match.group(1))
        if target is None:
            return {"operations": [], "clarification": "Which snack do you mean: morning or afternoon?"}
        if target in seen_slots:
            return {
                "operations": [],
                "clarification": f"You mentioned {target.lower()} more than once. Please give one clear instruction for it.",
            }
        seen_slots.add(target)
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        content = _clean_content(source[match.end():next_start])
        if not content:
            return {
                "operations": [],
                "clarification": f"What would you like to plan for {target.lower()}?",
            }
        operations.append(_operation("replace", target, content))

    return {"operations": operations, "clarification": None}


def apply_meal_commands(text: str, plan_date: date) -> dict[str, Any]:
    """Apply parsed commands to the existing plan, asking before ambiguous writes."""
    parsed = parse_meal_commands(text)
    if parsed["clarification"]:
        return {"status": "clarification", "message": parsed["clarification"], "changes": []}

    operations = parsed["operations"]
    if not operations:
        return {"status": "clarification", "message": "No meal changes were identified.", "changes": []}

    current = list_meals(plan_date)
    by_type: dict[str, list[dict[str, Any]]] = {meal_type: [] for meal_type in MEAL_TYPES}
    for meal in current:
        by_type.setdefault(meal["meal_type"], []).append(meal)

    # Resolve every operation before writing anything, so ambiguous commands do not
    # partially update a multi-meal request.
    resolved: list[tuple[dict[str, str], dict[str, Any] | None]] = []
    for operation in operations:
        target = operation["meal_type"]
        matches = by_type.get(target, [])
        if len(matches) > 1:
            return {
                "status": "clarification",
                "message": (
                    f"There are multiple {target.lower()} entries already. "
                    "Please edit the intended entry manually or remove the duplicate first."
                ),
                "changes": [],
            }
        resolved.append((operation, matches[0] if matches else None))

    changes: list[str] = []
    for operation, existing in resolved:
        action = operation["action"]
        target = operation["meal_type"]
        content = operation["content"]

        if action == "remove":
            if existing:
                delete_meal(plan_date=plan_date, meal_id=existing["id"])
                changes.append(f"Removed {target.lower()}.")
            else:
                changes.append(f"No {target.lower()} was saved, so nothing changed.")
            continue

        if action == "add" and existing:
            new_name = f"{existing['meal_name']} + {content}"
            if len(new_name) > 160:
                return {
                    "status": "clarification",
                    "message": f"The {target.lower()} entry is too long to append safely. Replace it with the full meal description instead.",
                    "changes": [],
                }
            save_meal(
                plan_date=plan_date,
                meal_id=existing["id"],
                meal_type=target,
                meal_name=new_name,
                description=existing["description"],
            )
            changes.append(f"Added {content} to {target.lower()}.")
            continue

        if action == "add" and not existing:
            save_meal(plan_date=plan_date, meal_type=target, meal_name=content)
            changes.append(f"Created {target.lower()} with {content}.")
            continue

        if existing:
            save_meal(
                plan_date=plan_date,
                meal_id=existing["id"],
                meal_type=target,
                meal_name=content,
                description="",
            )
            changes.append(f"Updated {target.lower()} to {content}.")
        else:
            save_meal(plan_date=plan_date, meal_type=target, meal_name=content)
            changes.append(f"Added {target.lower()}: {content}.")

    return {"status": "success", "message": "Meal plan updated.", "changes": changes}
