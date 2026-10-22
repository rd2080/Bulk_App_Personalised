"""Today's calories and protein eaten (from meal logs only) versus a target.

Plans are never read here. A log with unknown nutrition is counted as an item
but adds nothing to the totals, and the day is marked incomplete.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable, Iterable

from bulking_app.repositories import meal_log


def _nutrient(logs: Iterable[dict[str, Any]], key: str) -> dict[str, Any]:
    total = 0.0
    known = unknown = 0
    for log in logs:
        value = log.get(key)
        if value is None:
            unknown += 1
        else:
            known += 1
            total += float(value)
    return {
        "eaten": round(total, 1) if known else None,
        "known_items": known,
        "unknown_items": unknown,
    }


def _vs_target(eaten: float | None, target: Any) -> dict[str, Any]:
    if target is None or float(target) <= 0:
        return {"target": None, "remaining": None, "percent": None}
    goal = float(target)
    done = eaten or 0.0
    return {
        "target": goal,
        "remaining": round(max(goal - done, 0.0), 1),
        "percent": round(done / goal * 100, 1),
    }


def summarise(logs: list[dict[str, Any]], *, target_kcal: Any = None,
              target_protein_g: Any = None) -> dict[str, Any]:
    """Pure summary of active meal logs. Totals cover known values only."""
    kcal = _nutrient(logs, "calories_kcal")
    protein = _nutrient(logs, "protein_g")
    kcal.update(_vs_target(kcal["eaten"], target_kcal))
    protein.update(_vs_target(protein["eaten"], target_protein_g))
    incomplete = bool(kcal["unknown_items"] or protein["unknown_items"])
    return {
        "item_count": len(logs),
        "calories": kcal,
        "protein": protein,
        "incomplete": incomplete,
        "includes_estimates": any(l.get("nutrition_source") == "estimate" for l in logs),
        "note": (
            "Incomplete: some logged items have unknown nutrition, so totals are "
            "at least this much." if incomplete else None
        ),
    }


def daily_progress(day: date | str, *, target_kcal: Any = None,
                   target_protein_g: Any = None,
                   list_logs: Callable[..., list[dict[str, Any]]] = meal_log.list_logs
                   ) -> dict[str, Any]:
    """Progress for one day from active (not deleted) meal logs only."""
    return summarise(list_logs(day), target_kcal=target_kcal,
                     target_protein_g=target_protein_g)
