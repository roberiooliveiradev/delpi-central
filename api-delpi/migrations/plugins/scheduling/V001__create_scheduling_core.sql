-- Central de Agendamento — schema scheduling

CREATE TABLE IF NOT EXISTS scheduling.resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_code VARCHAR(2) NOT NULL,
    name VARCHAR(200) NOT NULL,
    resource_type VARCHAR(30) NOT NULL,
    description TEXT,
    capacity INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_scheduling_resources_branch CHECK (branch_code IN ('ES', 'SC')),
    CONSTRAINT ck_scheduling_resources_type CHECK (
        resource_type IN ('meeting_room', 'training_room', 'company_car', 'other')
    ),
    CONSTRAINT ck_scheduling_resources_capacity CHECK (capacity IS NULL OR capacity >= 1)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_scheduling_resources_branch_name
    ON scheduling.resources (branch_code, lower(trim(name)));

CREATE INDEX IF NOT EXISTS idx_scheduling_resources_branch_active
    ON scheduling.resources (branch_code, active);

CREATE TABLE IF NOT EXISTS scheduling.bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id UUID NOT NULL,
    branch_code VARCHAR(2) NOT NULL,
    title VARCHAR(200) NOT NULL,
    notes TEXT,
    start_at TIMESTAMPTZ NOT NULL,
    end_at TIMESTAMPTZ NOT NULL,
    booked_by_user_id VARCHAR(100) NOT NULL,
    booked_by_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_scheduling_bookings_resource
        FOREIGN KEY (resource_id)
        REFERENCES scheduling.resources (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_scheduling_bookings_branch CHECK (branch_code IN ('ES', 'SC')),
    CONSTRAINT ck_scheduling_bookings_status CHECK (status IN ('confirmed', 'cancelled')),
    CONSTRAINT ck_scheduling_bookings_time CHECK (end_at > start_at)
);

CREATE INDEX IF NOT EXISTS idx_scheduling_bookings_resource_time
    ON scheduling.bookings (resource_id, start_at, end_at)
    WHERE status = 'confirmed';

CREATE INDEX IF NOT EXISTS idx_scheduling_bookings_branch_time
    ON scheduling.bookings (branch_code, start_at, end_at)
    WHERE status = 'confirmed';
