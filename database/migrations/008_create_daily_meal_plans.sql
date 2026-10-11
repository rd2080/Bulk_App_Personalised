-- Daily meal planning is additive; existing check-in, inventory, and recipe tables are unchanged.
CREATE TABLE IF NOT EXISTS daily_meal_plans (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_date DATE NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planned_meals (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES daily_meal_plans(id) ON DELETE CASCADE,
    meal_type TEXT NOT NULL CHECK (meal_type IN ('Breakfast', 'Morning snack', 'Lunch', 'Afternoon snack', 'Dinner', 'Other')),
    meal_name TEXT NOT NULL CHECK (length(btrim(meal_name)) BETWEEN 1 AND 160),
    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 2000),
    position INTEGER NOT NULL CHECK (position >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_planned_meals_plan_position ON planned_meals(plan_id, position, id);
