# Bulk App — Claude Code project rules

Personal, single-user, phone-first bulking assistant for the owner only. Streamlit UI, Neon PostgreSQL, Streamlit Cloud deploys from `main`. No commercial purpose, no multi-user or auth work without owner approval. The owner is non-technical and only texts the agent: keep updates short and plain.

Read on demand, not every session: `docs/PROGRESS.md` (latest status), `docs/BACKLOG.md` (prioritised plan), `docs/decisions/open-decisions.md` (owner decisions), `docs/engineering/team-plan.md` (roles, waves, token contract). Detailed procedures are skills in `.claude/skills/` (load only when the task needs them):
- `migration-procedure`: any schema change or production database step
- `ship-and-verify`: pushing a branch and confirming CI and the merge
- `report-format`: the end-of-task report and agent report shape
- `ai-feature-rules`: any work in `bulking_app/ai/` or on AI features A1/A4
- `food-data-rules`: food database, recipes, nutrition values, imports

## Source of truth (when sources disagree)
1. The owner's current instruction. 2. Verified live behaviour/schema. 3. Decisions and requirements in `docs/`. 4. Code and tests together. 5. Git history. 6. Older notes.
Document any mismatch; never silently redefine a requirement because the code differs.

## Product
A complete bulking assistant for one person:
- log what was eaten; calorie and protein tracking; daily target vs progress
- "what to eat next and when", fitted to the day's plan
- diet plan creation (weekly repeatable meal pattern first)
- calisthenics plan creation and logging (pull-up bar and dip bar only)
- exercise tracking and an improvement tracker
- daily light check-in, weekly Saturday check-in, morning motivation and reminder

The owner is a beginner at meal planning and training. Pattern: a deterministic, conservative skeleton; AI personalises inside it; Python validates; the owner accepts or edits. Recommend a dietitian/trainer review of the first plans.

## Non-negotiables
- Never commit secrets. Never read, print or ask the owner to paste API keys or `.env` values. Credentials live in `.env` locally, Streamlit Cloud secrets and GitHub secrets only.
- No personal data in the repo, even though it is private: no weight, height, age, health or digestion notes, or diet specifics in code, tests, fixtures, docs, logs or PRs. Synthetic test data only. Personal values live only in Neon.
- Database (Neon project `ancient-bonus-73336167`): develop and test on branch `claude-dev`, which holds copies of real rows: never print or commit rows. Additive migrations may go to `production` only via the `migration-procedure` skill (passed on `claude-dev`, Neon backup branch first, applied before merging the code that needs them). Anything that deletes or alters existing data needs the owner's explicit approval.
- Data wipe: only when the owner says the new tables are ready, after a backup, with one final confirmation. Until then keep existing data. After the wipe, reset `claude-dev` from production.
- Never edit an existing migration. Add a new numbered additive file; update `docs/database/schema.md` and `database/migrations/README.md` in the same PR.
- Git: never push to `main`, force-push, delete branches or rewrite shared history. Work on `claude/<task-id>-<slug>`. Pushing runs Ship: tests, auto PR, squash-merge (`[hold]` in the head commit message skips the merge). Failing tests leave the branch unmerged: fix, never bypass CI. Merged code redeploys the live app.
- SQL lives only in `bulking_app/repositories/` (parameterised, transactional). Pages stay thin; logic lives in `bulking_app/services/`.
- Every change needs tests in `tests/` with synthetic data, and CI must pass.

## Product rules
- Planned is not consumed. Plans never create or alter consumption logs; nothing counts as eaten without an explicit logging action.
- No hardcoded dietary rules, targets, preferences or routine in code or prompts; read them from profile/preferences in Neon. Old values are starting context: show their age and let the owner correct them.
- Never invent food, stock, nutrition values, completed actions or successful writes. Unknown nutrition stays unknown, never zero. Quantities carry units; incompatible units are never summed. Label estimates, calculations and AI suggestions apart from user-entered facts.
- Targets (D3) are suggested by a deterministic formula, never AI: show assumptions, label them estimates, use a conservative surplus, show a clinician/dietitian note, owner can override. Body measurements never go to an AI provider.
- Check-ins: daily light (sleep, soreness, optional weight); weekly on Saturday (weight, progress), stored at weekly level. One weigh-in is not a trend. Cadence and fields are configurable.
- Inventory changes are idempotent (a retried command must not deduct twice).
- AI is limited to A1 (meal suggestions/diet plans) and A4 (calisthenics workout ideas), on Claude, via the budget guard. AI output is validated and advisory, never auto-saved, and an AI outage never blocks manual tracking. Explicit commands ("I ate three eggs") use deterministic logic. Details: `ai-feature-rules` skill.
- Health: no diagnosis, no supplement prescriptions, no aggressive targets. Digestion/appetite entries are observations, never conclusions. Recommend a clinician or dietitian where appropriate.
- Reminders: Telegram bot sent by a scheduled GitHub Actions workflow (cron is UTC; owner is UTC+5:30). Messages are deterministic, minimal, no health detail. The workflow uses a read-only database role.

## Cost rule
Near-zero running cost. Deterministic Python first; AI only where rules cannot do the job. Every AI call goes through the budget guard (low hard defaults: 5 calls/day, token cap), one structured request per feature, generated once per day and cached.

## Token rules (how agents work)
Full contract: `docs/engineering/team-plan.md`. Essentials:
- Sonnet for design and code, Haiku for docs, formatting, CI watching and log reading. Effort medium by default, low for mechanical work, high only for migrations, the target formula, health rules and AI output validation. Never Opus or max unless the owner says so.
- Lead plus subagents by default; an agent team only for a wave of ready tasks with disjoint files, max 3 teammates (4 for schema + services + UI + reviewer).
- Spawn prompts under 300 words. Agents read only the files they own; never the whole docs folder, worktrees, lockfiles or generated files.
- Tests: `python -m pytest -q -x --tb=short | tail -40`. Never paste full logs. Agent reports are 150 words or less (`report-format` skill).
- Never poll CI in repeated turns, never `/loop`: one background wait command or the `ci-watcher` agent.
- Max 2 retries per failing check, one review round per branch, stop and report after about 40 tool calls on one task.
- Check plan usage at the start of every wave and after each merge; at about 70% of the 5-hour window or 80% weekly: finish the current task, push, write a 5-line handoff in `docs/PROGRESS.md`, stop.
- Deterministic first: never use an agent for what a script can do.

## Stop and ask
Only when an action could irreversibly delete or corrupt data, alters or deletes existing production data, changes deploy configuration, needs missing credentials or a secret the owner must set, hits conflicting requirements, shows corruption or a security problem, cannot identify the authoritative schema, or hinges on a product trade-off not covered by `docs/decisions/`. Otherwise use the recorded decision or recommended default and proceed.

## Status reporting
Keep these states separate and claim only what evidence shows: Implemented, Tested (actual output), Committed (hash), Pushed (verified on remote), Deployed, Verified live. Never say something succeeded because it was attempted. End each task with the `report-format` skill.

Commit messages end with the Co-Authored-By trailer; PR descriptions end with the Claude Code line.
