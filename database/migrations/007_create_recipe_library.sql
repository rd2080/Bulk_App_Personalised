-- Recipe Library is additive. Existing food_inventory rows and constraints are untouched.
CREATE TABLE IF NOT EXISTS recipe_library (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recipe_name TEXT NOT NULL UNIQUE,
    recipe_type TEXT NOT NULL CHECK (recipe_type IN ('meal', 'snack', 'shake')),
    preference_level TEXT NOT NULL CHECK (preference_level IN ('favorite', 'like', 'neutral', 'dislike', 'never')),
    cooking_complexity TEXT NOT NULL CHECK (cooking_complexity IN ('easy', 'medium', 'hard')),
    total_weight_g NUMERIC(10,2) NOT NULL CHECK (total_weight_g > 0),
    calories_kcal NUMERIC(10,2) NOT NULL CHECK (calories_kcal >= 0),
    protein_g NUMERIC(10,2) NOT NULL CHECK (protein_g >= 0),
    carbohydrates_g NUMERIC(10,2) NOT NULL CHECK (carbohydrates_g >= 0),
    fat_g NUMERIC(10,2) NOT NULL CHECK (fat_g >= 0)
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id INTEGER NOT NULL REFERENCES recipe_library(id) ON DELETE CASCADE,
    food_id INTEGER NOT NULL REFERENCES food_inventory(id) ON DELETE RESTRICT,
    quantity NUMERIC(10,3) NOT NULL CHECK (quantity > 0),
    unit TEXT NOT NULL CHECK (length(btrim(unit)) > 0),
    PRIMARY KEY (recipe_id, food_id)
);

CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_food_id ON recipe_ingredients(food_id);
