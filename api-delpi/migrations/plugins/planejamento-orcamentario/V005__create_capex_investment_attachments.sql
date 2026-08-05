-- Planejamento Orçamentário — anexos de investimentos CAPEX (Fase 2B.3)
-- Schema: planejamento_orcamentario
-- Binários ficam no volume (BudgetDocumentStorage); aqui só metadados.
-- Soft-archive via is_active + archived_by/archived_at (sem DELETE físico).

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.capex_investment_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investment_id UUID NOT NULL
        REFERENCES planejamento_orcamentario.capex_investments(id),
    attachment_type VARCHAR(40) NOT NULL,
    display_name VARCHAR(300) NOT NULL,
    description TEXT,
    original_filename VARCHAR(300) NOT NULL DEFAULT '',
    mime_type VARCHAR(120) NOT NULL DEFAULT '',
    file_size BIGINT NOT NULL DEFAULT 0,
    storage_key VARCHAR(500) NOT NULL,
    idempotency_key VARCHAR(100),
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_by VARCHAR(100),
    archived_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_po_capex_att_type CHECK (attachment_type IN (
        'quotation',
        'commercial_proposal',
        'technical_specification',
        'image',
        'justification',
        'other'
    )),
    CONSTRAINT ck_po_capex_att_size CHECK (file_size >= 0),
    CONSTRAINT ck_po_capex_att_storage CHECK (btrim(storage_key) <> ''),
    CONSTRAINT ck_po_capex_att_display CHECK (btrim(display_name) <> ''),
    CONSTRAINT ck_po_capex_att_archive CHECK (
        (is_active = TRUE AND archived_at IS NULL AND archived_by IS NULL)
        OR (is_active = FALSE AND archived_at IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS ix_po_capex_att_investment
    ON planejamento_orcamentario.capex_investment_attachments (investment_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_att_investment_active
    ON planejamento_orcamentario.capex_investment_attachments (investment_id, is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_capex_att_active
    ON planejamento_orcamentario.capex_investment_attachments (is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_capex_att_created
    ON planejamento_orcamentario.capex_investment_attachments (created_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_po_capex_att_idempotency
    ON planejamento_orcamentario.capex_investment_attachments (investment_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL AND btrim(idempotency_key) <> '';
