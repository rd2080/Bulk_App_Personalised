# Bulk App — Claude Code project rules

Personal, single-user bulking assistant for the owner only. Streamlit UI, Neon PostgreSQL, Streamlit Cloud deploys from `main`. No commercial purpose, no multi-user or auth work without owner approval.

## Source of truth (when sources disagree)
1. The owner's current instruction. 2. Verified live behaviour/schema. 3. Approved requirements and decisions in `docs/`. 4. Code and tests together. 5. Git history. 6. Older notes.
Document any mismatch between code and requirements; never silently redefine a requirement because the code differs.

## Non-negotiables
- Never commit secrets. Credentials live in `.env` locally and Streamlit Cloud secrets.
- **This repo is public. Never commit personal data**: no weight, height, age, health or digestion notes, or diet specifics in code, tests, fixtures, docs, logs or PRs. Use synthetic data. Personal values live only in Neon.
- Never touch the Neon `production` branch. Test on `claude-dev` (project `ancient-bonus-73336167`). `claude-dev` was copied from production on 2026-10-21 and contains real rows: never print or commit them. Applying a migration to production is a human step.
- Never edit an existing migration. Add a new numbered file, update `docs/database/schema.md` and `database/migrations/README.md` in the same PR, make it additive, and note the recovery path for anything risky.
- Never push directly to `main`, force-push, or rewrite shared history. Work on `claude/<task-id>-<slug>` branches and push them. The Ship workflow (`.github/workflows/ship.yml`) runs the tests and, when they pass, opens a PR and squash-merges it into `main` automatically; the owner does not review or approve merges. Add `[hold]` to the head commit message to test a branch without merging. Failed tests leave the branch unmerged: fix it, do not bypass CI. Merged code redeploys the live app, so keep changes small and tested.
- SQL lives only in `bulking_app/repositories/` (parameterised, transactional where related writes must succeed together). Pages stay thin; logic lives in `bulking_app/services/`.
- Every change needs tests in `tests/`, using synthetic data, and CI must pass.

## Product rules (from the owner's handover documents)
- Planned is not consumed. Plans never create or alter consumption logs; regenerating a plan never deletes logs. Nothing counts as eaten without an explicit logging action.
- No hardcoded dietary rules, targets, preferences or routine in code or prompts. Read them from the profile/preferences in Neon. Old values (weight, schedule) are starting context, not current facts: show their age and let the owner correct them.
- Never invent food, stock, nutrition values, completed actions or successful writes. Unknown nutrition is unknown, not zero. Quantities carry units; incompatible units are never summed. Label estimates, calculations and AI suggestions apart from user-entered facts.
- Inventory changes follow explicit rules and are idempotent (a retried command must not deduct twice).
- AI output is validated and advisory: it never changes plans, logs or inventory without the owner's acceptance, and an AI outage must never block manual tracking. Explicit commands ("I ate three eggs") use deterministic logic. Send an AI provider only the minimum context the task needs.
- Health: no diagnosis, no supplement prescriptions, no aggressive targets. Digestion/appetite entries are user observations, never conclusions about causes. A single weigh-in or missed meal is not a trend or a reason for extreme adjustment. Recommend a clinician or dietitian where appropriate.

## Cost rule
The owner wants near-zero running cost. Deterministic Python first; call an AI provider only when rules cannot do the job. Every AI call goes through the budget guard (BACKLOG T-005): cache identical requests, cap calls/tokens per day, degrade gracefully. Default provider stays Gemini (free tier).

## Agents
Roles live in `.claude/agents/` (implementer, reviewer, db-guardian). One bounded task per agent; no concurrent edits to the same files or schema; the reviewer approves before a PR is marked ready. Limits: at most 2 retries per failing check, then log the blocker in `docs/PROGRESS.md` and move to the next ready task. Pass only the context a task needs. Do not adopt agent frameworks (CrewAI, LangChain, etc.).

## Working loop
1. Read `docs/PROGRESS.md` and `docs/decisions/open-decisions.md`; pick the earliest unblocked task in `docs/BACKLOG.md`.
2. State scope, risk and acceptance criteria. Implement the smallest coherent change on a task branch.
3. Run tests and review the diff for unrelated changes, secrets, deletions and unsafe migrations.
4. Push the branch (Ship tests and merges it); confirm the run result with `gh run list`, and update `docs/PROGRESS.md` and the backlog with evidence.
5. Continue, or stop when a real decision or blocker needs the owner.

**Stop and ask** if an action could irreversibly delete or corrupt data, needs a production migration or deploy change, needs missing credentials, hits conflicting requirements, shows corruption or a security problem, cannot identify the authoritative schema, or hinges on a product trade-off.

## Status reporting
Keep these states separate and claim only what evidence shows: Implemented, Tested (actual output), Committed (hash), Pushed (verified on remote), Deployed, Verified live. Never say a command, migration or deploy succeeded because it was attempted. If a tool or permission is missing, say so and give the next step.

End each task with: Outcome, Files, Database, Verification, Git, Deployment, Remaining work, Next step.

Commit messages end with the Co-Authored-By trailer; PR descriptions end with the Claude Code line.
