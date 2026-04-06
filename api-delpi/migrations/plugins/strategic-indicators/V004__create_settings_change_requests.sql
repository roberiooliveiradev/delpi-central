BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.settings_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_code VARCHAR(40) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,

    target_block VARCHAR(100) NOT NULL,
    proposed_payload JSONB NOT NULL,

    status VARCHAR(30) NOT NULL DEFAULT 'draft',

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,

    submitted_by_user_id UUID NULL,
    submitted_by_email VARCHAR(255) NULL,
    submitted_at TIMESTAMPTZ NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_si_change_requests_status
        CHECK (status IN ('draft', 'submitted')),

    CONSTRAINT ck_si_change_requests_target_block
        CHECK (
            target_block IN (
                'weights.departments',
                'goals.summary',
                'parameters.global',
                'governance.notes'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_si_change_requests_status
    ON strategic_indicators.settings_change_requests (status);

CREATE INDEX IF NOT EXISTS idx_si_change_requests_target_block
    ON strategic_indicators.settings_change_requests (target_block);

CREATE INDEX IF NOT EXISTS idx_si_change_requests_created_at
    ON strategic_indicators.settings_change_requests (created_at DESC);

COMMENT ON TABLE strategic_indicators.settings_change_requests IS
'Fila inicial de solicitações administrativas para futuras evoluções de workflow do Strategic Indicators.';

COMMIT;