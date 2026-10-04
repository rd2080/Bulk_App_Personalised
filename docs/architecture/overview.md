# Architecture overview

## System components

- **GitHub** is the versioned source for application code, PostgreSQL migrations, and documentation.
- **Streamlit Cloud** runs the deployed application with separate pages for Food Inventory and Morning Check-in.
- **Neon PostgreSQL** provides persistent application data.
- **The Neon connection helper** in `bulking_app/neon.py` reads deployment secrets and is shared by repository modules.

The deployed app connects to Neon using deployment secrets. Credentials belong in Streamlit Cloud secrets or local environment configuration, never in source control.

## Change workflow

Keep schema changes as reviewed SQL migration files in `database/migrations/`. Update the related database documentation in the same change. Apply a migration to the intended Neon branch and database before deploying code that depends on it.

## Current scope

Phase 1 provides Food Inventory. Phase 2 provides an objective Morning Check-in for date, weight, sleep hours, soreness, and optional notes. This is a single-user personal application. Meal planning, meal logging, schedules/constraints, and analytics are deferred.
