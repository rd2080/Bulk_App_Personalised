"""Repository for the food_inventory PostgreSQL table."""

from __future__ import annotations

from typing import Any

from bulking_app.neon import connection

ALLOWED_AVAILABILITY_TYPES = ("always_available", "stock_tracked", "on_demand")


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row[0],
        "food_name": row[1],
        "availability_type": row[2],
        "quantity": row[3],
        "unit": row[4],
        "is_available": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }


def list_foods(*, include_unavailable: bool = True) -> list[dict[str, Any]]:
    sql = """
        SELECT id, food_name, availability_type, quantity, unit,
               is_available, created_at, updated_at
        FROM food_inventory
    """
    if not include_unavailable:
        sql += " WHERE is_available = TRUE"
    sql += " ORDER BY is_available DESC, food_name ASC, id ASC"
    with connection() as conn:
        rows = conn.execute(sql).fetchall()
    return [_row_to_dict(row) for row in rows]


def add_food(*, food_name: str, availability_type: str,
             quantity: float | None, unit: str | None) -> int:
    name = food_name.strip()
    if not name:
        raise ValueError("Food name is required.")
    if availability_type not in ALLOWED_AVAILABILITY_TYPES:
        raise ValueError("Invalid availability type.")
    if quantity is not None and quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    with connection() as conn:
        duplicate = conn.execute(
            "SELECT id FROM food_inventory WHERE LOWER(food_name) = LOWER(%s) LIMIT 1",
            (name,),
        ).fetchone()
        if duplicate:
            raise ValueError(f"'{name}' already exists in the inventory.")
        row = conn.execute(
            """
            INSERT INTO food_inventory (food_name, availability_type, quantity, unit)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (name, availability_type, quantity, unit.strip() if unit else None),
        ).fetchone()
    return int(row[0])


def update_food(*, food_id: int, food_name: str, availability_type: str,
                quantity: float | None, unit: str | None) -> None:
    name = food_name.strip()
    if not name:
        raise ValueError("Food name is required.")
    if availability_type not in ALLOWED_AVAILABILITY_TYPES:
        raise ValueError("Invalid availability type.")
    if quantity is not None and quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    with connection() as conn:
        duplicate = conn.execute(
            """
            SELECT id FROM food_inventory
            WHERE LOWER(food_name) = LOWER(%s) AND id <> %s
            LIMIT 1
            """,
            (name, food_id),
        ).fetchone()
        if duplicate:
            raise ValueError(f"'{name}' already exists in the inventory.")
        result = conn.execute(
            """
            UPDATE food_inventory
            SET food_name = %s, availability_type = %s, quantity = %s,
                unit = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (name, availability_type, quantity, unit.strip() if unit else None, food_id),
        )
        if result.rowcount != 1:
            raise ValueError("Food item was not found.")


def set_food_availability(*, food_id: int, is_available: bool) -> None:
    with connection() as conn:
        result = conn.execute(
            """
            UPDATE food_inventory
            SET is_available = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (is_available, food_id),
        )
        if result.rowcount != 1:
            raise ValueError("Food item was not found.")
