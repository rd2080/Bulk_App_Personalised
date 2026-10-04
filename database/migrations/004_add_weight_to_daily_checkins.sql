-- Store the complete morning check-in alongside the existing daily measurements.
-- Nullable for compatibility with any historical check-ins created before Phase 2.
ALTER TABLE daily_checkins
    ADD COLUMN weight_kg NUMERIC(5,2),
    ADD CONSTRAINT daily_checkins_weight_kg_range
        CHECK (weight_kg IS NULL OR weight_kg BETWEEN 25 AND 350);
