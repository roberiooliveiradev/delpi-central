-- Melhorias-como-revisões + auditoria em 3 camadas (padrão quality-action-plans).
--
-- Conceito:
--  * Cada revisão de quality.kaizen_revisions é uma MELHORIA do processo, com sua
--    própria vigência (effective_from/until), cálculo (daily/annual_savings) e
--    evidências (kaizen_evidences.revision_id). O ganho por período soma cada
--    melhoria dentro da sua validade de 1 ano a partir de effective_from.
--  * quality.kaizen_history = linha do tempo operacional (eventos discretos).
--  * quality.kaizen_audit_log = trilha de governança append-only (imutável).

-- 1) Economia explícita na revisão (para agregação de ganhos por período sem varrer JSONB)
ALTER TABLE quality.kaizen_revisions
    ADD COLUMN IF NOT EXISTS daily_savings NUMERIC(14, 2),
    ADD COLUMN IF NOT EXISTS annual_savings NUMERIC(14, 2),
    ADD COLUMN IF NOT EXISTS created_by_name VARCHAR(300);

UPDATE quality.kaizen_revisions
   SET daily_savings = NULLIF(snapshot ->> 'daily_savings', '')::numeric
 WHERE daily_savings IS NULL
   AND snapshot ->> 'daily_savings' IS NOT NULL;

UPDATE quality.kaizen_revisions
   SET annual_savings = NULLIF(snapshot ->> 'annual_savings', '')::numeric
 WHERE annual_savings IS NULL
   AND snapshot ->> 'annual_savings' IS NOT NULL;

-- 2) Evidências por melhoria (revisão). NULL = evidência geral do kaizen.
ALTER TABLE quality.kaizen_evidences
    ADD COLUMN IF NOT EXISTS revision_id UUID;

ALTER TABLE quality.kaizen_evidences
    DROP CONSTRAINT IF EXISTS fk_kaizen_evidences_revision;

ALTER TABLE quality.kaizen_evidences
    ADD CONSTRAINT fk_kaizen_evidences_revision
        FOREIGN KEY (revision_id)
        REFERENCES quality.kaizen_revisions (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_kaizen_evidences_revision
    ON quality.kaizen_evidences (revision_id);

-- 3) Linha do tempo operacional
CREATE TABLE IF NOT EXISTS quality.kaizen_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    comment TEXT,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(300),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_kaizen_history_kaizen
        FOREIGN KEY (kaizen_id)
        REFERENCES quality.kaizens (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_kaizen_history_kaizen
    ON quality.kaizen_history (kaizen_id, created_at DESC);

-- 4) Trilha de governança append-only (imutável)
CREATE TABLE IF NOT EXISTS quality.kaizen_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_name VARCHAR(300),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_kaizen_audit_log_kaizen
    ON quality.kaizen_audit_log (kaizen_id, created_at DESC);

-- Bloqueia UPDATE/DELETE na trilha de governança
CREATE OR REPLACE FUNCTION quality.kaizen_audit_log_block_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'quality.kaizen_audit_log é append-only (UPDATE/DELETE bloqueado).';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_kaizen_audit_log_block_mutation ON quality.kaizen_audit_log;
CREATE TRIGGER trg_kaizen_audit_log_block_mutation
    BEFORE UPDATE OR DELETE ON quality.kaizen_audit_log
    FOR EACH ROW EXECUTE FUNCTION quality.kaizen_audit_log_block_mutation();
