-- Etiquetas da Qualidade — inspeção por OP/produto com QR público.
-- Schema quality_labels (criado pelo runner de migrations de plugins).
-- Dados de produto são snapshot da OP (via use case de produção) no momento do registro.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS quality_labels.inspection_labels (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    public_token         TEXT NOT NULL UNIQUE,

    -- OP e snapshot do produto
    production_order     TEXT NOT NULL,
    branch               TEXT,
    product_code         TEXT NOT NULL,
    product_description  TEXT NOT NULL,
    product_unit         TEXT,
    order_number         TEXT,

    -- Inspeção
    inspected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    inspector_user_id    TEXT NOT NULL,
    inspector_name       TEXT NOT NULL,
    result               TEXT NOT NULL DEFAULT 'approved',
    notes                TEXT,

    -- QR / ciclo de vida
    qr_filename          TEXT,
    view_count           INTEGER NOT NULL DEFAULT 0,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_labels_op
    ON quality_labels.inspection_labels (production_order);
CREATE INDEX IF NOT EXISTS idx_quality_labels_product
    ON quality_labels.inspection_labels (product_code);
CREATE INDEX IF NOT EXISTS idx_quality_labels_date
    ON quality_labels.inspection_labels (inspected_at DESC);
