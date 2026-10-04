# Database migrations

Numbered SQL files in this directory are the versioned source of truth for PostgreSQL schema changes. Add a new migration for each change; keep applied migration files immutable. See [schema documentation](../../docs/database/schema.md).

Phase 2 adds `weight_kg` to the existing `daily_checkins` table with migration `004_add_weight_to_daily_checkins.sql`. Migration `005_widen_weight_entries_precision.sql` corrects the original too-narrow `weight_entries.weight_kg` type to `NUMERIC(5,2)` and enforces the supported weight range. Apply migrations to the intended Neon branch and database before deploying code that depends on them. A migration file in GitHub does not change Neon automatically.

Migration `006_create_user_profile.sql` adds the single-user profile table with exactly the ten agreed profile fields and a unique constant-expression index enforcing a single row. It is safe to apply repeatedly.
