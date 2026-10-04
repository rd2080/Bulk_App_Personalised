CREATE TABLE food_inventory (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    food_name TEXT NOT NULL,
    availability_type TEXT NOT NULL,
    quantity NUMERIC(8,2),
    unit TEXT,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT food_inventory_availability_type_check
        CHECK (
            availability_type IN (
                'always_available',
                'stock_tracked',
                'on_demand'
            )
        ),

    CONSTRAINT food_inventory_quantity_check
        CHECK (quantity IS NULL OR quantity >= 0)
);
