"""Read and write the single current user's profile in Neon."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from math import isfinite
from typing import Any, Mapping

from bulking_app.neon import connection

PROFILE_FIELDS = (
    "age", "height_cm", "target_weight_kg", "diet_type", "diet_philosophy",
    "calorie_strategy", "cuisine_preference", "regional_context",
    "cooking_complexity", "meals_per_day",
)
_TEXT_LIMITS = {
    "diet_type": 120, "diet_philosophy": 120, "calorie_strategy": 120,
    "cuisine_preference": 120, "regional_context": 200, "cooking_complexity": 120,
}


def validate_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize all profile fields; reject missing or extra keys."""
    if not isinstance(profile, Mapping):
        raise ValueError("Profile must be a mapping of the ten profile fields.")
    missing = set(PROFILE_FIELDS) - set(profile)
    extra = set(profile) - set(PROFILE_FIELDS)
    if missing or extra:
        details = []
        if missing:
            details.append("missing: " + ", ".join(sorted(missing)))
        if extra:
            details.append("unsupported: " + ", ".join(sorted(extra)))
        raise ValueError("Invalid profile fields (" + "; ".join(details) + ").")

    result: dict[str, Any] = {}
    for field, low, high in (
        ("age", 13, 100), ("meals_per_day", 1, 10),
    ):
        value = profile[field]
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise ValueError(f"{field} must be a whole number between {low} and {high}.")
        result[field] = value

    for field, low, high in (
        ("height_cm", 100, 250), ("target_weight_kg", 25, 350),
    ):
        value = profile[field]
        if isinstance(value, bool):
            raise ValueError(f"{field} must be a number between {low} and {high}.")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{field} must be a number between {low} and {high}.") from exc
        if not isfinite(number) or not low <= number <= high:
            raise ValueError(f"{field} must be a number between {low} and {high}.")
        result[field] = Decimal(str(value))

    for field, limit in _TEXT_LIMITS.items():
        value = profile[field]
        if not isinstance(value, str):
            raise ValueError(f"{field} must be text.")
        value = value.strip()
        if not value or len(value) > limit:
            raise ValueError(f"{field} must contain 1 to {limit} characters.")
        result[field] = value
    return {field: result[field] for field in PROFILE_FIELDS}


def get_user_profile() -> dict[str, Any] | None:
    """Return the current profile row, or None before the first save."""
    columns = ", ".join(PROFILE_FIELDS)
    with connection() as conn:
        row = conn.execute(f"SELECT {columns} FROM user_profile LIMIT 1").fetchone()
    if row is None:
        return None
    return dict(zip(PROFILE_FIELDS, row))


def upsert_user_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and atomically insert or replace the singleton profile row."""
    values = validate_profile(profile)
    columns = ", ".join(PROFILE_FIELDS)
    placeholders = ", ".join(["%s"] * len(PROFILE_FIELDS))
    assignments = ", ".join(f"{field} = EXCLUDED.{field}" for field in PROFILE_FIELDS)
    params = tuple(values[field] for field in PROFILE_FIELDS)
    with connection() as conn:
        # Serialize first writes and updates. The unique constant-expression index
        # in the migration independently guarantees that only one row can exist.
        conn.execute("SELECT pg_advisory_xact_lock(hashtext('user_profile_singleton'))")
        conn.execute(
            f"""INSERT INTO user_profile ({columns}) VALUES ({placeholders})
                ON CONFLICT ((true)) DO UPDATE SET {assignments}""",
            params,
        )
    return values
