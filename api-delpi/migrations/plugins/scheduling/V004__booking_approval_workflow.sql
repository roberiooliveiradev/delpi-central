-- Aprovação prévia: flag no recurso, status pending/rejected/expired, hold do slot + auditoria

ALTER TABLE scheduling.resources
    ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE scheduling.bookings
    ADD COLUMN IF NOT EXISTS decided_by_user_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS decided_by_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS decided_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS decision_reason TEXT,
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

ALTER TABLE scheduling.bookings
    DROP CONSTRAINT IF EXISTS ck_scheduling_bookings_status;

ALTER TABLE scheduling.bookings
    ADD CONSTRAINT ck_scheduling_bookings_status CHECK (
        status IN ('confirmed', 'cancelled', 'pending', 'rejected', 'expired')
    );

ALTER TABLE scheduling.bookings
    DROP CONSTRAINT IF EXISTS ex_scheduling_bookings_no_overlap;

ALTER TABLE scheduling.bookings
    ADD CONSTRAINT ex_scheduling_bookings_no_overlap
    EXCLUDE USING gist (
        resource_id WITH =,
        tstzrange(start_at, end_at, '[)') WITH &&
    )
    WHERE (status IN ('confirmed', 'pending'));

DROP INDEX IF EXISTS scheduling.idx_scheduling_bookings_resource_time;
DROP INDEX IF EXISTS scheduling.idx_scheduling_bookings_branch_time;

CREATE INDEX IF NOT EXISTS idx_scheduling_bookings_resource_time
    ON scheduling.bookings (resource_id, start_at, end_at)
    WHERE status IN ('confirmed', 'pending');

CREATE INDEX IF NOT EXISTS idx_scheduling_bookings_branch_time
    ON scheduling.bookings (branch_code, start_at, end_at)
    WHERE status IN ('confirmed', 'pending');

CREATE INDEX IF NOT EXISTS idx_scheduling_bookings_pending_expiry
    ON scheduling.bookings (branch_code, expires_at)
    WHERE status = 'pending';
