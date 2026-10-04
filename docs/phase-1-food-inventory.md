# Phase 1 — Food Inventory

## Goal

Phase 1 implements the first complete application slice: a dedicated Food Inventory page backed by the existing Neon PostgreSQL `food_inventory` table.

## User workflow

1. Open **Food Inventory**.
2. Add a food with an availability type and optional quantity/unit.
3. Review available foods as a checklist-like list.
4. Mark an item unavailable when it is out of stock or should not be considered by meal planning.
5. Mark it available again after buying/restocking it.
6. Edit the food name, availability type, quantity, or unit when needed.

The inventory becomes the base context for future meal planning. Phase 1 does not generate meal plans yet.

## Data flow

```text
Streamlit Food Inventory page
        ↓
Food inventory repository
        ↓
Neon PostgreSQL
        ↓
food_inventory
```

The page contains no SQL. Database operations live in `bulking_app/repositories/food_inventory.py`, while `bulking_app/neon.py` owns the database connection.

## Availability model

- `always_available`: routinely available; quantity may be omitted.
- `stock_tracked`: quantity can represent current stock on hand.
- `on_demand`: can be obtained when needed; quantity may be omitted.

`is_available` is deliberately separate from `quantity`. An item can have an unknown quantity and still be available, or retain a quantity while being temporarily marked unavailable.

## Database configuration

The application checks the local `DATABASE_URL` environment variable first, then Streamlit Secrets.

- **Local development:** set `DATABASE_URL` in your shell or local environment.
- **Streamlit Cloud:** open the app's **Settings → Secrets** and add the following TOML entry, replacing the placeholder with the Neon PostgreSQL connection string:

```toml
DATABASE_URL = "your-neon-postgresql-connection-string"
```

Save the secrets and restart/redeploy the app if it does not restart automatically. Never commit the connection string to GitHub or put it in source files.

If neither the environment variable nor Streamlit Secret is configured, the app reports that `DATABASE_URL` is missing and tells you where to configure it.

## Scope boundary

Phase 1 intentionally does not implement analytics, meal planning, meal logging, or the morning check-in. Quantity is editable inventory information; consumption tracking belongs to the later Meal Log phase.
