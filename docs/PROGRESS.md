# Progress log

Newest first. Each agent session appends what was done, what is blocked, and what needs an owner decision.

## 2026-10-21 — OpenAI removed, AI re-scope proposed
- Owner dropped the OpenAI SDK and asked to re-scope AI. Removed `openai_adapter.py`, the `openai` dependency, env vars and doc mentions; Gemini is the only provider. Proposed scope in `docs/ai/scope.md` (D11), awaiting the owner's pick.

## 2026-10-21 — Wave 1 merged (T-002, T-005, T-006)
- T-002 (PR #7): legacy SQLite path removed; D8 closed. T-006 (PR #8): `requirements-dev.txt`, unique page prefixes, README tests section. T-005 (PR #9): AI budget guard (cache, daily call/token caps, safe failure) wired into `get_planner`. All three Ship runs green and squash-merged to `main` (`34c7b67`).
- Not verified: live Streamlit deploy (needs app URL, T-007). Caps are per-process; no caller catches `AIUnavailable` yet (T-050).
- Waiting on owner: D9 (production migrations) before any schema task; D2-D6.

## 2026-10-21 — Hands-off shipping
- Owner is non-technical and wants to only text the agent, with no manual PR approval. PRs #4 and #5 merged. Replaced Auto PR with `ship.yml`: push `claude/**` → tests → auto PR → squash-merge. Local-computer tools were unavailable this session, so CI is the test runner.
- T-001 done: CI green on the bug-fix branch (tests passed in the push run).

## 2026-10-21 — CI diagnosis and meal-command bug (T-001)
- `pytest.ini` fix worked: collection now succeeds. CI then showed 35 passed, 1 failed (annotation text from the `claude/ci-visible-failures` run).
- Real bug: `parse_meal_commands` omitted the `clarification` key for single-slot remove/replace/add, so `apply_meal_commands` raised `KeyError` for every such command in the app. Fixed (key always present, `.get` in apply) with regression tests. Not yet confirmed green in CI.
- Auto PR verified: a `claude/**` push opened PR #4 automatically. PRs opened by the workflow show CI as `action_required` for the `pull_request` event; the push-event CI run on the same commit is the real check.

## 2026-10-21 — Auto PR workflow
- The agent's PR connector returns 403 (app lacks pull-request write), but `git push` works. Added `.github/workflows/auto-pr.yml`: pushing a `claude/**` branch opens a PR into `main`; merging stays manual. CI now also runs on `claude/**` pushes.
- One-time owner setting required: repo Settings → Actions → General → Workflow permissions → enable "Allow GitHub Actions to create and approve pull requests". Not yet verified working.

## 2026-10-21 — Handover documents merged
- Read all seven handover PDFs. Distilled their rules into `CLAUDE.md`, reconciled `BACKLOG.md`, and listed decisions in `docs/decisions/open-decisions.md`. The PDFs themselves are not committed: the repo is public and they contain personal measurements.
- Findings:
  - CI run #1 (PR branch) and #2 (`main`) both failed in the `pytest -q` step with exit code 2, which usually means collection errors. Suspected cause: repo root not on `sys.path`. Fix proposed in this PR (`pytest.ini`, `python -m pytest`); unconfirmed until CI runs because step logs require sign-in.
  - The agent sandbox cannot reach PyPI (proxy returns 403), so agents cannot run `pytest` locally here. CI is the test runner for sandbox sessions; local Claude Code on the owner's machine can run it directly.
  - Documents 05 and 06 named in Doc 01 (roadmap/status, AI automation strategy) were not supplied. Files supplied as 05/06/07 are data model, deployment runbook and testing plan.
  - No dedicated actual-consumption table exists (matches Doc 03): the main missing feature.
  - `claude-dev` Neon branch is a copy of production taken 2026-10-21 and contains real rows.
- Needs owner: D2, D3, D4, D5, D6 in `docs/decisions/open-decisions.md`; the Streamlit app URL (T-007); a test `DATABASE_URL` GitHub secret for T-003.

## 2026-10-21 — Setup
- Audited repo (Streamlit + Neon, 8 migrations, 8 tables, a test file per module).
- Neon: only `production` existed. Created `claude-dev` for agent testing.
- Added CLAUDE.md, BACKLOG.md, this log, CI workflow (PR #1, merged).
