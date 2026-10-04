"""Strict CSV validation and atomic recipe/ingredient import."""

from __future__ import annotations

import csv
import io
from decimal import Decimal
from typing import Any

from bulking_app.neon import connection
from bulking_app.repositories.recipe_library import (
    INGREDIENT_HEADERS, RECIPE_FIELDS, RECIPE_HEADERS,
    _decimal, _replace_ingredients, validate_recipe,
)


def _rows(source: Any, expected: tuple[str, ...], label: str) -> list[dict[str, str]]:
    if hasattr(source, "getvalue"):
        source = source.getvalue()
    if isinstance(source, bytes):
        source = source.decode("utf-8-sig")
    if not isinstance(source, str):
        raise ValueError(f"{label} must be uploaded as CSV text.")
    reader = csv.DictReader(io.StringIO(source.lstrip("\ufeff")))
    if tuple(reader.fieldnames or ()) != expected:
        raise ValueError(f"{label} headers must be exactly: {', '.join(expected)}.")
    rows = []
    for line_number, row in enumerate(reader, start=2):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"{label} row {line_number} has the wrong number of columns.")
        if all(not str(value).strip() for value in row.values()):
            continue
        rows.append({key: str(value).strip() for key, value in row.items()})
    if not rows:
        raise ValueError(f"{label} must contain at least one data row.")
    return rows


def parse_and_validate(recipes_csv: Any, ingredients_csv: Any, food_names: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    recipes = _rows(recipes_csv, RECIPE_HEADERS, "recipes.csv")
    ingredients = _rows(ingredients_csv, INGREDIENT_HEADERS, "recipe_ingredients.csv")
    recipe_map: dict[str, dict[str, Any]] = {}
    for line, row in enumerate(recipes, start=2):
        recipe = validate_recipe(row)
        key = recipe["recipe_name"].casefold()
        if key in recipe_map:
            raise ValueError(f"Duplicate recipe name in recipes.csv row {line}: {recipe['recipe_name']}.")
        recipe_map[key] = recipe
    seen: set[tuple[str, str]] = set()
    for line, row in enumerate(ingredients, start=2):
        key = row["recipe_name"].casefold()
        food_key = row["food_name"].casefold()
        if key not in recipe_map:
            raise ValueError(f"recipe_ingredients.csv row {line} references recipe '{row['recipe_name']}' not listed in recipes.csv.")
        if food_key not in {name.casefold() for name in food_names}:
            raise ValueError(f"recipe_ingredients.csv row {line} references unknown food '{row['food_name']}'.")
        if (key, food_key) in seen:
            raise ValueError(f"Duplicate ingredient '{row['food_name']}' for recipe '{row['recipe_name']}'.")
        seen.add((key, food_key))
        _decimal(row["quantity"], "Ingredient quantity", positive=True)
        if not row["unit"]:
            raise ValueError(f"recipe_ingredients.csv row {line} requires a unit.")
    return list(recipe_map.values()), ingredients


def import_recipe_csvs(recipes_csv: Any, ingredients_csv: Any) -> dict[str, int]:
    """Validate all rows first, then upsert recipes and replace their ingredients in one transaction."""
    with connection() as conn:
        foods = conn.execute("SELECT id, food_name FROM food_inventory").fetchall()
        recipes, ingredients = parse_and_validate(recipes_csv, ingredients_csv, {row[1] for row in foods})
        food_ids = {row[1].casefold(): row[0] for row in foods}
        recipe_ids: dict[str, int] = {}
        for recipe in recipes:
            row = conn.execute(
                "INSERT INTO recipe_library (recipe_name, recipe_type, preference_level, cooking_complexity, "
                "total_weight_g, calories_kcal, protein_g, carbohydrates_g, fat_g) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT (recipe_name) DO UPDATE SET recipe_type=EXCLUDED.recipe_type, "
                "preference_level=EXCLUDED.preference_level, cooking_complexity=EXCLUDED.cooking_complexity, "
                "total_weight_g=EXCLUDED.total_weight_g, calories_kcal=EXCLUDED.calories_kcal, "
                "protein_g=EXCLUDED.protein_g, carbohydrates_g=EXCLUDED.carbohydrates_g, fat_g=EXCLUDED.fat_g "
                "RETURNING id", tuple(recipe[k] for k in RECIPE_FIELDS),
            ).fetchone()
            recipe_ids[recipe["recipe_name"].casefold()] = int(row[0])
        grouped: dict[int, list[dict[str, Any]]] = {rid: [] for rid in recipe_ids.values()}
        for item in ingredients:
            rid = recipe_ids[item["recipe_name"].casefold()]
            grouped[rid].append({"food_id": food_ids[item["food_name"].casefold()],
                                 "quantity": Decimal(item["quantity"]), "unit": item["unit"]})
        for rid, values in grouped.items():
            _replace_ingredients(conn, rid, values)
    return {"recipes": len(recipes), "ingredients": len(ingredients)}


def template_csv(kind: str) -> str:
    if kind == "recipes":
        headers = RECIPE_HEADERS
        rows = [("Sev Ki Sabji", "meal", "favorite", "easy", "400", "720", "18", "65", "42")]
    elif kind == "ingredients":
        headers = INGREDIENT_HEADERS
        rows = [("Sev Ki Sabji", "Onion", "100", "g"), ("Sev Ki Sabji", "Tomato", "100", "g")]
    else:
        raise ValueError("Template kind must be 'recipes' or 'ingredients'.")
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()
