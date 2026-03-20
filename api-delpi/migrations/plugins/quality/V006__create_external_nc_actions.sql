CREATE TABLE IF NOT EXISTS quality.external_nc_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    root_cause_id UUID,
    action_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    responsible_user_id VARCHAR(100),
    responsible_external_name VARCHAR(255),
    responsible_external_email VARCHAR(255),
    start_date DATE,
    due_date DATE NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    verification_required BOOLEAN NOT NULL DEFAULT FALSE,
    effectiveness_due_date DATE,
    completion_notes TEXT,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_external_nc_actions_nonconformity
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.external_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_external_nc_actions_root_cause
        FOREIGN KEY (root_cause_id)
        REFERENCES quality.external_nc_root_causes (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_external_nc_actions_status
        CHECK (
            status IN (
                'pending',
                'in-progress',
                'completed',
                'cancelled',
                'overdue'
            )
        ),

    CONSTRAINT ck_external_nc_actions_dates
        CHECK (
            start_date IS NULL
            OR due_date IS NULL
            OR start_date <= due_date
        ),

    CONSTRAINT ck_external_nc_actions_responsible
        CHECK (
            responsible_user_id IS NOT NULL
            OR responsible_external_name IS NOT NULL
        ),

    CONSTRAINT ck_external_nc_actions_completed_at
        CHECK (
            (status = 'completed' AND completed_at IS NOT NULL)
            OR
            (status <> 'completed')
        )
);