"""Logic for the "Log what I ate" page.

Only an explicit call here writes a meal log. Plans are never read or changed.
Unknown nutrition stays None (never 0). A write is reported as saved only after
it is read back from the repository.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from bulking_app.repositories import meal_log

UNKNOWN = "unknown"


class LogWriteError(RuntimeError):
    """A write could not be verified."""


def _num(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def food_entry(food: dict[str, Any], quantity: Any, unit: str) -> dict[str, Any]:
    """Foods in the pantry carry no nutrition, so it is recorded as unknown."""
    return {"item_type": "food", "food_id": food["id"], "item_name": food["food_name"],
            "quantity": quantity, "unit": unit}


def recipe_entry(recipe: dict[str, Any], grams: Any) -> dict[str, Any]:
    """Scale whole-recipe nutrition to the eaten weight; unknown stays unknown."""
    amount, total = _num(grams), _num(recipe.get("total_weight_g"))
    if amount is None or amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    entry: dict[str, Any] = {"item_type": "recipe", "recipe_id": recipe["id"],
                             "item_name": recipe["recipe_name"], "quantity": amount, "unit": "g"}
    kcal, protein = _num(recipe.get("calories_kcal")), _num(recipe.get("protein_g"))
    if total and total > 0 and (kcal is not None or protein is not None):
        ratio = amount / total
        if kcal is not None:
            entry["calories_kcal"] = round(kcal * ratio, 1)
        if protein is not None:
            entry["protein_g"] = round(protein * ratio, 1)
        entry["nutrition_source"] = "calculated"
    return entry


def add_entry(log_date: Any, entry: dict[str, Any], log_time: Any = None) -> dict[str, Any]:
    """Create a log and return it only if it reads back; otherwise raise."""
    new_id = meal_log.create_log(log_date=log_date, log_time=log_time, source="manual", **entry)
    saved = meal_log.get_log(new_id)
    if not saved:
        raise LogWriteError("The entry could not be confirmed as saved. Please check the list.")
    return saved


def edit_entry(log_id: int, log_date: Any, entry: dict[str, Any], log_time: Any = None) -> dict[str, Any]:
    if not meal_log.update_log(log_id, log_date=log_date, log_time=log_time, source="manual", **entry):
        raise LogWriteError("That entry no longer exists, nothing was changed.")
    saved = meal_log.get_log(log_id)
    if not saved:
        raise LogWriteError("The change could not be confirmed. Please check the list.")
    return saved


def remove_entry(log_id: int) -> None:
    if not meal_log.soft_delete_log(log_id):
        raise LogWriteError("That entry was already removed or not found.")
    if meal_log.get_log(log_id) is not None:
        raise LogWriteError("The removal could not be confirmed. Please check the list.")


def format_value(value: Any, suffix: str) -> str:
    return UNKNOWN if value is None else f"{value:g} {suffix}"


def format_quantity(log: dict[str, Any]) -> str:
    return f"{log['quantity']:g} {log['unit']}"


def day_summary(log_date: Any) -> dict[str, Any]:
    """Day's logs with totals of known values only; incomplete if any unknown."""
    logs = meal_log.list_logs(log_date)
    kcal = [x["calories_kcal"] for x in logs if x["calories_kcal"] is not None]
    protein = [x["protein_g"] for x in logs if x["protein_g"] is not None]
    return {
        "logs": logs,
        "known_kcal": sum(kcal) if kcal else None,
        "known_protein_g": sum(protein) if protein else None,
        "incomplete": any(x["calories_kcal"] is None or x["protein_g"] is None for x in logs),
    }
