# Open owner decisions

Agents proceed with the recommended default unless the owner objects in PR review, except where a decision is marked blocking.

| ID | Decision | Recommended default | Blocks |
|---|---|---|---|
| D1 | Meal-log model: date boundary, edits/deletes, plan linking | Local-time date + optional time; edits keep `updated_at`; deletes are soft with a visible history; link to a plan only when the owner picks a match | T-010..T-014 (proceeds on default) |
| D2 | Where configurable preferences live (eggs, exclusions, shakes, budget, equipment, timing) | New additive `user_preferences` table; leave `user_profile` at its ten agreed fields | T-030 (blocking) |
| D3 | How intake targets are set | Owner-entered targets with visible assumptions; no auto-escalation; show a clinician/dietitian note. Owner should also confirm the profile's weight, height and age are current | T-022 (blocking) |
| D4 | Workout scope | Plan and log calisthenics sessions with pull-up/dip bar only | T-052 (blocking) |
| D5 | Reminders: channel, runtime, quiet hours | In-app only first; no background delivery until a scheduler is chosen | T-060 (blocking) |
| D6 | CSV export scope (foods, recipes, plans, logs) | Foods and recipes first, round-trip tested | T-061 (blocking) |
| D7 | AI provider, consent and what context may be sent | Gemini free tier; compact profile summary only; user reviews before saving | T-050 |
| D8 | Legacy SQLite code | Remove if no live call site, with a test update | T-002 (proceeds on default) |
| D9 | Production migrations | Owner does not run commands and wants fast, hands-off merging (2026-10-21). Proposed: agents apply ADDITIVE migrations to production themselves after passing on `claude-dev`, taking a Neon backup branch first and applying BEFORE merging the code that needs them. Destructive changes still need explicit approval. Awaiting the owner's yes | all schema tasks (blocking until confirmed) |
| D10 | Repo visibility | Make the repository private if it will hold anything personal | none |
