"""Repository for objective daily morning check-ins."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from bulking_app.neon import connection


def _validate(*, weight_kg: float, sleep_hours: float, soreness_level: int) -> None:
    if not 25 <= float(weight_kg) <= 350:
        raise ValueError("Weight must be between 25 and 350 kg.")
    if not 0 <= float(sleep_hours) <= 24:
        raise ValueError("Sleep hours must be between 0 and 24.")
    if not 1 <= int(soreness_level) <= 10:
        raise ValueError("Soreness must be between 1 and 10.")


def save_morning_checkin(*, checkin_date: date | str, weight_kg: float,
                         sleep_hours: float, soreness_level: int,
                         daily_notes: str = "") -> int:
    """Upsert one day's check-in and matching weight entry atomically."""
    day = date.fromisoformat(str(checkin_date)) if isinstance(checkin_date, str) else checkin_date
    _validate(weight_kg=weight_kg, sleep_hours=sleep_hours, soreness_level=soreness_level)
    notes = daily_notes.strip() or None
    with connection() as conn:
        checkin_row = conn.execute(
            """INSERT INTO daily_checkins
                   (checkin_date, weight_kg, sleep_hours, soreness_level, daily_notes)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (checkin_date) DO UPDATE SET
                   weight_kg = EXCLUDED.weight_kg,
                   sleep_hours = EXCLUDED.sleep_hours,
                   soreness_level = EXCLUDED.soreness_level,
                   daily_notes = EXCLUDED.daily_notes
            RETURNING id""",
            (day, Decimal(str(weight_kg)), Decimal(str(sleep_hours)), int(soreness_level), notes),
        ).fetchone()
        conn.execute(
            """INSERT INTO weight_entries (entry_date, weight_kg)
               VALUES (%s, %s)
               ON CONFLICT (entry_date) DO UPDATE SET weight_kg = EXCLUDED.weight_kg""",
            (day, Decimal(str(weight_kg))),
        )
        return int(checkin_row[0])


def get_morning_checkin(checkin_date: date | str) -> dict[str, Any] | None:
    day = date.fromisoformat(str(checkin_date)) if isinstance(checkin_date, str) else checkin_date
    with connection() as conn:
        row = conn.execute(
            """SELECT checkin_date, weight_kg, sleep_hours, soreness_level, daily_notes
               FROM daily_checkins WHERE checkin_date = %s""", (day,)
        ).fetchone()
    if row is None:
        return None
    return {
        "checkin_date": row[0], "weight_kg": row[1], "sleep_hours": row[2],
        "soreness_level": row[3], "daily_notes": row[4] or "",
    }


def recent_morning_checkins(limit: int = 7) -> list[dict[str, Any]]:
    if not 1 <= int(limit) <= 100:
        raise ValueError("Limit must be between 1 and 100.")
    with connection() as conn:
        rows = conn.execute(
            """SELECT checkin_date, weight_kg, sleep_hours, soreness_level, daily_notes
               FROM daily_checkins ORDER BY checkin_date DESC LIMIT %s""", (int(limit),)
        ).fetchall()
    return [
        {"checkin_date": row[0], "weight_kg": row[1], "sleep_hours": row[2],
         "soreness_level": row[3], "daily_notes": row[4] or ""}
        for row in rows
    ]
