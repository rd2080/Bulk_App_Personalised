# Backlog

Status: `todo` | `doing` | `review` | `done` | `blocked`. Reconciled with the owner's seven handover documents on 2026-10-21. Pick the earliest `todo` whose dependencies are done. Acceptance IDs (AC-, D-, OPS-, QA-) refer to those documents.

## P0 Foundation and truth
- T-001 `doing` Fix failing CI: `pytest -q` exits 2 on `main` (collection error suspected: repo root not on `sys.path`). Fix via `pytest.ini` + `python -m pytest`. Accept: green CI on the PR (QA-01, OPS-01).
- T-002 `todo` Legacy SQLite path: `bulking_app/database.py` and `tests/test_services.py` model an older design. Trace call sites; remove or migrate, and document the decision (QA P0).
- T-003 `todo` Postgres integration tests: apply migrations 001–008 to an isolated Neon branch and check constraints, FKs, check-in+weight atomic rollback, plan isolation, CSV atomicity. Must fail closed if the target URL is `production` (QA-03, QA-04, QA-05, QA-08, D-01..D-07). Needs a test `DATABASE_URL` secret for CI; agents use the Neon tools on `claude-dev`.
- T-004 `todo` Migration runner: `scripts/apply_migrations.py` plus a `schema_migrations` table recording applied versions per environment (D-08, OPS-03). Agents run it on `claude-dev` only.
- T-005 `todo` AI budget guard around `bulking_app/ai/`: cache, per-day call/token cap, deterministic fallback, minimal context (AC-14, D-12).
- T-006 `todo` Hygiene: `requirements-dev.txt`, fix duplicate `1_` page prefixes, README test section.
- T-007 `blocked` Verify the live Streamlit deployment and deployed commit (never verified in the handover). Needs the app URL from the owner.
- T-008 `todo` Release runbook in `docs/ops/`: release record template, smoke checklist, rollback notes (Doc 06). Production migration stays a human step.

## P1 Actual meal logging (largest missing feature)
- T-010 `todo` ADR for the log model with recommended defaults (see open decisions D1); the PR review is the owner's gate.
- T-011 `todo` Additive migration + repository for meal logs: consumed time/date, item (recipe, inventory food or free text), amount + unit, optional plan link, source (manual/command), nutrition provenance. Logs can exist without a plan (AC-10, D-09).
- T-012 `todo` "Log what I ate" page: separate from plan editing, partial servings, unplanned items, saved confirmation, daily log.
- T-013 `todo` Command-assisted logging reusing the deterministic parser ("I ate three eggs"); ambiguity asks for clarification.
- T-014 `todo` Idempotent inventory deduction on log; corrections update totals and inventory visibly (AC-11).

## P2 Nutrition
- T-020 `todo` Per-serving nutrition from recipes using the documented scaling; unknown stays unknown; provenance label (product label / dataset / user entry / estimate).
- T-021 `todo` Daily totals from logs only, never from plans; plan vs actual comparison (after T-014).
- T-022 `blocked` Configurable intake targets stored separately from intake, with visible assumptions and a clinician/dietitian note. Needs owner decision D3 first.

## P3 Personalisation (Doc 02)
- T-030 `blocked` Configurable preferences (eggs, exclusions, shake ingredients, budget, equipment, meal timing). `user_profile` is fixed at ten fields by earlier decision, so propose an additive `user_preferences` table. Needs D2.
- T-031 `todo` Staleness: show the age of profile/measurement values and prompt confirmation when it matters.
- T-032 `todo` Optional structured observations for digestion, appetite and energy, non-diagnostic, saved with partial check-ins.

## P4 Analysis
- T-040 `todo` Weight and check-in charts with date range, units, sample count, visible missing days, low-confidence labels (AC-12, D-11).
- T-041 `todo` Deterministic weekly review (after T-021).

## P5 AI features (after T-005; Gemini free tier by default)
- T-050 `todo` Advisory meal suggestions grounded in inventory, recipes and preferences: labelled as generated, context disclosed, regenerate/edit/accept/dismiss, safe failure (AC-14, AC-15).
- T-051 `todo` Optional Claude provider adapter; default provider unchanged.
- T-052 `blocked` Calisthenics workout planning and logging (pull-up and dip bar only). Needs D4.

## P6 Later / undecided
- T-060 `blocked` Reminders: channel, runtime and quiet hours undecided; Streamlit Cloud has no scheduler (D5).
- T-061 `blocked` CSV export: scope undecided (D6).
- T-062 `todo` Supplement tracking as user-entered products only.

## Meta
- T-070 `done` Handover documents merged. Documents 05 (roadmap/status) and 06 (AI automation strategy) listed in Doc 01 were not supplied; this backlog, `PROGRESS.md` and `CLAUDE.md` replace them.
