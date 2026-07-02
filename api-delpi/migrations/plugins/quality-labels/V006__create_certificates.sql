-- Certificado de Qualidade (RQ-032) anexo à etiqueta (1:1).
-- Cliente é autopreenchido via OP (C2_PEDIDO → SC5 → SA1) quando disponível,
-- caso contrário é editável (customer_source = 'manual').
-- O PDF emitido é imutável e armazenado em QUALITY_LABELS_CERTIFICATE_DIR.

CREATE TABLE IF NOT EXISTS quality_labels.certificates (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label_id           UUID NOT NULL UNIQUE
                       REFERENCES quality_labels.inspection_labels(id) ON DELETE CASCADE,
    doc_ref            TEXT NOT NULL DEFAULT 'RQ-032 – Rev.00 – 21/01/2021',
    sample_type        TEXT NOT NULL DEFAULT 'fornecimento',  -- amostra | lote_piloto | fornecimento
    quantity           TEXT,
    sample_quantity    TEXT,

    -- Cliente (autofill via OP quando houver; sempre editável)
    customer_code      TEXT,
    customer_store     TEXT,
    customer_name      TEXT,
    customer_item      TEXT,
    customer_item_rev  TEXT,
    customer_source    TEXT NOT NULL DEFAULT 'manual',        -- totvs | manual

    delpi_notes        TEXT,
    customer_notes     TEXT,

    inspector_user_id  TEXT NOT NULL,
    inspector_name     TEXT NOT NULL,

    status             TEXT NOT NULL DEFAULT 'draft',          -- draft | issued
    pdf_filename       TEXT,
    issued_at          TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ql_certificates_label
    ON quality_labels.certificates (label_id);

CREATE TABLE IF NOT EXISTS quality_labels.certificate_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id  UUID NOT NULL
                    REFERENCES quality_labels.certificates(id) ON DELETE CASCADE,
    position        INTEGER NOT NULL,
    description     TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'A',   -- A (aprovado) | R (reprovado) | NA (não aplicável)
    is_custom       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ql_cert_items_cert
    ON quality_labels.certificate_items (certificate_id, position);
