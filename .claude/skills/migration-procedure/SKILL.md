---
name: migration-procedure
description: Step-by-step procedure for any schema change, including applying an additive migration to Neon production (backup branch, claude-dev test, apply, verify). Use for every migration and any production database step.
---

# Migration procedure (decision D9)

Neon project `ancient-bonus-73336167`. Branches: `production` (live), `claude-dev` (agent testing, holds copies of real rows). Never print, export or commit row contents from either branch.

## 0. Classify the change
- **Additive** (new table, new nullable column, new index, new constraint that existing rows already satisfy): this procedure applies; no owner approval needed.
- **Anything else** (DROP, DELETE, UPDATE of existing rows, type changes, renames, NOT NULL on existing columns, data wipe): STOP and ask the owner, stating exactly what changes and the recovery path. The data wipe additionally needs: owner says new tables are ready, a fresh backup branch, and one final confirmation.

## 1. Write the migration
- New file `database/migrations/NNN_<slug>.sql`, next number, never edit an existing file.
- Rerun-safe (`IF NOT EXISTS`, guarded `DO` blocks). Wrap in a transaction where possible.
- Update `docs/database/schema.md` and `database/migrations/README.md` in the same branch. Note the recovery path.
- Tests with synthetic data; CI applies every migration to a throwaway Postgres.

## 2. Test on claude-dev
- Inspect the live `claude-dev` schema first (table/column metadata only, never rows) and compare with `docs/database/schema.md`. Report mismatches.
- Apply the file to `claude-dev`. Re-inspect the schema; confirm the new objects exist. Apply it a second time to prove rerun safety.

## 3. Back up production
- Create a Neon branch from `production` named `backup-<YYYYMMDD>-<migration-number>`. Confirm it exists before continuing. Do not delete old backup branches without owner approval.

## 4. Apply to production (before merging the code that needs it)
- Push the code branch with `[hold]` in the head commit so CI runs without merging.
- When CI is green, apply exactly the tested file to `production`.
- Verify with metadata queries only (`information_schema` / `pg_catalog`): objects exist, row counts of existing tables unchanged (counts are fine to report; values are not).

## 5. Merge and record
- Push a follow-up commit without `[hold]` (or re-push) so Ship merges the code. See `ship-and-verify`.
- Record in `docs/PROGRESS.md`: migration number, backup branch name, applied-on-claude-dev and applied-on-production evidence, CI run id.

## If something fails
- Failure on `claude-dev`: fix the file (it was never applied to production), retry at most twice.
- Failure on `production` mid-apply: stop, do not retry blindly, do not merge the code. Report the error and the backup branch name to the owner; restoring from backup needs the owner's approval.
