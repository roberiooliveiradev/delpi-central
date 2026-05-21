BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.refresh_state (
    id TEXT PRIMARY KEY DEFAULT 'default',

    last_started_at TIMESTAMPTZ,
    last_completed_at TIMESTAMPTZ,
    last_duration_ms INTEGER,
    last_periods_upserted INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE strategic_indicators.refresh_state IS
'Estado do job periódico que materializa period_scores (indicadores pré-calculados).';

COMMIT;
