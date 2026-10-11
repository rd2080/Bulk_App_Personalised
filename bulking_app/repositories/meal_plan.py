"""Persistence for dated meal plans and their editable meal rows."""

from __future__ import annotations

from datetime import date
from typing import Any

from bulking_app.neon import connection

MEAL_TYPES = ("Breakfast", "Morning snack", "Lunch", "Afternoon snack", "Dinner", "Other")


def _day(value: date | str) -> date:
    return date.fromisoformat(value) if isinstance(value, str) else value


def list_meals(plan_date: date | str) -> list[dict[str, Any]]:
    day = _day(plan_date)
    with connection() as conn:
        rows = conn.execute(
            """SELECT m.id, m.meal_type, m.meal_name, m.description, m.position
               FROM daily_meal_plans p JOIN planned_meals m ON m.plan_id = p.id
               WHERE p.plan_date = %s ORDER BY m.position, m.id""", (day,)
        ).fetchall()
    return [
        {"id": row[0], "meal_type": row[1], "meal_name": row[2],
         "description": row[3] or "", "position": row[4]}
        for row in rows
    ]


def save_meal(*, plan_date: date | str, meal_type: str, meal_name: str,
              description: str = "", meal_id: int | None = None) -> int:
    day = _day(plan_date)
    if meal_type not in MEAL_TYPES:
        raise ValueError("Choose a valid meal type.")
    name = meal_name.strip()
    if not name or len(name) > 160:
        raise ValueError("Meal name is required and must be 160 characters or fewer.")
    detail = description.strip()
    if len(description) > 2000:
        raise ValueError("Meal notes must be 2,000 characters or fewer.")

    with connection() as conn:
        plan = conn.execute(
            """INSERT INTO daily_meal_plans (plan_date) VALUES (%s)
               ON CONFLICT (plan_date) DO UPDATE SET updated_at = NOW()
               RETURNING id""", (day,)
        ).fetchone()
        plan_id = plan[0]
        if meal_id is None:
            position = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM planned_meals WHERE plan_id = %s",
                (plan_id,),
            ).fetchone()[0]
            row = conn.execute(
                """INSERT INTO planned_meals (plan_id, meal_type, meal_name, description, position)
                   VALUES (%s, %s, %s, %s, %s) RETURNING id""",
                (plan_id, meal_type, name, detail, position),
            ).fetchone()
            return int(row[0])

        row = conn.execute(
            """UPDATE planned_meals SET meal_type = %s, meal_name = %s, description = %s
               WHERE id = %s AND plan_id = %s RETURNING id""",
            (meal_type, name, detail, meal_id, plan_id),
        ).fetchone()
        if row is None:
            raise ValueError("That meal was not found in the selected day's plan.")
        return int(row[0])


def delete_meal(*, plan_date: date | str, meal_id: int) -> bool:
    day = _day(plan_date)
    with connection() as conn:
        row = conn.execute(
            """DELETE FROM planned_meals m USING daily_meal_plans p
               WHERE m.plan_id = p.id AND p.plan_date = %s AND m.id = %s
               RETURNING m.id""", (day, meal_id)
        ).fetchone()
    return row is not None
