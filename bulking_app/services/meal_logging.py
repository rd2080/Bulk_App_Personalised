"""Logic for the "Log what I ate" page.

Only an explicit call here writes a meal log. Plans are never read or changed.
Unknown nutrition stays None (never 0). A write is reported as saved only after
it is read back from the repository. Input is validated here, before the
repository is reached.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from bulking_app.meal_commands import normalize_food_name, parse_eaten_command
from bulking_app.repositories import meal_log

RETRY_WINDOW = timedelta(minutes=2)

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


def parse_nutrition(value: Any, label: str) -> Decimal | None:
    """Blank means unknown (None, never 0); anything else must be a number >= 0."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number.")
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError(f"{label} must be a number, or left blank if unknown.") from None
    if not number.is_finite() or number < 0:
        raise ValueError(f"{label} cannot be negative.")
    return number


def with_nutrition(entry: dict[str, Any], kcal: Any, protein: Any) -> dict[str, Any]:
    """Apply owner-entered nutrition; blank values leave the entry unknown."""
    k, p = parse_nutrition(kcal, "Calories"), parse_nutrition(protein, "Protein")
    if k is None and p is None:
        return entry
    return {**entry, "calories_kcal": k, "protein_g": p, "nutrition_source": "user_entered"}


def validate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Check name, quantity, unit and nutrition before anything reaches the repository."""
    name = str(entry.get("item_name") or "").strip()
    if not name:
        raise ValueError("Enter what you ate.")
    if len(name) > 160:
        raise ValueError("The name must be 160 characters or fewer.")
    unit = str(entry.get("unit") or "").strip()
    if not unit:
        raise ValueError("Enter a unit (for example g or piece).")
    qty = _num(entry.get("quantity"))
    if qty is None or not qty.is_finite() or qty <= 0:
        raise ValueError("Amount must be greater than zero.")
    k = parse_nutrition(entry.get("calories_kcal"), "Calories")
    p = parse_nutrition(entry.get("protein_g"), "Protein")
    clean = {**entry, "item_name": name, "unit": unit, "quantity": qty,
             "calories_kcal": k, "protein_g": p}
    if k is None and p is None:
        clean["nutrition_source"] = "unknown"
    return clean


def food_entry(food: dict[str, Any], quantity: Any, unit: str,
               kcal: Any = None, protein: Any = None) -> dict[str, Any]:
    """Pantry foods carry no nutrition (unknown) unless the owner enters it."""
    entry = {"item_type": "food", "food_id": food["id"], "item_name": food["food_name"],
             "quantity": quantity, "unit": unit}
    return with_nutrition(entry, kcal, protein)


def free_text_entry(name: str, quantity: Any, unit: str,
                    kcal: Any = None, protein: Any = None) -> dict[str, Any]:
    entry = {"item_type": "free_text", "item_name": name, "quantity": quantity, "unit": unit}
    return with_nutrition(entry, kcal, protein)


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


def edited_entry(log: dict[str, Any], name: str, quantity: Any, unit: str,
                 kcal: Any, protein: Any) -> dict[str, Any]:
    """Build an update, keeping the nutrition source label true."""
    entry = {"item_type": log["item_type"], "recipe_id": log["recipe_id"],
             "food_id": log["food_id"], "plan_meal_id": log["plan_meal_id"],
             "item_name": name, "quantity": quantity, "unit": unit,
             "calories_kcal": kcal, "protein_g": protein,
             "nutrition_source": log["nutrition_source"]}
    k, p = parse_nutrition(kcal, "Calories"), parse_nutrition(protein, "Protein")
    typed = (None if k is None else float(k), None if p is None else float(p))
    if typed != (log["calories_kcal"], log["protein_g"]):
        entry["nutrition_source"] = "user_entered"
    elif log["nutrition_source"] == "calculated":
        new_q, old_q = _num(quantity), _num(log["quantity"])
        same_unit = str(unit).strip() == log["unit"]
        if new_q is not None and old_q and new_q > 0 and (new_q != old_q or not same_unit):
            if same_unit:
                ratio = new_q / old_q
                entry["calories_kcal"] = None if k is None else round(k * ratio, 1)
                entry["protein_g"] = None if p is None else round(p * ratio, 1)
            else:
                entry["nutrition_source"] = "estimate"
    return entry


def add_entry(log_date: Any, entry: dict[str, Any], log_time: Any = None,
              source: str = "manual") -> dict[str, Any]:
    """Create a log and return it only if it reads back; otherwise raise."""
    entry = validate_entry(entry)
    try:
        new_id = meal_log.create_log(log_date=log_date, log_time=log_time, source=source, **entry)
        saved = meal_log.get_log(new_id)
    except ValueError as exc:
        raise LogWriteError(str(exc)) from exc
    except Exception as exc:  # database or connection problem
        raise LogWriteError("Could not save right now. Nothing was recorded.") from exc
    if not saved:
        raise LogWriteError("The entry could not be confirmed as saved. Please check the list.")
    return saved


def edit_entry(log_id: int, log_date: Any, entry: dict[str, Any], log_time: Any = None) -> dict[str, Any]:
    entry = validate_entry(entry)
    try:
        updated = meal_log.update_log(log_id, log_date=log_date, log_time=log_time,
                                      source="manual", **entry)
        saved = meal_log.get_log(log_id) if updated else None
    except ValueError as exc:
        raise LogWriteError(str(exc)) from exc
    except Exception as exc:
        raise LogWriteError("Could not save right now. Nothing was changed.") from exc
    if not updated:
        raise LogWriteError("That entry no longer exists, nothing was changed.")
    if not saved:
        raise LogWriteError("The change could not be confirmed. Please check the list.")
    return saved


def remove_entry(log_id: int) -> None:
    try:
        deleted = meal_log.soft_delete_log(log_id)
        still_there = meal_log.get_log(log_id) is not None if deleted else False
    except Exception as exc:
        raise LogWriteError("Could not remove right now. Nothing was changed.") from exc
    if not deleted:
        raise LogWriteError("That entry was already removed or not found.")
    if still_there:
        raise LogWriteError("The removal could not be confirmed. Please check the list.")


def _is_retry(existing: dict[str, Any], entry: dict[str, Any], now: datetime) -> bool:
    """Same command-sourced item logged moments ago: a retry, not a new meal."""
    created = existing.get("created_at")
    if existing.get("source") != "command" or not isinstance(created, datetime):
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    same = (normalize_food_name(existing["item_name"]) == normalize_food_name(entry["item_name"])
            and existing["unit"] == entry["unit"]
            and Decimal(str(existing["quantity"])) == Decimal(str(entry["quantity"])))
    return same and timedelta(0) <= now - created <= RETRY_WINDOW


def log_from_command(text: str, log_date: Any, foods: list[dict[str, Any]], *,
                     allow_free_text: bool = False, now: datetime | None = None) -> dict[str, Any]:
    """Log "I ate three eggs". Deterministic; asks instead of guessing.

    Status: "logged", "duplicate" (a retry within RETRY_WINDOW, nothing written) or
    "clarification". Nutrition stays unknown. Pantry stock is never changed here, so a
    retry cannot deduct inventory. Set allow_free_text to log a food not in the pantry.
    """
    parsed = parse_eaten_command(text)
    if parsed["status"] != "ok":
        return parsed
    wanted = normalize_food_name(parsed["item_name"])
    matches = [f for f in foods if normalize_food_name(f["food_name"]) == wanted]
    if len(matches) > 1:
        return {"status": "clarification",
                "message": f"More than one food matches '{parsed['item_name']}'. Log it from the list."}
    if matches:
        entry = food_entry(matches[0], parsed["quantity"], parsed["unit"])
    elif allow_free_text:
        entry = free_text_entry(parsed["item_name"], parsed["quantity"], parsed["unit"])
    else:
        return {"status": "clarification",
                "message": f"'{parsed['item_name']}' is not in your foods. Confirm to log it as typed."}
    try:
        entry = validate_entry(entry)
    except ValueError as exc:
        return {"status": "clarification", "message": str(exc)}
    now = now or datetime.now(timezone.utc)
    try:
        existing = meal_log.list_logs(log_date)
    except Exception as exc:
        raise LogWriteError("Could not check today's log. Nothing was recorded.") from exc
    for log in existing:
        if _is_retry(log, entry, now):
            return {"status": "duplicate", "log": log,
                    "message": "Already logged a moment ago, so I did not add it again."}
    saved = add_entry(log_date, entry, source="command")
    return {"status": "logged", "log": saved,
            "message": "Logged. Nutrition is unknown until you add it."}


def undo_last_command(log_date: Any) -> dict[str, Any] | None:
    """Soft-delete the newest command-logged entry of the day."""
    commands = [x for x in meal_log.list_logs(log_date) if x["source"] == "command"]
    if not commands:
        return None
    target = max(commands, key=lambda x: x["id"])
    remove_entry(target["id"])
    return target


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
