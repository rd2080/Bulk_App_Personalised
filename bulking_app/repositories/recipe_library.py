"""Repository and validation for recipes and their food composition."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from bulking_app.neon import connection

RECIPE_TYPES = ("meal", "snack", "shake")
PREFERENCE_LEVELS = ("favorite", "like", "neutral", "dislike", "never")
COOKING_COMPLEXITIES = ("easy", "medium", "hard")
RECIPE_FIELDS = (
    "recipe_name", "recipe_type", "preference_level", "cooking_complexity",
    "total_weight_g", "calories_kcal", "protein_g", "carbohydrates_g", "fat_g",
)
RECIPE_HEADERS = RECIPE_FIELDS
INGREDIENT_HEADERS = ("recipe_name", "food_name", "quantity", "unit")
NUMERIC_FIELDS = ("total_weight_g", "calories_kcal", "protein_g", "carbohydrates_g", "fat_g")


def _decimal(value: Any, field: str, *, positive: bool = False) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field} must be a number.") from None
    if not number.is_finite() or (number <= 0 if positive else number < 0):
        rule = "greater than zero" if positive else "zero or greater"
        raise ValueError(f"{field} must be {rule}.")
    return number


def validate_recipe(data: dict[str, Any]) -> dict[str, Any]:
    name = str(data.get("recipe_name", "")).strip()
    if not name:
        raise ValueError("Recipe name is required.")
    if data.get("recipe_type") not in RECIPE_TYPES:
        raise ValueError(f"Invalid recipe type. Allowed values: {', '.join(RECIPE_TYPES)}.")
    if data.get("preference_level") not in PREFERENCE_LEVELS:
        raise ValueError(f"Invalid preference level. Allowed values: {', '.join(PREFERENCE_LEVELS)}.")
    if data.get("cooking_complexity") not in COOKING_COMPLEXITIES:
        raise ValueError(f"Invalid cooking complexity. Allowed values: {', '.join(COOKING_COMPLEXITIES)}.")
    result = {key: data[key] for key in RECIPE_FIELDS if key in data}
    result["recipe_name"] = name
    for field in NUMERIC_FIELDS:
        result[field] = _decimal(data.get(field), field, positive=field == "total_weight_g")
    return result


def nutrition_per_weight(recipe: dict[str, Any], weight_g: Any) -> dict[str, Decimal]:
    """Scale recipe-level nutrients proportionally to a serving weight."""
    weight = _decimal(weight_g, "Serving weight", positive=True)
    total = _decimal(recipe["total_weight_g"], "total_weight_g", positive=True)
    ratio = weight / total
    return {field: (_decimal(recipe[field], field) * ratio) for field in NUMERIC_FIELDS[1:]}


def list_recipes() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            "SELECT id, recipe_name, recipe_type, preference_level, cooking_complexity, "
            "total_weight_g, calories_kcal, protein_g, carbohydrates_g, fat_g "
            "FROM recipe_library ORDER BY recipe_name, id"
        ).fetchall()
    return [dict(zip(("id", *RECIPE_FIELDS), row)) for row in rows]


def get_recipe(recipe_id: int) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, recipe_name, recipe_type, preference_level, cooking_complexity, "
            "total_weight_g, calories_kcal, protein_g, carbohydrates_g, fat_g "
            "FROM recipe_library WHERE id = %s", (recipe_id,),
        ).fetchone()
        if row is None:
            return None
        ingredients = conn.execute(
            "SELECT ri.food_id, fi.food_name, ri.quantity, ri.unit "
            "FROM recipe_ingredients ri JOIN food_inventory fi ON fi.id = ri.food_id "
            "WHERE ri.recipe_id = %s ORDER BY fi.food_name", (recipe_id,),
        ).fetchall()
    result = dict(zip(("id", *RECIPE_FIELDS), row))
    result["ingredients"] = [dict(zip(("food_id", "food_name", "quantity", "unit"), item)) for item in ingredients]
    return result


def save_recipe(data: dict[str, Any], ingredients: Iterable[dict[str, Any]] = (), recipe_id: int | None = None) -> int:
    recipe = validate_recipe(data)
    ingredient_rows = list(ingredients)
    with connection() as conn:
        if recipe_id is None:
            row = conn.execute(
                "INSERT INTO recipe_library (recipe_name, recipe_type, preference_level, cooking_complexity, "
                "total_weight_g, calories_kcal, protein_g, carbohydrates_g, fat_g) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                tuple(recipe[k] for k in RECIPE_FIELDS),
            ).fetchone()
            recipe_id = int(row[0])
        else:
            result = conn.execute(
                "UPDATE recipe_library SET recipe_name=%s, recipe_type=%s, preference_level=%s, "
                "cooking_complexity=%s, total_weight_g=%s, calories_kcal=%s, protein_g=%s, "
                "carbohydrates_g=%s, fat_g=%s WHERE id=%s",
                (*[recipe[k] for k in RECIPE_FIELDS], recipe_id),
            )
            if result.rowcount != 1:
                raise ValueError("Recipe was not found.")
        _replace_ingredients(conn, recipe_id, ingredient_rows)
    return recipe_id


def _replace_ingredients(conn: Any, recipe_id: int, ingredients: Iterable[dict[str, Any]]) -> None:
    conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = %s", (recipe_id,))
    seen: set[int] = set()
    for item in ingredients:
        food_id = int(item["food_id"])
        if food_id in seen:
            raise ValueError("A food can appear only once in a recipe.")
        seen.add(food_id)
        quantity = _decimal(item.get("quantity"), "Ingredient quantity", positive=True)
        unit = str(item.get("unit", "")).strip()
        if not unit:
            raise ValueError("Ingredient unit is required.")
        conn.execute(
            "INSERT INTO recipe_ingredients (recipe_id, food_id, quantity, unit) VALUES (%s,%s,%s,%s)",
            (recipe_id, food_id, quantity, unit),
        )


def delete_recipe(recipe_id: int) -> None:
    with connection() as conn:
        result = conn.execute("DELETE FROM recipe_library WHERE id = %s", (recipe_id,))
        if result.rowcount != 1:
            raise ValueError("Recipe was not found.")


def list_food_options() -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute("SELECT id, food_name FROM food_inventory ORDER BY LOWER(food_name)").fetchall()
    return [{"id": row[0], "food_name": row[1]} for row in rows]

