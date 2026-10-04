# Bulk App

A personal bulking assistant. The application uses Streamlit for separate workflows and Neon PostgreSQL for persistent data.

## Run locally

Use Python 3.9+, install `requirements.txt`, configure `DATABASE_URL` with your Neon PostgreSQL connection string, then run `streamlit run app.py`. Never commit database credentials.

## Current scope

**Phase 1 — Food Inventory:** add and edit foods, manage availability categories, and review available or unavailable items. Data is stored in Neon PostgreSQL.

**Phase 2 — Morning Check-in:** use the separate Morning Check-in page to save the check-in date, weight in kg, sleep hours, soreness (1–10), and optional notes. Check-ins persist to Neon PostgreSQL and can be reviewed or updated by date.

**User Profile:** the dedicated Profile page reads and saves the single current profile in Neon. Its only fields are age, height, target weight, diet type, diet philosophy, calorie strategy, cuisine preference, regional context, cooking complexity, and meals per day.

Meal generation is not implemented. The AI request builder is a reusable foundation that reads the profile from its repository every time it is called and returns structured context. It does not save an AI copy of the profile or call an AI provider. Future context sources are extension points only.

## Architecture and database

The app uses the Neon connection helper (`bulking_app/neon.py`) and repository pattern. Profile data access and validation live in `bulking_app/repositories/user_profile.py`. Request preparation lives in `bulking_app/ai/request_builder.py`. See [database schema](docs/database/schema.md) and [User Profile and request builder](docs/user-profile-and-request-builder.md).

Numbered SQL files under `database/migrations/` document schema changes. Apply a new migration to Neon before deploying code that depends on it; a file in GitHub does not change the database automatically.
