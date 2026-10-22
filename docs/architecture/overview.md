# Architecture overview

## System components

- **GitHub** is the versioned source for application code, PostgreSQL migrations, tests, and documentation.
- **Streamlit** provides the Profile, Food Inventory, Morning Check-in, Voice Input, and Daily Meal Plan pages (in that order).
- **Neon PostgreSQL** provides persistent application data.
- **The Neon connection helper** in `bulking_app/neon.py` reads deployment secrets and is shared by repository modules.
- **Claude API** (decided, D7) for AI features A1 and A4 only, behind the budget guard in `bulking_app/ai/`. The Gemini adapter remains until it is replaced.
- **GitHub Actions** runs CI and the Ship pipeline, and (planned) a scheduled morning reminder sent through a Telegram bot using a read-only database role.
- **Deterministic meal command processing** in `bulking_app/meal_commands.py` interprets a limited set of reviewed commands with Python rules. It has no AI-provider dependency.

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

Keep schema changes as reviewed SQL migration files in `database/migrations/`. Update the related database documentation in the same change. Additive migrations are applied by agents to `claude-dev`, then to production after a Neon backup branch and before merging dependent code (`.claude/skills/migration-procedure/SKILL.md`). Destructive changes need owner approval.

## Current scope

The app supports Food Inventory, Morning Check-in, User Profile, Recipe Library, browser-based voice transcription, dated meal plans, and deterministic meal commands. Planned next (see `docs/BACKLOG.md`): meal logging with daily target vs progress, IFCT 2017 food data and recipe nutrition, suggested targets and next-meal timing, calisthenics plans, weekly check-ins and Telegram reminders, AI A1/A4 on Claude, improvement tracker and morning motivation.
