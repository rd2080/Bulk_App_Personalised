-- NUMERIC(3,2) allows only one digit before the decimal and rejects normal
-- body weights. Widen to two decimal places with room for the Phase 2 range.
ALTER TABLE public.weight_entries
    ALTER COLUMN weight_kg TYPE NUMERIC(5,2)
    USING weight_kg::NUMERIC(5,2);

ALTER TABLE public.weight_entries
    ADD CONSTRAINT weight_entries_weight_kg_range
    CHECK (weight_kg BETWEEN 25 AND 350);
