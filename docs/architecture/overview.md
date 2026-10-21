# Architecture overview

## System components

- **GitHub** is the versioned source for application code, PostgreSQL migrations, tests, and documentation.
- **Streamlit** provides the Profile, Food Inventory, Morning Check-in, Voice Input, and Daily Meal Plan pages (in that order).
- **Neon PostgreSQL** provides persistent application data.
- **The Neon connection helper** in `bulking_app/neon.py` reads deployment secrets and is shared by repository modules.
- **Deterministic meal command processing** in `bulking_app/meal_commands.py` interprets a limited set of reviewed commands with Python rules. It has no Gemini/OpenAI dependency.

The deployed app connects to Neon using deployment secrets. Credentials belong in Streamlit Cloud secrets or local environment configuration, never in source control.

## Meal command data flow

```text
Browser speech recognition or typed text
        ↓
User reviews/corrects transcription
        ↓
Deterministic command parser
        ↓
Validation and clarification checks
        ↓
Existing meal-plan repository
        ↓
Neon daily_meal_plans / planned_meals
```

Routine plan entry, retrieval, and supported command operations do not require an AI API call. Complex suggestions and nutrition analysis remain separate future work.

## Change workflow

Keep schema changes as reviewed SQL migration files in `database/migrations/`. Update the related database documentation in the same change. Apply a migration to the intended Neon branch and database before deploying code that depends on it.

## Current scope

The app supports Food Inventory, Morning Check-in, User Profile, Recipe Library, browser-based voice transcription, dated meal plans, and deterministic meal commands. Nutrition calculations, AI meal suggestions, and actual-consumption logging remain future phases.
