# AI scope (DECIDED, D7 and D11, 2026-10-22)

AI is used only where deterministic code cannot do the job, inside a deterministic, conservative skeleton: AI personalises, Python validates, the owner accepts or edits. Implementation rules: `.claude/skills/ai-feature-rules/SKILL.md`.

Provider: Claude API, Haiku-class model by default, through the budget guard (`bulking_app/ai/budget.py`, `AI_MAX_CALLS_PER_DAY=5` and a token cap). Gemini code and `google-genai` are to be removed (backlog item 6); OpenAI is already gone.

## In scope
| ID | Use | Context sent (minimal) |
|---|---|---|
| A1 | Meal suggestions and diet plan personalisation within the weekly meal pattern | Available foods, preference labels, remaining macro numbers |
| A4 | Calisthenics workout ideas (pull-up bar and dip bar only) within the skeleton plan | Equipment, baseline ability numbers (e.g. max reps) |

One structured request per feature, generated once per day and cached. Output is validated JSON; invalid output or an outage falls back to the deterministic skeleton.

Last-resort nutrition estimate for a food with no data source is allowed only as an editable draft labelled "AI estimate, unverified", never auto-saved, through the same guard.

## Dropped
A2 (free text to draft food entry) and A3 (weekly written review). T-051 (optional second provider) is replaced by the switch to Claude.

## Stays deterministic Python (no AI)
Meal logging and commands, inventory, units, nutrition totals, target formula, next-meal timing, check-ins, trends, improvement tracker, reminders and motivation messages, imports.

## Never sent to a provider
Weight, height, age, body measurements, health, digestion or appetite notes, free-text notes.

Not in scope: diagnosis, supplement advice, aggressive targets, conclusions about digestion.
