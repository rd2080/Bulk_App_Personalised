# Bulk App

A personal bulking assistant for daily weight tracking and AI-generated meal and workout plans.

## Run locally

Use Python 3.9+, install `requirements.txt`, configure an AI provider key from `.env.example`, then run `streamlit run app.py`.

## Architecture

The app runs on Streamlit Cloud, stores persistent data in Neon PostgreSQL, and keeps application code, migrations, and documentation in this GitHub repository. See [docs](docs/architecture/overview.md) for the system overview and [database documentation](docs/database/schema.md) for the current schema and migration workflow.
