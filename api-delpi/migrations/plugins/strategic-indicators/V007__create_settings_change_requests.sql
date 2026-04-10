BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.settings_change_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    request_code VARCHAR(40) NOT NULL,
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

    CONSTRAINT uq_si_settings_change_requests_request_code
        UNIQUE (request_code),

    CONSTRAINT ck_si_settings_change_requests_status
        CHECK (
            status IN (
                'draft',
                'submitted',
                'approved',
                'rejected',
                'cancelled'
            )
        ),

    CONSTRAINT ck_si_settings_change_requests_payload_is_object
        CHECK (jsonb_typeof(proposed_payload) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_si_settings_change_requests_status
    ON strategic_indicators.settings_change_requests (status);

CREATE INDEX IF NOT EXISTS idx_si_settings_change_requests_target_block
    ON strategic_indicators.settings_change_requests (target_block);

CREATE INDEX IF NOT EXISTS idx_si_settings_change_requests_created_at
    ON strategic_indicators.settings_change_requests (created_at DESC);

COMMENT ON TABLE strategic_indicators.settings_change_requests IS
'Fila administrativa de solicitações de alteração do Strategic Indicators.';

COMMENT ON COLUMN strategic_indicators.settings_change_requests.request_code IS
'Código legível da solicitação de alteração.';

COMMENT ON COLUMN strategic_indicators.settings_change_requests.target_block IS
'Bloco alvo da alteração. Ex.: departments, indicators, indicator_goals, parameters, governance.';

COMMENT ON COLUMN strategic_indicators.settings_change_requests.proposed_payload IS
'Payload JSONB com a proposta de alteração submetida para análise.';

COMMENT ON COLUMN strategic_indicators.settings_change_requests.status IS
'Status atual da solicitação.';

COMMIT;