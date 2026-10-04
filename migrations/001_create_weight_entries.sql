-- Create the daily weight measurement table.
CREATE TABLE weight_entries (
    id BIGSERIAL PRIMARY KEY,
    entry_date DATE NOT NULL UNIQUE,
    weight_kg NUMERIC(3,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
