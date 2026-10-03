# Bulking App V0.1

A small local-first app for a morning check-in, AI-generated meal/workout plan, and SQLite history. It uses Streamlit, Python, and SQLite, with Gemini as the routine provider and OpenAI as an optional alternative. There is no authentication and no MCP dependency.

## Run locally

1. Use Python 3.9 or newer.
2. Create and activate a virtual environment, then install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` or `OPENAI_API_KEY`.
4. Start the app:

   ```bash
   streamlit run app.py
   ```

The database is created automatically at `DATABASE_PATH` (default `bulking_app.db`). `.env` and database files are ignored by Git. Never put a real API key in source control.

## Morning flow

Enter today's weight, how you feel, available foods, and any schedule or workout notes. Generate a plan, review and edit its text, then save it. Saving records the check-in, available foods, the daily plan, and a log entry in SQLite. AI output is guidance, not medical advice; review it and adapt it to your needs.

## Structure

- `app.py`: Streamlit morning check-in and plan review
- `bulking_app/database.py`: schema, connection management, and initialization
- `bulking_app/services/`: validation and database operations
- `bulking_app/ai/`: provider-agnostic interface and Gemini/OpenAI adapters
- `tests/`: lightweight local checks for persistence and provider selection

Provider calls are made from Python service code. Gemini is the default routine planner; choose `AI_PROVIDER=openai` for the OpenAI adapter. Configure `OPENAI_API_KEY` to enable the more capable reasoning provider. No provider key is needed just to import the app or use the storage functions.
