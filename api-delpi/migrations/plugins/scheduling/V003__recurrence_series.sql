-- Agendamento recorrente — série + vínculo nas reservas

CREATE TABLE IF NOT EXISTS scheduling.recurrence_series (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_code VARCHAR(2) NOT NULL,
    resource_id UUID NOT NULL,
    frequency VARCHAR(10) NOT NULL,
    interval_count INTEGER NOT NULL DEFAULT 1,
    series_start TIMESTAMPTZ NOT NULL,
    series_end TIMESTAMPTZ NOT NULL,
    title VARCHAR(200) NOT NULL,
    notes TEXT,
    booked_by_user_id VARCHAR(100) NOT NULL,
    booked_by_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_recurrence_series_resource
        FOREIGN KEY (resource_id)
        REFERENCES scheduling.resources (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_recurrence_series_branch CHECK (branch_code IN ('ES', 'SC')),
    CONSTRAINT ck_recurrence_series_frequency CHECK (frequency IN ('weekly', 'monthly')),
    CONSTRAINT ck_recurrence_series_interval CHECK (interval_count >= 1),
    CONSTRAINT ck_recurrence_series_time CHECK (series_end >= series_start)
);

CREATE INDEX IF NOT EXISTS idx_recurrence_series_resource
    ON scheduling.recurrence_series (resource_id);

ALTER TABLE scheduling.bookings
    ADD COLUMN IF NOT EXISTS recurrence_series_id UUID NULL
        REFERENCES scheduling.recurrence_series (id)
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_scheduling_bookings_series
    ON scheduling.bookings (recurrence_series_id)
    WHERE recurrence_series_id IS NOT NULL;
