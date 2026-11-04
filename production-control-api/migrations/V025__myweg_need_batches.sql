BEGIN;

-- V025 — MyWEG Necessidades (filial 02): lotes imutáveis + registros.
-- Snapshots históricos: nunca UPDATE/DELETE de lote aceito na aplicação.
-- Idempotência: UNIQUE(collection_id) — mesmo collection_id + mesmo payload
-- reutiliza o lote; mesmo collection_id + payload diferente → conflito 409.
-- payload_sha256 NÃO é único global (planejamento idêntico em dias distintos).

CREATE TABLE IF NOT EXISTS production_control.myweg_need_batches (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id            VARCHAR(120) NOT NULL,
    branch                   VARCHAR(2)   NOT NULL
        CHECK (branch = '02'),
    myweg_company_code       VARCHAR(20)  NOT NULL
        CHECK (myweg_company_code = '1009'),
    myweg_work_center        VARCHAR(20)  NOT NULL
        CHECK (myweg_work_center = '1106'),
    contract_version         VARCHAR(64)  NOT NULL,
    collected_at             TIMESTAMPTZ  NOT NULL,
    exported_at              TIMESTAMPTZ  NOT NULL,
    collection_date          DATE         NOT NULL,
    imported_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    payload_sha256           CHAR(64)     NOT NULL,
    source_files_json        JSONB        NOT NULL,
    record_count             INTEGER      NOT NULL CHECK (record_count > 0),
    total_quantidade_un      NUMERIC(18, 6) NOT NULL CHECK (total_quantidade_un > 0),
    total_quantidade_mi      NUMERIC(18, 6) NOT NULL CHECK (total_quantidade_mi > 0),
    status                   VARCHAR(20)  NOT NULL DEFAULT 'accepted'
        CHECK (status = 'accepted'),
    idempotency_key          VARCHAR(200) NOT NULL,
    caller_app               VARCHAR(120) NULL,
    CONSTRAINT uq_pc_myweg_need_batches_collection_id UNIQUE (collection_id)
);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_batches_imported_at
    ON production_control.myweg_need_batches (imported_at DESC);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_batches_collection_date
    ON production_control.myweg_need_batches (collection_date DESC, imported_at DESC);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_batches_payload_sha
    ON production_control.myweg_need_batches (payload_sha256);

CREATE TABLE IF NOT EXISTS production_control.myweg_need_records (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id                 UUID NOT NULL
        REFERENCES production_control.myweg_need_batches (id) ON DELETE RESTRICT,
    line_no                  INTEGER NOT NULL CHECK (line_no >= 1),
    material_weg_tratado     TEXT NOT NULL,
    codigo_referencia_weg    TEXT NULL,
    origem_material_weg      TEXT NOT NULL,
    quantidade_original_un   NUMERIC(18, 6) NOT NULL CHECK (quantidade_original_un > 0),
    quantidade_mi            NUMERIC(18, 6) NOT NULL CHECK (quantidade_mi > 0),
    unidade                  VARCHAR(10) NOT NULL,
    data_remessa             DATE NOT NULL,
    documento                TEXT NULL,
    linha_fonte              TEXT NULL,
    assinatura_registro      TEXT NULL,
    rastreabilidade          TEXT NOT NULL,
    line_fingerprint         CHAR(64) NOT NULL,
    sb1_status               VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (sb1_status = 'pending'),
    sb1_protheus_product_code TEXT NULL,
    sb1_matched_by           TEXT NULL,
    sb1_resolved_at          TIMESTAMPTZ NULL,
    CONSTRAINT uq_pc_myweg_need_records_batch_line UNIQUE (batch_id, line_no),
    CONSTRAINT uq_pc_myweg_need_records_batch_fingerprint UNIQUE (batch_id, line_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_records_batch_id
    ON production_control.myweg_need_records (batch_id);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_records_remessa
    ON production_control.myweg_need_records (batch_id, data_remessa);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_records_material
    ON production_control.myweg_need_records (batch_id, material_weg_tratado);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_need_records_referencia
    ON production_control.myweg_need_records (batch_id, codigo_referencia_weg);

COMMIT;
