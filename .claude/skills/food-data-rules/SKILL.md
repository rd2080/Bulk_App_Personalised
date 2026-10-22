---
name: food-data-rules
description: Rules for the food database (IFCT 2017), recipes, nutrition computation, units, imports and gaps. Use for any work on foods, recipes, nutrition values, meal logging totals or CSV import.
---

# Food data rules (decision D6 and food-data decisions)

## Sources, in order
1. **IFCT 2017** (Indian Food Composition Tables, 542 foods, with cooking yield factors) as the base for Indian home-cooked food. Use the older MIT-licensed machine-readable version where possible; record the exact source, version and licence in `docs/data/food-sources.md` and keep the licence file with any imported data. If only a non-MIT version is available, stop and ask before committing data.
2. **Recipes**: nutrition computed in Python from ingredients (raw weights × IFCT values, cooking yield applied for cooked weight, per-serving scaling). Never typed totals when ingredients are known.
3. **Gaps**: manual entry by the owner, or Open Food Facts for packaged items (store barcode/product id and fetch date).
4. **Last resort**: AI nutrition estimate, labelled "AI estimate, unverified", shown as an editable draft, never auto-saved.

## Values
- Unknown stays unknown (NULL), never zero. Totals that include unknowns show "incomplete" with the count of unknown items.
- Every value carries provenance: `ifct`, `recipe_computed`, `off` (Open Food Facts), `manual`, `ai_estimate`.
- Quantities carry units. Convert only with explicit factors (g, ml, piece with a per-piece weight). Never sum incompatible units.
- Per-100 g basis in storage; scale at display/compute time. Round only for display.

## Imports
- CSV is for the first food import only (IFCT seed and the owner's initial list), via an idempotent script (rerun does not duplicate). Ongoing additions go through the app.
- The IFCT dataset itself is public reference data and may be committed; the owner's personal food list and quantities may not (they live in Neon).
- Imports into production follow `migration-procedure` for any schema part; data seeding is additive and idempotent.

## Tests
Synthetic foods only. Cover: recipe computation with yield, unknown propagation, unit mismatch rejection, idempotent import, provenance labels.
