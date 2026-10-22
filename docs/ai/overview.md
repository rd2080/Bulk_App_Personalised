# AI architecture

AI is used sparingly and only where deterministic code cannot do the job; see [AI scope](scope.md). Decided provider: Claude API (Haiku-class model by default). The current code still contains the Gemini adapter until backlog item 6 replaces it. Provider-specific code sits behind adapters and is called through the application service layer, keeping provider integration separate from the Streamlit interface and database.

Provider credentials are supplied through Streamlit Cloud secrets (and GitHub secrets if a workflow needs them). Never commit, print or ask for credentials. Generated output is an advisory suggestion that the owner accepts, edits or dismisses.

## Budget guard (T-005)

`bulking_app/ai/budget.py` wraps the planner returned by `get_planner` (pass `guarded=False` for the raw provider). It provides:

- An in-memory cache keyed by provider + model + SHA-256 of the context, with a TTL (`AI_CACHE_TTL_SECONDS`, default 3600).
- Per-day caps on calls (`AI_MAX_CALLS_PER_DAY`) and on estimated tokens (`AI_MAX_TOKENS_PER_DAY`). Tokens are an estimate (characters / 4), not billed usage. Failed provider attempts still count against the caps.
- `BudgetExceeded` and `ProviderUnavailable` (both subclasses of `AIUnavailable`). Callers must catch `AIUnavailable` and fall back; an AI outage must never block other features.

Decided targets (backlog item 6): default 5 calls/day and a low token cap (code defaults are currently 20 and 40000), one structured request per feature per day, cache persisted for the day so restarts do not re-spend.

Limitation today: counters and cache are in process memory only. They reset on restart and are not shared between processes. The "day" uses the server's local date.
