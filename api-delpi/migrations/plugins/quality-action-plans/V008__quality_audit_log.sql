-- Onda 4 — trilha de auditoria imutável para governança PAC

CREATE TABLE IF NOT EXISTS quality.quality_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_audit_log_entity
    ON quality.quality_audit_log (entity_type, entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quality_audit_log_event
    ON quality.quality_audit_log (event_type, created_at DESC);

CREATE OR REPLACE FUNCTION quality.prevent_quality_audit_log_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'quality_audit_log is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_quality_audit_log_no_mutation ON quality.quality_audit_log;

CREATE TRIGGER trg_quality_audit_log_no_mutation
    BEFORE UPDATE OR DELETE ON quality.quality_audit_log
    FOR EACH ROW
    EXECUTE PROCEDURE quality.prevent_quality_audit_log_mutation();

COMMENT ON TABLE quality.quality_audit_log IS
    'Trilha imutável de eventos sensíveis PAC (reabertura, fechamento, eficácia).';
