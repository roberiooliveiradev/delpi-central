-- GLPI #945: cancelamento auditável de NC candidata sem plano de ação.
-- Migration somente aditiva: não modifica linhas nem constraints existentes.
-- Aplicar antes de publicar a versão da API que consulta esta tabela.
CREATE TABLE IF NOT EXISTS quality.audit_5s_nc_candidate_cancellations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL REFERENCES quality.audit_5s_audits(id) ON DELETE CASCADE,
    response_id UUID NOT NULL REFERENCES quality.audit_5s_responses(id) ON DELETE CASCADE,
    score_at_cancellation SMALLINT NOT NULL
        CHECK (score_at_cancellation IN (1, 3)),
    reason TEXT NOT NULL CHECK (char_length(btrim(reason)) BETWEEN 5 AND 1000),
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ NULL
);

-- Permite múltiplos eventos históricos, mas apenas um cancelamento ativo por critério.
CREATE UNIQUE INDEX IF NOT EXISTS uq_audit_5s_nc_candidate_cancellations_active
    ON quality.audit_5s_nc_candidate_cancellations (response_id)
    WHERE revoked_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_audit_5s_nc_candidate_cancellations_audit_active
    ON quality.audit_5s_nc_candidate_cancellations (audit_id, response_id)
    WHERE revoked_at IS NULL;
