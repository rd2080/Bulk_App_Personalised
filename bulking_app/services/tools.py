"""Validated Python operations used by the UI and AI workflow."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from bulking_app.database import connection


def validate_check_in(weight_kg: float, feeling: str, foods: list[dict[str, str]]) -> None:
    if not 25 <= float(weight_kg) <= 350:
        raise ValueError("Weight must be between 25 and 350 kg.")
    if not feeling.strip():
        raise ValueError("Describe how you feel before generating a plan.")
    if not any(item.get("name", "").strip() for item in foods):
        raise ValueError("Add at least one available food.")


def get_profile(path: str | None = None) -> dict[str, Any]:
    with connection(path) as conn:
        return dict(conn.execute("SELECT * FROM profile WHERE id = 1").fetchone())


def save_profile(name: str, goal: str, dietary_notes: str, path: str | None = None) -> None:
    with connection(path) as conn:
        conn.execute("""UPDATE profile SET name=?, goal=?, dietary_notes=?, updated_at=CURRENT_TIMESTAMP
                     WHERE id=1""", (name.strip(), goal.strip(), dietary_notes.strip()))


def save_daily_plan(*, weight_kg: float, feeling: str, foods: list[dict[str, str]],
                    notes: str, plan: dict[str, Any], provider: str,
                    entry_date: date | str | None = None, path: str | None = None) -> int:
    day = str(entry_date or date.today())
    validate_check_in(weight_kg, feeling, foods)
    check_in = {"weight_kg": float(weight_kg), "feeling": feeling.strip(),
                "foods": foods, "notes": notes.strip()}
    with connection(path) as conn:
        conn.execute("""INSERT INTO weight_entries(entry_date, weight_kg) VALUES (?, ?)
                     ON CONFLICT(entry_date) DO UPDATE SET weight_kg=excluded.weight_kg""",
                     (day, float(weight_kg)))
        conn.execute("DELETE FROM foods WHERE entry_date=?", (day,))
        conn.executemany("INSERT INTO foods(name, quantity, entry_date) VALUES (?, ?, ?)",
                         [(x["name"].strip(), x.get("quantity", "").strip(), day)
                          for x in foods if x.get("name", "").strip()])
        cursor = conn.execute("""INSERT INTO daily_plans(plan_date, check_in, plan_json, provider)
            VALUES (?, ?, ?, ?) ON CONFLICT(plan_date) DO UPDATE SET check_in=excluded.check_in,
            plan_json=excluded.plan_json, provider=excluded.provider RETURNING id""",
            (day, json.dumps(check_in), json.dumps(plan, ensure_ascii=False), provider))
        plan_id = int(cursor.fetchone()[0])
        conn.execute("INSERT INTO logs(log_date, event_type, details) VALUES (?, ?, ?)",
                     (day, "plan_saved", f"Saved daily plan #{plan_id} using {provider}"))
        return plan_id


def recent_plans(limit: int = 7, path: str | None = None) -> list[dict[str, Any]]:
    with connection(path) as conn:
        rows = conn.execute("SELECT plan_date, plan_json, provider FROM daily_plans "
                            "ORDER BY plan_date DESC LIMIT ?", (limit,)).fetchall()
    result = []
    for row in rows:
        result.append({"plan_date": row["plan_date"], "provider": row["provider"],
                       "plan": json.loads(row["plan_json"])})
    return result
