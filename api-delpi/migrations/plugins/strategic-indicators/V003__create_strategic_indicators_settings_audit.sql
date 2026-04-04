BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.settings_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    entity_key VARCHAR(100) NOT NULL,
    payload_before JSONB NULL,
    payload_after JSONB NULL,
    changed_by_user_id UUID NULL,
    changed_by_email VARCHAR(255) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_si_settings_audit_event_type
        CHECK (
            event_type IN (
                'settings.updated'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_si_settings_audit_entity_key
    ON strategic_indicators.settings_audit (entity_key);

CREATE INDEX IF NOT EXISTS idx_si_settings_audit_created_at
    ON strategic_indicators.settings_audit (created_at DESC);

COMMENT ON TABLE strategic_indicators.settings_audit IS
'Tabela de auditoria mínima das alterações administrativas do plugin Strategic Indicators.';

COMMENT ON COLUMN strategic_indicators.settings_audit.entity_key IS
'Bloco lógico alterado. Ex.: weights.departments, goals.summary, parameters.global, governance.notes.';

COMMIT;