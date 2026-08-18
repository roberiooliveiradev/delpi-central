CREATE TABLE IF NOT EXISTS commercial.sla_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applies_to TEXT NOT NULL,
    duration_hours INTEGER NOT NULL,
    calendar_code TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT sla_policies_applies_ck CHECK (
        applies_to IN ('task', 'sample', 'order_confirmation', 'offer_stage')
    )
);

COMMENT ON TABLE commercial.sla_policies IS
    'SLA settings; empty until Comercial homologates durations. GET returns [].';
