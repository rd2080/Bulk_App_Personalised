# Database migrations

Numbered SQL files in this directory are the versioned source of truth for PostgreSQL schema changes. Add a new migration for each change; keep migration files immutable after application. See [schema documentation](../../docs/database/schema.md).

A migration file in GitHub is not automatically applied to Neon.
