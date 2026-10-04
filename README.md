# Bulk App

A personal bulking assistant. The application uses Streamlit for separate workflows and Neon PostgreSQL for persistent data.

## Run locally

Use Python 3.9+, install `requirements.txt`, configure `DATABASE_URL` with your Neon PostgreSQL connection string, then run `streamlit run app.py`. Never commit database credentials.

## Current scope

**Phase 1 — Food Inventory:** add and edit foods, manage availability categories, and review available or unavailable items. Data is stored in Neon PostgreSQL.

**Phase 2 — Morning Check-in:** use the separate Morning Check-in page to save the check-in date, weight in kg, sleep hours, soreness (1–10), and optional notes. Check-ins persist to Neon PostgreSQL and can be reviewed or updated by date.

Meal planning, meal logging, schedules/constraints, and analytics are not included in these phases.

## Architecture and database

The app uses the existing Neon connection helper (`bulking_app/neon.py`) and repository pattern. See [architecture](docs/architecture/overview.md), [database schema](docs/database/schema.md), [Phase 1](docs/phase-1-food-inventory.md), and [Phase 2](docs/phase-2-morning-check-in.md).

Numbered SQL files under `database/migrations/` document schema changes. Apply a new migration to Neon before deploying code that depends on it; a file in GitHub does not change the database automatically.
