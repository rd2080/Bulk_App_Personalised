# Recipe Library

## Purpose and scope

The Recipe Library extends the Food Inventory page while leaving inventory availability behavior unchanged. Recipes capture whole-recipe nutrition and weight, preference, complexity, and their ingredients. Ingredients reference existing `food_inventory` entries; they have no nutrition fields. No AI meal generation, meal logging, supplements, workout integration, or analytics are included.

## Controlled values and constraints

- `recipe_type`: `meal`, `snack`, `shake`
- `preference_level`: `favorite`, `like`, `neutral`, `dislike`, `never`
- `cooking_complexity`: `easy`, `medium`, `hard`
- `total_weight_g` and ingredient `quantity`: greater than zero
- Recipe calories, protein, carbohydrates, and fat: zero or greater
- Recipe name: unique; each food appears once per recipe; units are required

## CSV files

Upload both files together. Headers are exact and in the order shown.

`recipes.csv` has one row per recipe:

```csv
recipe_name,recipe_type,preference_level,cooking_complexity,total_weight_g,calories_kcal,protein_g,carbohydrates_g,fat_g
Sev Ki Sabji,meal,favorite,easy,400,720,18,65,42
```

`recipe_ingredients.csv` has one row per ingredient:

```csv
recipe_name,food_name,quantity,unit
Sev Ki Sabji,Onion,100,g
Sev Ki Sabji,Tomato,100,g
```

Names in the ingredient file must reference a recipe in the uploaded recipe file and a food already in Food Inventory (case-insensitive matching). Duplicate recipe or recipe-food entries are rejected. Existing recipes are upserted by exact recipe name; their ingredient list is replaced with the uploaded definition. A recipe with no ingredient rows in the CSV is saved with an empty ingredient list. Validation and import run in one transaction so any database error rolls back the entire upload.

The page provides both template downloads, validation and preview, then a separate import confirmation. The backend entry points are `parse_and_validate`, `import_recipe_csvs`, and `template_csv` in `bulking_app/services/recipe_csv.py`.

## Nutrition scaling

For each nutrient, the value for a serving is `recipe_nutrient × serving_weight_g ÷ total_weight_g`. This uses recipe-level nutrition and does not infer nutrition from ingredient quantities.
