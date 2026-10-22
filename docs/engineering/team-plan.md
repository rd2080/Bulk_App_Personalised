# Team plan

How the multi-agent build runs. Owner-confirmed 2026-10-22. Product rules live in `CLAUDE.md`; tasks in `docs/BACKLOG.md`; decisions in `docs/decisions/open-decisions.md`.

## Roles
| Role | Agent file | Model / effort | Does | Never |
|---|---|---|---|---|
| Lead | main session | Sonnet / medium | Picks tasks, spawns agents, merges results, reports to owner, runs the budget governor | Writes large features itself while a wave runs |
| schema | `.claude/agents/schema.md` | Sonnet / high | Migrations, repositories for new tables, DB roles, `migration-procedure` | Destructive SQL without owner approval; prints rows |
| builder | `.claude/agents/builder.md` | Sonnet / medium | Services, pages, scripts, tests for one task | Edits files it does not own; touches migrations |
| reviewer | `.claude/agents/reviewer.md` | Sonnet / medium | Reviews one branch's diff, one round | Edits files |
| ci-watcher | `.claude/agents/ci-watcher.md` | Haiku / low | Waits for one Ship run, one-line pass/fail | Polls in repeated turns |
| docs-writer | `.claude/agents/docs-writer.md` | Haiku / low | PROGRESS/BACKLOG/how-to edits from given facts | Invents results |

## File ownership
- `database/migrations/`, `docs/database/`, `database/roles/`: schema only, one task at a time.
- `bulking_app/repositories/<table>.py`: the schema task that creates the table; later edits by the owning builder task.
- `bulking_app/services/<feature>.py`, `pages/<feature>`, `tests/test_<feature>.py`: the builder task that lists them in BACKLOG "Owns".
- `bulking_app/ai/`, `requirements.txt`, `.env.example`: T-060 only.
- `.github/workflows/`, `CLAUDE.md`, `.claude/`, `docs/engineering/`: lead only.
- `docs/PROGRESS.md`, `docs/BACKLOG.md` status lines: lead or docs-writer, after merges.
Two tasks that own the same file are never in the same wave.

## Wave order
| Wave | Tasks (parallel where files are disjoint) | Mode |
|---|---|---|
| 0 | Phase 0 setup (this file, skills, settings) | lead only |
| 1 | T-011 (schema) → then T-012 + T-013 (builders) + T-003 | team of up to 3 after T-011 merges |
| 2 | T-020 (docs-writer) + T-014 (builder); then T-021 (schema) | subagents |
| 3 | T-022 + T-023 (builders); T-030 (schema) | team of 3 |
| 4 | T-031 (builder, high) then T-032 + T-033 | subagents |
| 5 | T-040 (schema) then T-041 (builder) | subagents |
| 6 | T-050 (schema then UI), T-051 (schema), T-052 (builder) | sequential schema, builder in parallel |
| 7 | T-060 then T-061 + T-062 | team of 2 + reviewer |
| 8 | T-070 then T-071 | subagents |
T-004 (migration runner) slots in before the first production migration if time allows; otherwise migrations are applied with the Neon tools per the skill.

## Token rules (contract for all runs)
1. Default to the lead plus subagents. Use an agent team only for a wave whose tasks own disjoint files and are all ready, max 3 teammates (4 only for a schema + services + UI + reviewer wave). Spawn them when the wave starts and shut each down the moment its task is done.
2. Spawn prompts are under 300 words: task id, owned files, acceptance criteria, which docs to read. Agents never read the whole docs folder, worktrees, lockfiles or generated files; they grep or read only the files they own.
3. Models: Sonnet for design and code, Haiku for docs, formatting, CI watching and log reading. Effort low for mechanical work, medium by default, high only for migrations, the target formula, health rules and AI output validation. Never max.
4. Output discipline: run tests as `python -m pytest -q -x --tb=short | tail -40`. Never paste logs into conversation. Agent final reports are 150 words or less in the `report-format` skill.
5. Waiting: never poll in repeated turns and never use `/loop`. Wait for CI with one background command (`until ... gh ... completed`) or the ci-watcher.
6. Retries: max 2 per failing check, one review round per branch, and a teammate that passes about 40 tool calls on one task stops and reports the blocker instead.
7. Context: `/clear` between unrelated tasks, `/compact` with instructions only if a task must continue. One bounded task per spawn.
8. Budget governor: run `/usage` at the start of every wave and after every merged task. At about 70% of the 5-hour window or 80% of the weekly allowance (or the daily spend the owner sets): finish the current task, push, write a 5-line handoff in `docs/PROGRESS.md`, shut down teammates and stop starting new work. Next work is picked up after the reset. If a limit hits mid-task, choose the option to wait and continue after the reset.
9. Plan limits are shared with the owner's normal Claude chat. Heavy waves should run when the owner is away.
10. Deterministic first: never use an agent to do what a script can (formatting, migration apply, file moves).

## Standing run procedure (each wave)
1. Check usage (`/usage`); apply rule 8. Read `docs/PROGRESS.md` (latest entry only) and the wave's BACKLOG entries.
2. For each ready task: create `claude/<task-id>-<slug>` (worktree per teammate), spawn the role with a <300-word prompt.
3. On a task report: reviewer on that branch's diff (one round) → fix if needed → push via `ship-and-verify` (schema tasks: `migration-procedure` first, push with `[hold]` until production is migrated).
4. ci-watcher confirms the Ship run; lead confirms the merge commit on `origin/main`.
5. docs-writer updates `docs/PROGRESS.md` (5 lines) and BACKLOG status. Check usage again.
6. Report to the owner in plain language (`report-format`), only with owner actions they must take.

## Watching a team in tmux
- Start with `scripts/team-tmux.sh` (session `bulk-team`; run it inside an existing tmux session to use that one). The lead runs in pane 0.
- `teammateMode` is `tmux` in `.claude/settings.json`: each teammate the lead spawns opens in its own split pane and closes when the lead shuts it down. Subagents (lead plus subagents mode) do not get panes; only agent-team teammates do.
- Click a pane to focus it and type to steer that teammate directly; scroll with the mouse. Settings load at startup, so restart `claude` after changing them.
- Panes cost nothing extra; tokens do. Rule 1 still applies: max 3 teammates (4 for schema + services + UI + reviewer).

## Stable releases to main
The owner tests on the live app, so agents may push to `main` directly once a build is stable. Before any direct push: full tests pass locally, the app starts and the changed pages render, required migrations are applied (`migration-procedure`), and the reviewer has seen the diff. Fast-forward pushes only, never force. Report exactly what was verified (`report-format`). If any check is missing, use the Ship PR path instead.

## Owner-only actions (agents give click-by-click steps, never ask for secret values in chat)
- Set GitHub/Streamlit secrets (`ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `REMINDER_DATABASE_URL`).
- Set a monthly spend limit in the Anthropic Console.
- Make the repo private (D10). Approve destructive DB changes and the data wipe.
