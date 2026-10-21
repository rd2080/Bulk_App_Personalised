# Bulk App

A personal bulking assistant. The application uses Streamlit for separate workflows and Neon PostgreSQL for persistent data.

## Run locally

Use Python 3.9+, install `requirements.txt`, configure `DATABASE_URL` with your Neon PostgreSQL connection string, then run `streamlit run app.py`. Never commit database credentials.

## Current scope

**Phase 1 — Food Inventory:** add and edit foods, manage availability categories, and review available or unavailable items. Data is stored in Neon PostgreSQL.

**Phase 2 — Morning Check-in:** use the separate Morning Check-in page to save the check-in date, weight in kg, sleep hours, soreness (1–10), and optional notes. Check-ins persist to Neon PostgreSQL and can be reviewed or updated by date.

**User Profile:** the dedicated Profile page reads and saves the single current profile in Neon. Its fields cover age, height, target weight, diet type, diet philosophy, calorie strategy, cuisine preference, regional context, cooking complexity, and meals per day.

**Recipe Library:** the Food Inventory page also manages recipes, recipe-level nutrition, preference and cooking complexity, prepared weight, and ingredient composition. Ingredients reference existing inventory foods but do not store nutrition. CSV import and template downloads are documented in [Recipe Library](docs/recipe-library.md).

**Phase 1 — Voice Input:** browser microphone dictation, editable transcription review, and text fallback. Transcription does not call Gemini or OpenAI. Browser support varies; Chrome was manually confirmed during development. See [Voice Input](docs/voice-input.md).

**Phase 2 — Daily Meal Plan:** create, edit, remove, and review meals for a selected date. Plans persist in Neon through `bulking_app/repositories/meal_plan.py`. See [Daily Meal Plan](docs/daily-meal-plan.md) and migration `008_create_daily_meal_plans.sql`.

**Phase 3 — Deterministic Meal Commands:** reviewed text from the Voice Input page can populate or update the selected day's plan. Supported actions include a labeled multi-meal plan and explicit add, replace, and remove commands. The parser uses Python rules and does not call Gemini/OpenAI. Ambiguous requests ask for clarification. See [Voice Input](docs/voice-input.md).

## Tests

CI runs `python -m pytest -q` on every push. Locally, run `pip install -r requirements-dev.txt` and then `python -m pytest`. Pushing a `claude/*` branch triggers the Ship workflow (`.github/workflows/ship.yml`), which runs the tests and squash-merges into `main` only if they pass.

## Architecture and database

The app uses the Neon connection helper (`bulking_app/neon.py`) and repository pattern. Profile data access and validation live in `bulking_app/repositories/user_profile.py`. AI request preparation lives in `bulking_app/ai/request_builder.py`; it does not itself call an AI provider.

Numbered SQL files under `database/migrations/` document schema changes. Apply a migration to the intended Neon branch/database before deploying code that depends on it; a file in GitHub does not change the database automatically.

The existing Neon schema includes `daily_meal_plans` and `planned_meals` for dated meal plans. Phase 3 reuses these tables and introduces no database migration. See [database schema](docs/database/schema.md).

AI meal suggestions, nutrition calculations, and actual-consumption tracking remain future phases. Routine plan entry and command processing do not require AI calls.
