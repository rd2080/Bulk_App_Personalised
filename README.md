# Bulk App

A personal bulking assistant for structured daily planning, food inventory, meal logging, and later data-driven insights.

## Run locally

Use Python 3.9+, install `requirements.txt`, configure `DATABASE_URL` with the Neon PostgreSQL connection string, then run `streamlit run app.py`.

AI provider keys are not required for Phase 1.

## Current development scope

**Phase 1 — Food Inventory**

- Dedicated Food Inventory page
- Add and edit foods
- Availability categories
- Available/unavailable checklist-style views
- Optional stock quantity and unit
- Neon PostgreSQL persistence

Meal planning, morning check-ins, meal logging, and analytics are intentionally deferred to later phases.

## Architecture

The app uses Streamlit for the interface, Neon PostgreSQL for persistent data, and GitHub for application code, migrations, and documentation. See [architecture](docs/architecture/overview.md), [database schema](docs/database/schema.md), and [Phase 1 documentation](docs/phase-1-food-inventory.md).
