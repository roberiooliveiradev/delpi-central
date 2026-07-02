-- Auditoria completa do módulo de Etiquetas da Qualidade.
-- Registra o histórico de ações (criação, ativação, exclusão, visualização pública).
-- O label_id não tem FK: a etiqueta pode ser excluída e o evento deve permanecer.

CREATE TABLE IF NOT EXISTS quality_labels.audit_events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type        TEXT NOT NULL,
    label_id          UUID,
    production_order  TEXT,
    product_code      TEXT,
    branch            TEXT,
    result            TEXT,
    actor_user_id     TEXT,
    actor_name        TEXT,
    detail            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ql_audit_created
    ON quality_labels.audit_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ql_audit_type
    ON quality_labels.audit_events (event_type);
CREATE INDEX IF NOT EXISTS idx_ql_audit_label
    ON quality_labels.audit_events (label_id);
