# Phase 2 — Morning Check-in

## Goal and scope

Phase 2 adds a separate Streamlit page for recording objective daily inputs. Each check-in captures a date, weight in kilograms, sleep hours, soreness on a 1–10 scale, and optional notes. The user can revisit a date to update its entry and review recent saved entries.

There is no generic mood/feeling prompt. Schedules and constraints, meal planning, meal logging, and analytics remain out of scope.

## Data flow

```text
Streamlit Morning Check-in page
        ↓
Morning check-in repository
        ↓
Neon connection helper
        ↓
daily_checkins + weight_entries (one transaction)
```

`daily_checkins` stores the complete check-in. The existing `weight_entries` table is also upserted to preserve the established daily weight history. Saving both records is atomic. `checkin_date` is unique, so resubmitting a date updates that day's data.

## Database change

Migration `004_add_weight_to_daily_checkins.sql` adds `weight_kg NUMERIC(5,2)` and a 25–350 kg check constraint. Migration `005_widen_weight_entries_precision.sql` corrects the original `weight_entries.weight_kg NUMERIC(3,2)` precision to `NUMERIC(5,2)`, which can represent body weights, and applies the same range constraint. The daily check-in weight remains nullable only for legacy rows; the Phase 2 form requires a weight and always writes one. The existing sleep (0–24 hours) and soreness (1–10) constraints remain in place. Notes are optional.

Apply the migration to Neon before deploying Phase 2. The migration is additive and does not alter Food Inventory.
