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

## Migration source of truth

Numbered SQL files in `database/migrations/` are the versioned schema source of truth. Add a migration for each change and keep applied migration files immutable. Update documentation alongside schema changes. A migration file in GitHub does not apply itself to Neon.
