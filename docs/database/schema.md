# Database schema

## Database

The deployed application uses Neon PostgreSQL. `bulking_app/neon.py` is the shared connection helper; SQL operations belong in repository modules.

## Phase 1 — `food_inventory`

The existing Food Inventory table and behavior are unchanged. See [Food Inventory schema](food_inventory.md) and migration `003_create_food_inventory.sql`.

## Weight history — `weight_entries`

| Column | PostgreSQL type | Rule |
|---|---|---|
| `id` | `BIGSERIAL` | Primary key |
| `entry_date` | `DATE` | Required, unique |
| `weight_kg` | `NUMERIC(5,2)` | Required, 25–350 kg |
| `created_at` | `TIMESTAMPTZ` | Required, defaults to `NOW()` |

Migration `001_create_weight_entries.sql` records the original `NUMERIC(3,2)` definition. That precision allowed only one digit before the decimal and could not store human body weights. Migration `005_widen_weight_entries_precision.sql` corrects deployed databases to `NUMERIC(5,2)` and adds the 25–350 kg database constraint. Application validation uses the same supported range.

## Phase 2 — `daily_checkins`

One row per check-in date. Columns are `id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY`, `checkin_date DATE NOT NULL UNIQUE`, `weight_kg NUMERIC(5,2)`, `sleep_hours NUMERIC(3,1)`, `soreness_level INTEGER`, `daily_notes TEXT`, and `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`. Weight is nullable only to preserve compatibility with any pre-Phase 2 rows; Phase 2 requires and writes it. Weight is constrained to 25–350 kg, sleep to 0–24 hours, and soreness to 1–10. Notes are optional.

The check-in repository also upserts the corresponding date and weight into `weight_entries` in the same transaction. See [daily check-in details](daily_checkins.md).

## User Profile — `user_profile`

The single-user profile has exactly ten columns: `age SMALLINT`, `height_cm NUMERIC(5,1)`, `target_weight_kg NUMERIC(5,1)`, `diet_type TEXT`, `diet_philosophy TEXT`, `calorie_strategy TEXT`, `cuisine_preference TEXT`, `regional_context TEXT`, `cooking_complexity TEXT`, and `meals_per_day SMALLINT`. All fields are required and constrained to supported numeric/text ranges. There is no id, name, timestamp, current weight, primary goal, allergy, or foreign-food-preference column. A unique expression index on the constant `true` enforces at most one row without adding a column. Migration `006_create_user_profile.sql` creates the table and index idempotently.

The Profile page reads/writes through `bulking_app/repositories/user_profile.py`. The request builder calls that repository afresh on each invocation and never stores another profile copy. See [profile and request-builder architecture](../user-profile-and-request-builder.md).

## Recipe Library — `recipe_library` and `recipe_ingredients`

`recipe_library` has exactly `id`, `recipe_name`, `recipe_type`, `preference_level`, `cooking_complexity`, `total_weight_g`, `calories_kcal`, `protein_g`, `carbohydrates_g`, and `fat_g`. Recipe names are unique. Type values are `meal`, `snack`, or `shake`; preference values are `favorite`, `like`, `neutral`, `dislike`, or `never`; complexity values are `easy`, `medium`, or `hard`. Total prepared weight must be positive; nutrition values must be non-negative.

`recipe_ingredients` has exactly `recipe_id`, `food_id`, `quantity`, and `unit`. It references `recipe_library` with delete cascade and `food_inventory` with delete restriction. Quantity is positive, unit is non-empty, and each food can occur once per recipe. There are no ingredient-level calories or macros. Recipe nutrition per serving is deterministic proportional scaling: each recipe nutrient multiplied by `serving_weight_g / total_weight_g`.

Migration `007_create_recipe_library.sql` is additive and preserves the existing inventory table. Recipe CRUD, composition, CSV import, and serving calculations live in `bulking_app/repositories/recipe_library.py` and `bulking_app/services/recipe_csv.py`.

## Migration source of truth

Numbered SQL files in `database/migrations/` are the versioned schema source of truth. Add a migration for each change and keep applied migration files immutable. Update documentation alongside schema changes. A migration file in GitHub does not apply itself to Neon.
