-- Create the daily recovery check-in table.
CREATE TABLE daily_checkins (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    checkin_date DATE NOT NULL UNIQUE,
    sleep_hours NUMERIC(3,1),
    soreness_level INTEGER,
    daily_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT daily_checkins_sleep_hours_range
        CHECK (sleep_hours IS NULL OR sleep_hours BETWEEN 0 AND 24),
    CONSTRAINT daily_checkins_soreness_level_range
        CHECK (soreness_level IS NULL OR soreness_level BETWEEN 1 AND 10)
);
