# Architecture decisions

## GitHub repository for code, migrations, and documentation

**Decision:** Keep application source, versioned database migrations, and project documentation in the GitHub repository.

**Reason:** Related changes can be reviewed and audited together, while the README stays brief and detailed material lives under `docs/`.

## Streamlit Cloud for runtime

**Decision:** Use Streamlit Cloud to run the deployed application.

**Reason:** It provides the hosted runtime for the Streamlit interface.

## Neon PostgreSQL for deployed persistence

**Decision:** Use Neon PostgreSQL for persistent deployed data rather than SQLite.

**Reason:** The app runs on Streamlit Cloud, and persistent data should live in a managed database rather than depend on a local app filesystem.

## No profile table for the single-user app

**Decision:** Do not create a profile table for the current single-user application.

**Reason:** Personal context is static application context; storing it as a relational profile row adds no current value. Revisit if the app becomes multi-user or needs editable persisted profiles.

## Migration files as schema history

**Decision:** Store schema changes as versioned SQL files in `database/migrations/`.

**Reason:** Each change can be reviewed and audited, and applied migration history remains explicit. The files are the source of truth for intended schema evolution.

## Initial table: weight entries

**Decision:** Start the database design with the agreed `weight_entries` table.

**Reason:** Daily weight history is the first persistent feature. Its schema is described in [Database schema](../database/schema.md) and defined by migration `001_create_weight_entries.sql`.
