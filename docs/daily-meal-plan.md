# Phase 2 — Daily Meal Plan Management

## Scope

The Daily Meal Plan Streamlit page maintains one plan per date. A plan can contain any number of meals. Each meal has a category (breakfast, morning snack, lunch, afternoon snack, dinner, or other), a required name, optional details, and a stable display position. Users can add, edit, remove, and reload meals for a selected date.

Phase 3 adds a deterministic command-processing path to the Voice Input page. It can create an initial plan from labeled meal descriptions and apply explicit add, replace, and remove commands. It does not call an AI provider. Direct manual editing remains available.

## Data flow

```text
Voice transcription / reviewed text
        ↓
Deterministic command parser (no LLM)
        ↓
Validation and ambiguity checks
        ↓
Existing meal-plan repository
        ↓
Neon connection helper
        ↓
daily_meal_plans → planned_meals
```

`daily_meal_plans.plan_date` is unique. `planned_meals.plan_id` references its plan with `ON DELETE CASCADE`; meal edits and deletes are restricted to the selected date. Adding a meal creates the date's plan if needed. Existing check-in, food inventory, recipe, profile, and weight tables are not modified.

## Schema and migration

Migration `008_create_daily_meal_plans.sql` additively creates the plan header and meal rows plus an ordering index. No new migration is required for Phase 3. The parser uses the existing `planned_meals.meal_type`, `meal_name`, and `description` columns. Apply migration 008 to the target Neon database if it has not already been applied.

## Implementation

- Persistence and validation: `bulking_app/repositories/meal_plan.py`
- Daily manual editing: `pages/5_Daily_Meal_Plan.py`
- Deterministic command parser/application: `bulking_app/meal_commands.py`
- Voice input and command confirmation: `pages/4_Voice_Input.py`

The parser supports labeled meal descriptions and explicit add/replace/remove instructions. Ambiguous snack references and duplicate meal slots prompt clarification. Meal contents remain text; this phase does not parse ingredients or calculate nutrition.
