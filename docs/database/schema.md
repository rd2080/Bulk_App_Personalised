# Database schema

## Database choice

The deployed application uses Neon PostgreSQL for persistent storage. PostgreSQL was chosen over SQLite because the app runs on Streamlit Cloud and needs database persistence independent of an individual app process or local filesystem.

## Current first table: `weight_entries`

The agreed initial table stores one daily weight measurement:

| Column | PostgreSQL type | Rule / default | Purpose |
|---|---|---|---|
| `id` | `BIGSERIAL` | Primary key | Stable row identifier |
| `entry_date` | `DATE` | `NOT NULL UNIQUE` | One entry per calendar day |
| `weight_kg` | `NUMERIC(3,2)` | `NOT NULL` | Weight in kilograms |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT NOW()` | Creation timestamp |

The corresponding versioned migration is `database/migrations/001_create_weight_entries.sql`. The schema is documented here and in the migration file; this documentation task does not apply it to Neon.

## Migration source of truth

`database/migrations/` is the versioned source of truth for schema changes. Represent every database change in a numbered SQL migration file so the intended evolution is reviewable and auditable. Keep applied migration files immutable; add a new migration for later changes. Update this document alongside schema migrations when the documented design changes.

A migration file records an intended change. It does not mean that the migration has been run against Neon.
