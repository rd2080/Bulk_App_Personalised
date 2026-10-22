-- Meal log (what was actually eaten). Additive: no existing table is altered.
-- Logs stand alone; plan_meal_id is optional and set only when the owner picks a match.
-- Unknown nutrition is stored as NULL, never 0. log_date is the owner's local (UTC+5:30) date.
BEGIN;

CREATE TABLE IF NOT EXISTS meal_logs (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    log_date DATE NOT NULL,
    log_time TIME,
    item_type TEXT NOT NULL CHECK (item_type IN ('recipe', 'food', 'free_text')),
    recipe_id INTEGER REFERENCES recipe_library(id) ON DELETE SET NULL,
    food_id INTEGER REFERENCES food_inventory(id) ON DELETE SET NULL,
    item_name TEXT NOT NULL CHECK (length(btrim(item_name)) BETWEEN 1 AND 160),
    quantity NUMERIC(10,2) NOT NULL CHECK (quantity > 0),
    unit TEXT NOT NULL CHECK (length(btrim(unit)) BETWEEN 1 AND 30),
    calories_kcal NUMERIC(7,1) CHECK (calories_kcal IS NULL OR calories_kcal >= 0),
    protein_g NUMERIC(6,1) CHECK (protein_g IS NULL OR protein_g >= 0),
    nutrition_source TEXT NOT NULL DEFAULT 'unknown'
        CHECK (nutrition_source IN ('user_entered', 'calculated', 'estimate', 'unknown')),
    plan_meal_id INTEGER REFERENCES planned_meals(id) ON DELETE SET NULL,
    source TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'command')),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (recipe_id IS NULL OR item_type = 'recipe'),
    CHECK (food_id IS NULL OR item_type = 'food'),
    CHECK ((calories_kcal IS NULL AND protein_g IS NULL) = (nutrition_source = 'unknown'))
);

CREATE INDEX IF NOT EXISTS idx_meal_logs_date_active
    ON meal_logs(log_date, log_time, id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_meal_logs_plan_meal ON meal_logs(plan_meal_id) WHERE plan_meal_id IS NOT NULL;

COMMIT;
