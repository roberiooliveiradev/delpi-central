BEGIN;

-- V026 — Projeção de resolução SB1 para necessidades MyWEG (aditiva).
-- Snapshots V025 (batches/records) permanecem imutáveis; sb1_* nas records
-- continua restrito a pending. Vínculos verificados vivem nesta projeção.
-- verified_at registra quando o cadastro Protheus foi consultado (não prova
-- o estado histórico na data da coleta).

CREATE TABLE IF NOT EXISTS production_control.myweg_need_sb1_resolution_runs (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id                 UUID NOT NULL
        REFERENCES production_control.myweg_need_batches (id) ON DELETE RESTRICT,
    dry_run                  BOOLEAN NOT NULL DEFAULT TRUE,
    caller_app               VARCHAR(120) NULL,
    started_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at              TIMESTAMPTZ NULL,
    status                   VARCHAR(32) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed')),
    counts_json              JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message            TEXT NULL,
    semantics_proven         BOOLEAN NOT NULL DEFAULT FALSE,
    semantics_notes          TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_sb1_runs_batch
    ON production_control.myweg_need_sb1_resolution_runs (batch_id, started_at DESC);

CREATE TABLE IF NOT EXISTS production_control.myweg_need_sb1_resolutions (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id                 UUID NOT NULL
        REFERENCES production_control.myweg_need_batches (id) ON DELETE RESTRICT,
    record_id                UUID NOT NULL
        REFERENCES production_control.myweg_need_records (id) ON DELETE RESTRICT,
    line_fingerprint         CHAR(64) NOT NULL,
    status                   VARCHAR(32) NOT NULL
        CHECK (status IN (
            'confirmed',
            'pending',
            'not_found',
            'ambiguous',
            'divergent',
            'blocked',
            'unavailable'
        )),
    informed_product_code    TEXT NULL,
    customer_reference       TEXT NULL,
    verified_product_code    TEXT NULL,
    verified_description     TEXT NULL,
    matched_by               TEXT NULL,
    reason                   TEXT NULL,
    candidates_json          JSONB NOT NULL DEFAULT '[]'::jsonb,
    source                   VARCHAR(80) NOT NULL
        DEFAULT 'api-delpi.lookup_products_sb1_identity',
    resolution_run_id        UUID NOT NULL
        REFERENCES production_control.myweg_need_sb1_resolution_runs (id)
            ON DELETE RESTRICT,
    verified_at              TIMESTAMPTZ NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pc_myweg_sb1_resolutions_record UNIQUE (record_id)
);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_sb1_resolutions_batch_status
    ON production_control.myweg_need_sb1_resolutions (batch_id, status);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_sb1_resolutions_batch_verified
    ON production_control.myweg_need_sb1_resolutions (batch_id, verified_at DESC);

COMMIT;
