"""Persistence for the meal log: what was actually eaten.

Plans never write here; only an explicit logging action does. Unknown nutrition
is stored as NULL (never 0). Deletes are soft (``deleted_at``).
"""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal, InvalidOperation
from typing import Any

from bulking_app.neon import connection

ITEM_TYPES = ("recipe", "food", "free_text")
NUTRITION_SOURCES = ("user_entered", "calculated", "estimate", "unknown")
SOURCES = ("manual", "command")

_COLUMNS = (
    "id, log_date, log_time, item_type, recipe_id, food_id, item_name, quantity, unit, "
    "calories_kcal, protein_g, nutrition_source, plan_meal_id, source, deleted_at, "
    "created_at, updated_at"
)


def _day(value: date | str) -> date:
    return date.fromisoformat(value) if isinstance(value, str) else value


def _clock(value: time | str | None) -> time | None:
    if value is None or value == "":
        return None
    return time.fromisoformat(value) if isinstance(value, str) else value


def _number(value: Any, label: str, *, positive: bool = False) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number.")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{label} must be a number.") from None
    if not number.is_finite() or number < 0 or (positive and number == 0):
        raise ValueError(f"{label} must be {'greater than' if positive else 'at least'} zero.")
    return number


def _clean(*, log_date, log_time, item_type, item_name, quantity, unit, calories_kcal,
           protein_g, nutrition_source, recipe_id, food_id, plan_meal_id, source) -> tuple:
    if item_type not in ITEM_TYPES:
        raise ValueError("Choose a valid item type.")
    if source not in SOURCES:
        raise ValueError("Choose a valid log source.")
    name = (item_name or "").strip()
    if not name or len(name) > 160:
        raise ValueError("Item name is required and must be 160 characters or fewer.")
    unit_clean = (unit or "").strip()
    if not unit_clean or len(unit_clean) > 30:
        raise ValueError("A unit is required (30 characters or fewer).")
    amount = _number(quantity, "Amount", positive=True)
    if amount is None:
        raise ValueError("Amount is required.")
    kcal = _number(calories_kcal, "Calories")
    protein = _number(protein_g, "Protein")
    if kcal is None and protein is None:
        provenance = "unknown"
    else:
        provenance = nutrition_source
        if provenance not in NUTRITION_SOURCES or provenance == "unknown":
            raise ValueError("Say where the nutrition values came from.")
    if recipe_id is not None and item_type != "recipe":
        raise ValueError("A recipe reference needs item type 'recipe'.")
    if food_id is not None and item_type != "food":
        raise ValueError("A food reference needs item type 'food'.")
    return (_day(log_date), _clock(log_time), item_type, recipe_id, food_id, name, amount,
            unit_clean, kcal, protein, provenance, plan_meal_id, source)


def _row(row: tuple) -> dict[str, Any]:
    keys = [c.strip() for c in _COLUMNS.split(",")]
    data = dict(zip(keys, row))
    for key in ("quantity", "calories_kcal", "protein_g"):
        if data[key] is not None:
            data[key] = float(data[key])
    return data


def create_log(*, log_date: date | str, item_type: str, item_name: str, quantity: Any,
               unit: str, log_time: time | str | None = None, calories_kcal: Any = None,
               protein_g: Any = None, nutrition_source: str = "unknown",
               recipe_id: int | None = None, food_id: int | None = None,
               plan_meal_id: int | None = None, source: str = "manual") -> int:
    values = _clean(log_date=log_date, log_time=log_time, item_type=item_type,
                    item_name=item_name, quantity=quantity, unit=unit,
                    calories_kcal=calories_kcal, protein_g=protein_g,
                    nutrition_source=nutrition_source, recipe_id=recipe_id,
                    food_id=food_id, plan_meal_id=plan_meal_id, source=source)
    with connection() as conn:
        row = conn.execute(
            """INSERT INTO meal_logs (log_date, log_time, item_type, recipe_id, food_id,
                   item_name, quantity, unit, calories_kcal, protein_g, nutrition_source,
                   plan_meal_id, source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""", values
        ).fetchone()
    return int(row[0])


def update_log(log_id: int, *, log_date: date | str, item_type: str, item_name: str,
               quantity: Any, unit: str, log_time: time | str | None = None,
               calories_kcal: Any = None, protein_g: Any = None,
               nutrition_source: str = "unknown", recipe_id: int | None = None,
               food_id: int | None = None, plan_meal_id: int | None = None,
               source: str = "manual") -> bool:
    values = _clean(log_date=log_date, log_time=log_time, item_type=item_type,
                    item_name=item_name, quantity=quantity, unit=unit,
                    calories_kcal=calories_kcal, protein_g=protein_g,
                    nutrition_source=nutrition_source, recipe_id=recipe_id,
                    food_id=food_id, plan_meal_id=plan_meal_id, source=source)
    with connection() as conn:
        row = conn.execute(
            """UPDATE meal_logs SET log_date = %s, log_time = %s, item_type = %s,
                   recipe_id = %s, food_id = %s, item_name = %s, quantity = %s, unit = %s,
                   calories_kcal = %s, protein_g = %s, nutrition_source = %s,
                   plan_meal_id = %s, source = %s, updated_at = NOW()
               WHERE id = %s AND deleted_at IS NULL RETURNING id""", (*values, log_id)
        ).fetchone()
    return row is not None


def soft_delete_log(log_id: int) -> bool:
    """Mark a log deleted. Idempotent: an already-deleted log returns False."""
    with connection() as conn:
        row = conn.execute(
            """UPDATE meal_logs SET deleted_at = NOW(), updated_at = NOW()
               WHERE id = %s AND deleted_at IS NULL RETURNING id""", (log_id,)
        ).fetchone()
    return row is not None


def get_log(log_id: int, *, include_deleted: bool = False) -> dict[str, Any] | None:
    sql = f"SELECT {_COLUMNS} FROM meal_logs WHERE id = %s"
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    with connection() as conn:
        row = conn.execute(sql, (log_id,)).fetchone()
    return _row(row) if row else None


def list_logs(log_date: date | str, *, include_deleted: bool = False) -> list[dict[str, Any]]:
    sql = f"SELECT {_COLUMNS} FROM meal_logs WHERE log_date = %s"
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    sql += " ORDER BY log_time NULLS LAST, id"
    with connection() as conn:
        rows = conn.execute(sql, (_day(log_date),)).fetchall()
    return [_row(r) for r in rows]
