# Daily Check-ins

## Purpose

The `daily_checkins` table stores one daily record of recovery-related measurements and contextual information that can influence the day's bulking plan.

It provides structured daily inputs for both AI planning and longer-term analytics.

## Schema

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER GENERATED ALWAYS AS IDENTITY` | Unique identifier for the check-in |
| `checkin_date` | `DATE` | The calendar day represented by the check-in |
| `sleep_hours` | `NUMERIC(3,1)` | Total hours of sleep associated with the day |
| `soreness_level` | `INTEGER` | Self-reported physical soreness on a 1–10 scale |
| `daily_notes` | `TEXT` | Context about the day's schedule or other relevant circumstances |
| `created_at` | `TIMESTAMPTZ` | Timestamp when the record was created |

## Constraints

- `id` is the primary key.
- `checkin_date` must be unique, allowing one daily check-in per day.
- `checkin_date` is required.
- `soreness_level`, when provided, must be between 1 and 10.
- `sleep_hours`, when provided, must be between 0 and 24.

## Data Usage

The table serves two primary purposes:

### AI Planning

Daily check-in information is provided to the AI as part of the context used to generate the day's personalized bulking plan.

### Analytics

The structured fields can be combined with data from other tables to analyze relationships between recovery, nutrition, workouts, and weight progression.

Examples include:

- Sleep duration over time
- Soreness trends
- Sleep and workout adherence
- Recovery patterns alongside weight progression

## Design Decisions

### Separate `checkin_date` from `created_at`

`checkin_date` represents the business date associated with the observation, while `created_at` represents when the database record was created.

This allows a historical check-in to be entered after the day it represents without losing the actual creation timestamp.

### Keep daily notes flexible

`daily_notes` stores contextual details that may help personalize the day's plan. It is a flexible text field rather than a set of narrowly defined columns, so relevant context can be captured without treating each note as a structured analytics measure.

### Keep measurements optional

Sleep duration and soreness can be recorded when available. The table permits a check-in when either measurement is unknown, while enforcing the documented ranges whenever a value is supplied.

## Migration

The table is created by `database/migrations/002_create_daily_checkins.sql`.
