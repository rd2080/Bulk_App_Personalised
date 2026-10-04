# User Profile and AI Request Builder

## Profile flow

The Profile page calls `get_user_profile()` to read the sole row from Neon. On save, `upsert_user_profile()` validates exactly the ten supported fields, then atomically inserts or updates that row. The unique expression index in migration 006 prevents more than one row even if writes happen concurrently.

The database remains the only source of truth. No profile copy is saved for AI use. Numeric bounds and required text are validated in both Python and PostgreSQL.

## Request-builder foundation

`bulking_app/ai/request_builder.py` exposes `build_profile_request(task)`. Each invocation calls the profile repository, then returns a structured object containing system instructions, current profile context, a task, and named future context-source extension points. No request is cached and no provider is called. A missing profile or empty task raises a clear error.

Food preferences, inventory, morning check-in, supplements, workout profile, and nutrition data are listed only as future extension points. This change creates no tables or behavior for them and does not implement Phase 3 meal generation.

## Database change

Migration `006_create_user_profile.sql` creates an idempotent `user_profile` table containing only the agreed ten columns. A unique index over the constant expression `(true)` enforces the single-row constraint without adding an identifier field.
