# Food Inventory

## Purpose

The `food_inventory` table stores foods that may be considered when planning meals for the bulking app. It captures each food's availability category and, when useful, its current quantity and unit.

## Schema

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER GENERATED ALWAYS AS IDENTITY` | Unique identifier for the food item |
| `food_name` | `TEXT` | Name of the food |
| `availability_type` | `TEXT` | How the food is made available: `always_available`, `stock_tracked`, or `on_demand` |
| `quantity` | `NUMERIC(8,2)` | Optional current quantity for a food item |
| `unit` | `TEXT` | Optional unit associated with the quantity, such as grams, pieces, or servings |
| `is_available` | `BOOLEAN` | Whether the food is currently available to use; defaults to `TRUE` |
| `created_at` | `TIMESTAMPTZ` | Timestamp when the record was created |
| `updated_at` | `TIMESTAMPTZ` | Timestamp for the most recent application-recorded update; defaults to creation time |

## Constraints

- `id` is the primary key.
- `food_name` and `availability_type` are required.
- `availability_type` must be `always_available`, `stock_tracked`, or `on_demand`.
- `quantity`, when provided, must be zero or greater.
- `is_available` is required and defaults to `TRUE`.
- `created_at` and `updated_at` are required and default to `NOW()`.

## Data Usage

Meal planning can use this table to distinguish foods that are routinely available, foods whose stock is tracked, and foods that can be obtained on demand.

For stock-tracked items, the quantity and unit give the planner practical context about what is currently on hand. The `is_available` flag gives the app a simple way to mark an item unavailable without deleting its record.

## Design Decisions

### Keep availability categories simple

The `availability_type` check constraint keeps the V1 categories to three values: `always_available`, `stock_tracked`, and `on_demand`. This gives the planner useful distinctions without introducing a separate category table.

### Keep quantity and unit flexible

Quantity and unit are optional because not every availability category needs a measured stock amount. The non-negative check prevents a stored quantity from dropping below zero; the unit remains text so the app can use practical labels such as grams, pieces, or servings.

### Separate availability from stock quantity

`is_available` records whether the item should currently be treated as available. Quantity can remain unknown or recorded separately, avoiding assumptions that every food is tracked by amount.

### Keep timestamps straightforward

Both timestamps default to the time the row is created. The application should update `updated_at` when it changes a record; the schema does not add a trigger for this V1 table.

## Review

The V1 design keeps one row per food item and includes only the fields needed to identify it, describe how it can be obtained, record optional stock, and track basic availability and timestamps. The three allowed availability types and non-negative quantity rule are enforced by PostgreSQL.

The corresponding migration is `database/migrations/003_create_food_inventory.sql`.
