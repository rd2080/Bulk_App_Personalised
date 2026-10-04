import unittest
from unittest.mock import patch

from bulking_app.repositories.recipe_library import (
    delete_recipe, nutrition_per_weight, validate_recipe, save_recipe,
)
from bulking_app.services.recipe_csv import import_recipe_csvs, parse_and_validate, template_csv

RECIPE_CSV = (
    "recipe_name,recipe_type,preference_level,cooking_complexity,total_weight_g,calories_kcal,protein_g,carbohydrates_g,fat_g\n"
    "Oats bowl,meal,favorite,easy,400,600,25,80,12\n"
)
INGREDIENT_CSV = "recipe_name,food_name,quantity,unit\nOats bowl,Oats,100,g\n"


class FakeResult:
    rowcount = 1

    def fetchone(self):
        return (17,)


class FakeConnection:
    def __init__(self, foods=()):
        self.foods = foods
        self.sql = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        self.rolled_back = exc_type is not None
        return False

    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        if "SELECT id, food_name FROM food_inventory" in sql:
            return type("Rows", (), {"fetchall": lambda _self: self.foods})()
        return FakeResult()


class RecipeLibraryTests(unittest.TestCase):
    def test_validates_controls_and_numeric_ranges(self):
        row = {"recipe_name": " Oats bowl ", "recipe_type": "meal", "preference_level": "favorite",
               "cooking_complexity": "easy", "total_weight_g": "400", "calories_kcal": "0",
               "protein_g": "25", "carbohydrates_g": "80", "fat_g": "12"}
        self.assertEqual(validate_recipe(row)["recipe_name"], "Oats bowl")
        for field, value in (("recipe_type", "breakfast"), ("preference_level", "love"),
                             ("cooking_complexity", "very_easy"), ("total_weight_g", "0"),
                             ("protein_g", "-1")):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_recipe({**row, field: value})

    def test_calculates_nutrition_per_weight_deterministically(self):
        recipe = {"total_weight_g": 400, "calories_kcal": 600, "protein_g": 25,
                  "carbohydrates_g": 80, "fat_g": 12}
        result = nutrition_per_weight(recipe, 100)
        self.assertEqual(str(result["calories_kcal"]), "150.00")
        self.assertEqual(str(result["protein_g"]), "6.25")

    def test_recipe_and_ingredient_headers_and_example_rows(self):
        self.assertTrue(template_csv("recipes").startswith("recipe_name,recipe_type,preference_level,cooking_complexity"))
        self.assertEqual(template_csv("ingredients").splitlines()[0], "recipe_name,food_name,quantity,unit")
        self.assertEqual(template_csv("ingredients").count("\n"), 3)
        with self.assertRaises(ValueError):
            template_csv("unknown")

    def test_validates_recipe_food_references_and_duplicate_handling(self):
        recipes, ingredients = parse_and_validate(RECIPE_CSV, INGREDIENT_CSV, {"Oats"})
        self.assertEqual(len(recipes), 1)
        self.assertEqual(ingredients[0]["food_name"], "Oats")
        with self.assertRaisesRegex(ValueError, "headers"):
            parse_and_validate("wrong\nvalue\n", INGREDIENT_CSV, {"Oats"})
        with self.assertRaisesRegex(ValueError, "unknown food"):
            parse_and_validate(RECIPE_CSV, INGREDIENT_CSV, {"Rice"})
        duplicate = RECIPE_CSV + RECIPE_CSV.splitlines()[1].replace("Oats bowl", "oats bowl") + "\n"
        with self.assertRaisesRegex(ValueError, "Duplicate recipe"):
            parse_and_validate(duplicate, INGREDIENT_CSV, {"Oats"})

    def test_import_validation_failure_rolls_back_before_writes(self):
        fake = FakeConnection([(1, "Oats")])
        with patch("bulking_app.services.recipe_csv.connection", return_value=fake):
            with self.assertRaisesRegex(ValueError, "unknown food"):
                import_recipe_csvs(RECIPE_CSV, INGREDIENT_CSV.replace(",Oats,", ",No such food,"))
        self.assertTrue(fake.rolled_back)
        self.assertEqual(len(fake.sql), 1)

    def test_crud_write_keeps_recipe_and_ingredient_changes_in_one_transaction(self):
        fake = FakeConnection()
        recipe = {"recipe_name": "Oats", "recipe_type": "meal", "preference_level": "like",
                  "cooking_complexity": "easy", "total_weight_g": 400, "calories_kcal": 600,
                  "protein_g": 20, "carbohydrates_g": 80, "fat_g": 10}
        with patch("bulking_app.repositories.recipe_library.connection", return_value=fake):
            new_id = save_recipe(recipe, [{"food_id": 1, "quantity": 100, "unit": "g"}])
        self.assertEqual(new_id, 17)
        self.assertTrue(any("INSERT INTO recipe_library" in sql for sql, _ in fake.sql))
        self.assertTrue(any("INSERT INTO recipe_ingredients" in sql for sql, _ in fake.sql))

    def test_update_and_delete_crud_operations(self):
        fake_update = FakeConnection()
        recipe = {"recipe_name": "Oats", "recipe_type": "meal", "preference_level": "like",
                  "cooking_complexity": "easy", "total_weight_g": 400, "calories_kcal": 600,
                  "protein_g": 20, "carbohydrates_g": 80, "fat_g": 10}
        with patch("bulking_app.repositories.recipe_library.connection", return_value=fake_update):
            result_id = save_recipe(recipe, [], recipe_id=17)
        self.assertEqual(result_id, 17)
        self.assertTrue(any("UPDATE recipe_library SET" in sql for sql, _ in fake_update.sql))
        self.assertTrue(any("DELETE FROM recipe_ingredients" in sql for sql, _ in fake_update.sql))

        fake_delete = FakeConnection()
        with patch("bulking_app.repositories.recipe_library.connection", return_value=fake_delete):
            delete_recipe(17)
        self.assertTrue(any("DELETE FROM recipe_library" in sql for sql, _ in fake_delete.sql))

    def test_csv_upsert_replaces_recipe_ingredients_transactionally(self):
        fake = FakeConnection([(1, "Oats")])
        with patch("bulking_app.services.recipe_csv.connection", return_value=fake):
            result = import_recipe_csvs(RECIPE_CSV, INGREDIENT_CSV)
        self.assertEqual(result, {"recipes": 1, "ingredients": 1})
        self.assertTrue(any("ON CONFLICT (recipe_name) DO UPDATE" in sql for sql, _ in fake.sql))
        self.assertTrue(any("DELETE FROM recipe_ingredients" in sql for sql, _ in fake.sql))
        self.assertFalse(fake.rolled_back)


if __name__ == "__main__":
    unittest.main()
