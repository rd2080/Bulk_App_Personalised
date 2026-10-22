---
name: ship-and-verify
description: How to push a task branch, wait for CI without polling, and confirm the Ship workflow merged it. Use whenever a branch is ready to ship.
---

# Ship and verify

Pipeline (`.github/workflows/ship.yml`): push `claude/<task-id>-<slug>` → CI tests → PR opened → squash-merge into `main` → Streamlit Cloud redeploys. `[hold]` anywhere in the head commit message runs tests without merging.

## Before pushing
1. `git status` and `git diff --stat`: only the task's files changed; no secrets, no `.env`, no personal data, no real rows.
2. `python -m pytest -q -x --tb=short | tail -40` passes locally (if Postgres-only tests skip locally, say so).
3. Commit message: `<task-id>: <what changed>`; body ends with the Co-Authored-By trailer.

## Push and wait (one background command, never repeated polling)
```bash
git push -u origin HEAD
sha=$(git rev-parse HEAD)
until gh run list --commit "$sha" --workflow Ship --json status --jq '.[0].status' | grep -q completed; do sleep 30; done
gh run list --commit "$sha" --workflow Ship --json conclusion,databaseId,url --jq '.[0]'
```
Run the wait in the background (or hand it to the `ci-watcher` agent) and continue other work or end the turn. Do not use `/loop` or repeated turns.

## Confirm
- `conclusion: success` and the PR shows merged: `gh pr list --head <branch> --state merged --json number,mergeCommit`.
- `git fetch origin && git log origin/main -1 --oneline` shows the squash commit.
- On failure: `gh run view <id> --log-failed | tail -60` (never paste the whole log). Fix and push again; max 2 retries, then log the blocker in `docs/PROGRESS.md` and stop.

## Report
State only what evidence shows: Committed (hash), Pushed, CI (run id + result), Merged (PR number), Deployed (only if the live app was checked).
