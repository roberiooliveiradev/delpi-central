-- Gestão de inspetor — perfil e assinatura por usuário do Core API.
-- A assinatura (PNG) é armazenada em disco (QUALITY_LABELS_SIGNATURE_DIR);
-- aqui guardamos apenas o metadado (nome do arquivo + mime).

CREATE TABLE IF NOT EXISTS quality_labels.inspectors (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               TEXT NOT NULL UNIQUE,
    display_name          TEXT NOT NULL,
    role_title            TEXT,
    signature_filename    TEXT,
    signature_mime        TEXT,
    signature_updated_at  TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ql_inspectors_user
    ON quality_labels.inspectors (user_id);
