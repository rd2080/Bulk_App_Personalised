# Backlog

Status: `todo` | `doing` | `review` | `done` | `blocked`. Priorities are provisional until the owner's Codex/ChatGPT strategy documents are merged (T-050).

## P0 Foundation
- T-001 `todo` CI: GitHub Actions running `pytest` on every PR.
- T-002 `todo` Migration runner: `scripts/apply_migrations.py` with a `schema_migrations` table; applies pending files to a chosen Neon branch. Idempotent, tested on `claude-dev`.
- T-003 `todo` Hygiene: `requirements-dev.txt` (pytest), fix duplicate `1_` page numbering, README test section.
- T-004 `todo` AI cost guard: cache + per-day call/token cap + deterministic fallback around `bulking_app/ai/`, with unit tests.
- T-005 `todo` Optional Claude adapter alongside Gemini/OpenAI; default provider unchanged.

## P1 Nutrition
- T-010 `todo` Link planned meals to recipes/foods; compute per-meal nutrition deterministically.
- T-011 `todo` Daily calorie/protein targets from profile + recent weight trend (rules, no AI).
- T-012 `todo` Daily totals vs targets on the Daily Meal Plan page.

## P2 Consumption tracking
- T-020 `todo` Additive migration for actual meals eaten.
- T-021 `todo` UI to log actual consumption, including via the voice/command flow.
- T-022 `todo` Plan vs actual comparison.

## P3 Progress
- T-030 `todo` Weight trend and weekly rate-of-gain charts from `weight_entries`.
- T-031 `todo` Deterministic weekly review from check-ins and consumption.

## P4 AI suggestions (after T-004)
- T-040 `todo` Grounded meal suggestions from inventory + recipes + targets, behind the budget guard.
- T-041 `blocked` Workout plan generation: needs owner decision on scope.

## Meta
- T-050 `blocked` Merge owner's ChatGPT/Codex documents into docs/ and reconcile with this backlog.
