# AI architecture

AI is used sparingly and only where deterministic code cannot do the job; see [AI scope](scope.md). Gemini is the only provider. Provider-specific code sits behind adapters and is called through the application service layer, keeping provider integration separate from the Streamlit interface and database.

Provider credentials are supplied through environment configuration locally and deployment secrets in Streamlit Cloud. Do not commit credentials. Generated plans are user-facing suggestions and should be reviewed before use.

## Budget guard (T-005)

`bulking_app/ai/budget.py` wraps the planner returned by `get_planner` (pass `guarded=False` for the raw provider). It provides:

- An in-memory cache keyed by provider + model + SHA-256 of the context, with a TTL (`AI_CACHE_TTL_SECONDS`, default 3600).
- Per-day caps on calls (`AI_MAX_CALLS_PER_DAY`, default 20) and on estimated tokens (`AI_MAX_TOKENS_PER_DAY`, default 40000). Tokens are an estimate (characters / 4), not billed usage. Failed provider attempts still count against the caps.
- `BudgetExceeded` and `ProviderUnavailable` (both subclasses of `AIUnavailable`). Callers must catch `AIUnavailable` and fall back to manual tracking; an AI outage must never block other features.

Limitation: counters and cache are in process memory only. They reset on restart and are not shared between processes or persisted to the database. The "day" uses the server's local date.
