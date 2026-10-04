# Database migrations

Numbered SQL files in this directory are the versioned source of truth for PostgreSQL schema changes. Add a new migration for each change; keep applied migration files immutable. See [schema documentation](../../docs/database/schema.md).

Phase 2 adds `weight_kg` to the existing `daily_checkins` table with migration `004_add_weight_to_daily_checkins.sql`. Apply migrations to the intended Neon branch and database before deploying code that depends on them. A migration file in GitHub does not change Neon automatically.
