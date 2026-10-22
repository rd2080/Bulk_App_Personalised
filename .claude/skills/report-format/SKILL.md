---
name: report-format
description: The required shape for end-of-task reports to the owner and for agent/teammate final reports (150 words or less). Use at the end of every task.
---

# Report format

## Agent / teammate final report (to the lead), 150 words or less
```
Task: <id> — <done | blocked | partial>
Files: <changed files>
Tests: <passed/failed counts from the actual run, or "not run" + why>
Git: <branch> @ <short hash>, pushed: yes/no
Blocker: <one line or "none">
Next: <one line>
```
No logs, no diffs, no restating the task.

## Lead report to the owner (plain language, short)
- **Outcome**: what now works, in one or two sentences a non-technical reader understands.
- **Files**: main files touched (count if many).
- **Database**: none / migration NNN on claude-dev / on production (with backup branch name).
- **Verification**: tests (counts), CI run result, live check if done.
- **Git**: commit hash, PR number, merged yes/no.
- **Deployment**: redeployed / not verified live.
- **Remaining work** and **Next step**: one line each.
- **Owner action needed**: only if there is one, as click-by-click steps.

Claim only what evidence shows. Never say "deployed" or "applied" because it was attempted.
