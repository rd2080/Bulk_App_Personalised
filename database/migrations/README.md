# Database migrations

Numbered SQL files in this directory are the versioned source of truth for PostgreSQL schema changes. Add a new migration for each change; keep applied migration files immutable. See [schema documentation](../../docs/database/schema.md).

Phase 2 adds `weight_kg` to the existing `daily_checkins` table with migration `004_add_weight_to_daily_checkins.sql`. Migration `005_widen_weight_entries_precision.sql` corrects the original too-narrow `weight_entries.weight_kg` type to `NUMERIC(5,2)` and enforces the supported weight range. Apply migrations to the intended Neon branch and database before deploying code that depends on them. A migration file in GitHub does not change the database automatically.

Migration `006_create_user_profile.sql` adds the single-user profile table with exactly the ten agreed profile fields and a unique constant-expression index enforcing a single row. It is safe to apply repeatedly.

Migration `007_create_recipe_library.sql` adds `recipe_library` and `recipe_ingredients` without changing `food_inventory`. It is additive and safe to apply repeatedly. Recipe nutrition is stored only on `recipe_library`; ingredients store composition only.

Migration `008_create_daily_meal_plans.sql` adds the dated meal-plan header and its ordered meal rows. It is additive and leaves check-ins, inventory, recipes, profile, and weight history unchanged.

Migration `009_create_meal_logs.sql` adds the `meal_logs` table (what was actually eaten), with soft delete and optional links to recipes, foods and planned meals. It is additive, safe to apply repeatedly, and leaves every existing table unchanged. Recovery: the table is new and empty at creation, so `DROP TABLE meal_logs` (owner approval needed) or the Neon backup branch taken before applying it.
