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
        return {"operations": [_operation("remove", target)], "clarification": None}

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
        return {"operations": [_operation("replace", target, content)], "clarification": None}

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
        return {"operations": [_operation("add", target, content)], "clarification": None}

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
    if parsed.get("clarification"):
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

    # Validate all proposed values before any write so a later invalid item cannot
    # leave a multi-meal plan only partially updated.
    for operation, existing in resolved:
        action = operation["action"]
        target = operation["meal_type"]
        content_value = operation["content"]
        if action != "remove":
            proposed_name = content_value
            if action == "add" and existing:
                proposed_name = f"{existing['meal_name']} + {content_value}"
            if not proposed_name.strip() or len(proposed_name.strip()) > 160:
                return {
                    "status": "clarification",
                    "message": f"The {target.lower()} description must be between 1 and 160 characters. Shorten it or edit the meal manually.",
                    "changes": [],
                }

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


# ---------------------------------------------------------------------------
# "I ate ..." commands: parsing only (no database access, no guessing).
# ---------------------------------------------------------------------------
_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "half": 0.5,
}
_UNIT_ALIASES = {
    "g": "g", "gm": "g", "gram": "g", "grams": "g", "kg": "kg", "ml": "ml", "l": "l",
    "litre": "l", "litres": "l", "liter": "l", "liters": "l",
    "cup": "cup", "cups": "cup", "bowl": "bowl", "bowls": "bowl", "glass": "glass",
    "glasses": "glass", "tbsp": "tbsp", "tsp": "tsp", "scoop": "scoop", "scoops": "scoop",
    "slice": "slice", "slices": "slice", "piece": "piece", "pieces": "piece",
}
_EAT_PREFIX = re.compile(
    r"^(?:please\s+)?(?:i\s+)?(?:just\s+)?(?:have\s+)?(?:ate|eaten|had|have)\s+",
    re.IGNORECASE,
)


def _singular(word: str) -> str:
    word = word.lower()
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("oes") and len(word) > 4:
        return word[:-2]
    if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
        return word[:-1]
    return word


def normalize_food_name(name: str) -> str:
    return " ".join(_singular(w) for w in re.sub(r"[^a-z0-9 ]", " ", name.lower()).split())


def _clarify(message: str) -> dict[str, Any]:
    return {"status": "clarification", "message": message}


def parse_eaten_command(text: str) -> dict[str, Any]:
    """Parse "I ate three eggs" / "had 200 g rice" into name, quantity and unit.

    Returns {"status": "ok", "item_name", "quantity", "unit"} or
    {"status": "clarification", "message"}. A missing amount or food is asked,
    never guessed. A bare count ("three eggs") is counted in "piece".
    """
    source = re.sub(r"\s+", " ", (text or "").strip()).rstrip(".!")
    if not source:
        return _clarify("Type what you ate, for example: I ate three eggs.")
    match = _EAT_PREFIX.match(source)
    if not match:
        return _clarify("I only log commands like 'I ate three eggs' or 'had 200 g rice'.")
    rest = source[match.end():].strip()
    if "," in rest or re.search(r"\s(?:and|with|plus|\+)\s", rest, re.IGNORECASE):
        return _clarify("Please log one food at a time so each amount is clear.")
    digits = re.match(r"(\d+(?:\.\d+)?)\s*([a-z]*)\s*(.*)$", rest, re.IGNORECASE)
    unit: str | None = None
    if digits:
        quantity = float(digits.group(1))
        word, tail = digits.group(2).lower(), digits.group(3)
        if word in _UNIT_ALIASES:
            unit, name = _UNIT_ALIASES[word], tail
        else:
            name = f"{word} {tail}".strip()
    else:
        first, _, tail = rest.partition(" ")
        if first.lower() not in _NUMBER_WORDS:
            return _clarify("How much did you eat? Add an amount, for example 'three eggs' or '200 g rice'.")
        quantity, name = float(_NUMBER_WORDS[first.lower()]), tail
        word, _, tail2 = tail.partition(" ")
        if word.lower() in _UNIT_ALIASES:
            unit, name = _UNIT_ALIASES[word.lower()], tail2
    name = re.sub(r"^of\s+", "", name.strip(), flags=re.IGNORECASE).strip(" ,.;:")
    if not name:
        return _clarify("What did you eat?")
    if quantity <= 0:
        return _clarify("The amount must be greater than zero.")
    return {"status": "ok", "item_name": name, "quantity": quantity, "unit": unit or "piece"}
