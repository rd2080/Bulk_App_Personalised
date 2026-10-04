# Daily Check-ins

`daily_checkins` stores one objective Morning Check-in per date. The date is unique, and saving again for that date updates the entry.

| Column | PostgreSQL type | Rule |
|---|---|---|
| `id` | `INTEGER GENERATED ALWAYS AS IDENTITY` | Primary key |
| `checkin_date` | `DATE` | Required, unique |
| `weight_kg` | `NUMERIC(5,2)` | Nullable only for legacy rows; 25–350 when present |
| `sleep_hours` | `NUMERIC(3,1)` | 0–24 when present; required by the Phase 2 form |
| `soreness_level` | `INTEGER` | 1–10 when present; required by the Phase 2 form |
| `daily_notes` | `TEXT` | Optional free-text note |
| `created_at` | `TIMESTAMPTZ` | Required, defaults to `NOW()` |

The page writes `weight_entries(entry_date, weight_kg)` in the same Neon transaction, maintaining the existing weight history. Both tables upsert on their date uniqueness constraints. `weight_entries.weight_kg` uses `NUMERIC(5,2)` and the same 25–350 kg range, established by migration `005_widen_weight_entries_precision.sql`.

The table supports the Phase 2 check-in only. It does not implement meal planning, meal logging, schedules/constraints, or analytics. The SQL migration is `database/migrations/004_add_weight_to_daily_checkins.sql`; migrations in GitHub must be applied to Neon separately.
