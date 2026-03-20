CREATE TABLE IF NOT EXISTS quality.external_nc_effectiveness_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    action_id UUID,
    checked_by_user_id VARCHAR(100) NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL,
    criteria TEXT NOT NULL,
    result VARCHAR(30) NOT NULL,
    notes TEXT,
    next_action TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_external_nc_effectiveness_checks_nonconformity
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.external_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_external_nc_effectiveness_checks_action
        FOREIGN KEY (action_id)
        REFERENCES quality.external_nc_actions (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_external_nc_effectiveness_checks_result
        CHECK (
            result IN (
                'approved',
                'rejected',
                'partially-approved',
                'pending'
            )
        )
);