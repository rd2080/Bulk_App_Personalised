# AI scope (PROPOSED, awaiting owner decision D11)

Owner direction (2026-10-21): drop the OpenAI SDK; re-scope AI to where it is genuinely worth it. AI is not for forms or anything deterministic code can do.

Provider: Gemini free tier only (OpenAI removed). Every call goes through the budget guard (`bulking_app/ai/budget.py`). AI output is advisory and never changes plans, logs or inventory without explicit acceptance. An AI outage never blocks manual tracking.

## Stays deterministic Python (no AI)
Form filling, validation, voice/text meal commands, meal logging, inventory deduction, unit handling, nutrition totals, targets arithmetic, weight/trend calculations, reminders, CSV import/export.

## Candidate AI uses (owner to pick)
| ID | Use | Why AI helps | Context sent |
|---|---|---|---|
| A1 | Meal suggestions from current stock, recipes and preferences | Combinatorial and creative; hard to hand-write rules | Compact list of available foods, recipe names, preference labels |
| A2 | Free-text food to a draft food/recipe entry (nutrition unknown stays unknown) | Saves typing; always shown as an editable draft labelled AI-generated | The text the owner typed |
| A3 | Weekly written review of logged trends | Narrative summary only; numbers computed in Python | Aggregated weekly numbers, no notes |
| A4 | Workout session ideas (needs D4) | Variety | Equipment and goal labels |

Recommendation: ship A1 first, A2 second; defer A3 and A4. Drop the "optional Claude provider" task (T-051) unless asked.

Not in scope: diagnosis, supplement advice, aggressive targets, or conclusions about digestion.
