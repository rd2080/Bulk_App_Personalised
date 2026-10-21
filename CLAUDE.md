# Bulk App — Claude Code project rules

Personal, single-user bulking assistant. Streamlit UI, Neon PostgreSQL, deployed on Streamlit Cloud from `main`. No commercial purpose.

## Non-negotiables
- Never commit secrets. Credentials live in `.env` locally and Streamlit Cloud secrets.
- Never touch the Neon `production` branch. Test migrations/queries on the `claude-dev` branch only. Applying a migration to production is a human step.
- Never edit an existing migration in `database/migrations/`. Add a new numbered file; update `docs/database/schema.md` and `database/migrations/README.md` in the same PR.
- Never push to `main`. Work on `claude/<task-id>-<slug>` branches and open a PR.
- SQL lives only in `bulking_app/repositories/`. Pages in `pages/` stay thin; logic lives in `bulking_app/services/`.
- Every change needs tests in `tests/` and must pass `pytest`.

## Cost rule
The owner wants near-zero running cost. Deterministic Python first; call an AI provider only when rules cannot do the job. Every AI call must go through the budget guard (BACKLOG T-004): cache identical requests, cap calls/tokens per day, degrade gracefully at the cap. Default provider stays Gemini (free tier).

## Working loop for agents
1. Read `docs/PROGRESS.md`; pick the next unblocked task from `docs/BACKLOG.md`.
2. Implement on a task branch, run `pytest`, open a PR.
3. A separate reviewer agent checks the PR against these rules before the task is marked done.
4. Update `docs/PROGRESS.md` (done / blocked / needs owner decision) and the backlog status.

Commit messages end with the Co-Authored-By trailer; PR descriptions end with the Claude Code line.
