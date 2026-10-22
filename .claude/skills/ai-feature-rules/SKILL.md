---
name: ai-feature-rules
description: Rules for any AI work in the app (provider, allowed features A1/A4, budget guard, context limits, validation, fallback, secrets). Use for any change in bulking_app/ai/ or to meal-suggestion or workout-idea features.
---

# AI feature rules (decisions D7, D11)

## Allowed uses (only these)
- **A1** meal suggestions / diet plan personalisation inside the deterministic skeleton.
- **A4** calisthenics workout ideas (pull-up bar and dip bar only) inside the deterministic plan.
Everything else is deterministic Python: logging, commands, totals, targets, check-ins, reminders, imports, trends. The only other AI touch point is the last-resort nutrition estimate (see `food-data-rules`), labelled and never auto-saved.

## Provider
- Claude API via the `anthropic` SDK. Default model: the current Haiku-class model, configurable via `AI_MODEL`; do not hardcode a non-Haiku default.
- Gemini code and the `google-genai` dependency are to be removed; OpenAI is already gone. No other providers, no agent frameworks.
- `ANTHROPIC_API_KEY` lives only in Streamlit secrets (app) and GitHub secrets (if a workflow ever needs it). Never read it, print it, log it, commit it, or ask the owner to paste it. Tests use fakes; CI never calls the real API.
- Remind the owner once, when the feature ships, to set a monthly spend limit in the Anthropic Console.

## Calls
- One structured request per feature per day: build the request, call once, cache the validated result for the day (persist the cache so restarts do not re-spend).
- Every call goes through `bulking_app/ai/budget.py`. Hard defaults: `AI_MAX_CALLS_PER_DAY=5`, a low daily token cap, plus a `max_tokens` limit on each request.
- Minimal context only: available foods, preference labels, remaining macro numbers, equipment, baseline ability numbers (e.g. max pull-ups). Never weight, height, age, body measurements, health, digestion or free-text notes.

## Output
- Request structured JSON (tool use or a JSON schema). Validate in Python: schema, known food ids only, quantities with units, numbers in sane ranges, totals recomputed in Python (never trust model arithmetic), exercises limited to the allowed equipment.
- Invalid or missing output → deterministic fallback (the skeleton plan), with a plain message. Callers catch `AIUnavailable`; an AI outage never blocks manual tracking.
- Show results labelled "AI suggestion"; the owner accepts, edits or dismisses. Nothing is saved without acceptance.
- No diagnosis, supplements, aggressive surpluses or training volumes beyond the skeleton's limits.

## Tests
Fake provider for: valid output, malformed JSON, unknown food id, over-budget, provider error, cache hit (no second call), context contains no forbidden fields.
