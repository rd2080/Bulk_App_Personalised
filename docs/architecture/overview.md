# Architecture overview

## System components

- **GitHub** is the versioned source for application code, PostgreSQL migrations, and documentation.
- **Streamlit Cloud** runs the deployed application.
- **Neon PostgreSQL** provides persistent application data for the deployed app.
- **AI provider adapters** generate meal and workout plans through the app's service layer.

The deployed app connects to Neon using deployment secrets. Credentials belong in Streamlit Cloud secrets or local environment configuration, never in source control.

## Change workflow

Keep schema changes as reviewed SQL migration files in `database/migrations/`. Update the related database documentation in the same change. Applying a migration to Neon is a separate deployment operation; a migration file in GitHub does not itself change the live database.

## Current scope

This is a single-user personal application. Static personal context is configured as application context and does not require a profile row. The architecture can be revisited if multi-user support becomes a real requirement.
