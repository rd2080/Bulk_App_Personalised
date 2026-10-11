# Phase 2 — Daily Meal Plan Management

## Scope

The Daily Meal Plan Streamlit page maintains one plan per date. A plan can contain any number of meals. Each meal has a category (breakfast, morning snack, lunch, afternoon snack, dinner, or other), a required name, optional details, and a stable display position. Users can add, edit, remove, and reload meals for a selected date.

This is manual planning only. Speech transcription is not connected to meal fields; command interpretation, AI calls, nutrition calculations, and actual-consumption tracking are out of scope.

## Data flow

```text
Streamlit Daily Meal Plan page
        ↓
Meal plan repository
        ↓
Neon connection helper
        ↓
daily_meal_plans → planned_meals
```

`daily_meal_plans.plan_date` is unique. `planned_meals.plan_id` references its plan with `ON DELETE CASCADE`; meal edits and deletes are restricted to the selected date. Adding a meal creates the date's plan if needed. Existing check-in, food inventory, recipe, profile, and weight tables are not modified.

## Schema and migration

Migration `008_create_daily_meal_plans.sql` additively creates the plan header and meal rows plus an ordering index. Apply this migration to Neon before deploying the application code if it is not already applied. The migration is idempotent and does not delete or rewrite existing data.

## Implementation

Persistence and input validation live in `bulking_app/repositories/meal_plan.py`; the Streamlit page is `pages/4_Daily_Meal_Plan.py`. Repository tests cover date handling, validation, insertion, updates scoped to the selected plan, listing, and deletion.
