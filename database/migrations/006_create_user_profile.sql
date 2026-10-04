-- Single-user profile. Exactly the ten agreed data fields are stored.
CREATE TABLE IF NOT EXISTS user_profile (
    age SMALLINT NOT NULL CHECK (age BETWEEN 13 AND 100),
    height_cm NUMERIC(5,1) NOT NULL CHECK (height_cm BETWEEN 100 AND 250),
    target_weight_kg NUMERIC(5,1) NOT NULL CHECK (target_weight_kg BETWEEN 25 AND 350),
    diet_type TEXT NOT NULL CHECK (length(btrim(diet_type)) BETWEEN 1 AND 120),
    diet_philosophy TEXT NOT NULL CHECK (length(btrim(diet_philosophy)) BETWEEN 1 AND 120),
    calorie_strategy TEXT NOT NULL CHECK (length(btrim(calorie_strategy)) BETWEEN 1 AND 120),
    cuisine_preference TEXT NOT NULL CHECK (length(btrim(cuisine_preference)) BETWEEN 1 AND 120),
    regional_context TEXT NOT NULL CHECK (length(btrim(regional_context)) BETWEEN 1 AND 200),
    cooking_complexity TEXT NOT NULL CHECK (length(btrim(cooking_complexity)) BETWEEN 1 AND 120),
    meals_per_day SMALLINT NOT NULL CHECK (meals_per_day BETWEEN 1 AND 10)
);

-- A unique expression index enforces one row without adding an id/key column.
CREATE UNIQUE INDEX IF NOT EXISTS user_profile_single_row_idx ON user_profile ((true));
