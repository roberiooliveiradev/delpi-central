BEGIN;

-- V027 — MyWEG Notas Fiscais Emitidas (filial 02): observações históricas imutáveis.
-- Snapshots: nunca UPDATE/DELETE de observação aceita na aplicação.
-- Idempotência: UNIQUE(collection_id) — mesmo collection_id + mesmo payload
-- reutiliza; mesmo collection_id + payload diferente → conflito 409.
-- semantic_sha256 identifica equivalência fiscal entre coletas distintas.
-- Sem abatimento / conciliação nesta migration (Etapa 2).

CREATE TABLE IF NOT EXISTS production_control.myweg_invoice_observations (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id            VARCHAR(120) NOT NULL,
    branch                   VARCHAR(2)   NOT NULL
        CHECK (branch = '02'),
    myweg_company_code       VARCHAR(20)  NOT NULL
        CHECK (myweg_company_code = '1009'),
    myweg_work_center        VARCHAR(20)  NOT NULL
        CHECK (myweg_work_center = '1106'),
    myweg_supplier_code      VARCHAR(20)  NOT NULL
        CHECK (myweg_supplier_code = '50471'),
    contract_version         VARCHAR(64)  NOT NULL,
    document_date            DATE         NOT NULL,
    observation_status       VARCHAR(40)  NOT NULL
        CHECK (observation_status IN ('with_records', 'empty_signaled_by_sap')),
    observed_at              TIMESTAMPTZ  NULL,
    source_prepared_at       TIMESTAMPTZ  NOT NULL,
    imported_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    source_sha256            CHAR(64)     NULL,
    payload_sha256           CHAR(64)     NOT NULL,
    semantic_sha256          CHAR(64)     NOT NULL,
    record_count             INTEGER      NOT NULL CHECK (record_count >= 0),
    total_quantity_un        NUMERIC(18, 6) NOT NULL CHECK (total_quantity_un >= 0),
    manifesto_json           JSONB        NOT NULL DEFAULT '{}'::jsonb,
    status                   VARCHAR(20)  NOT NULL DEFAULT 'accepted'
        CHECK (status = 'accepted'),
    idempotency_key          VARCHAR(200) NOT NULL,
    caller_app               VARCHAR(120) NULL,
    CONSTRAINT uq_pc_myweg_invoice_observations_collection_id UNIQUE (collection_id),
    CONSTRAINT ck_pc_myweg_invoice_obs_empty_shape CHECK (
        (
            observation_status = 'empty_signaled_by_sap'
            AND record_count = 0
            AND source_sha256 IS NULL
        )
        OR (
            observation_status = 'with_records'
            AND record_count > 0
            AND source_sha256 IS NOT NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_document_date
    ON production_control.myweg_invoice_observations (document_date DESC, imported_at DESC);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_imported_at
    ON production_control.myweg_invoice_observations (imported_at DESC);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_payload_sha
    ON production_control.myweg_invoice_observations (payload_sha256);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_semantic_sha
    ON production_control.myweg_invoice_observations (semantic_sha256);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_status_date
    ON production_control.myweg_invoice_observations (observation_status, document_date DESC);

CREATE TABLE IF NOT EXISTS production_control.myweg_invoice_observation_items (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_id           UUID NOT NULL
        REFERENCES production_control.myweg_invoice_observations (id) ON DELETE RESTRICT,
    source_line_no           INTEGER NOT NULL CHECK (source_line_no >= 1),
    invoice_number           TEXT NOT NULL,
    invoice_series           TEXT NOT NULL,
    material_weg             TEXT NOT NULL,
    material_description     TEXT NOT NULL DEFAULT '',
    quantity_original        NUMERIC(18, 6) NOT NULL CHECK (quantity_original > 0),
    source_unit              VARCHAR(10) NOT NULL,
    quantity_un              NUMERIC(18, 6) NULL,
    unit_comparability       VARCHAR(20) NOT NULL
        CHECK (unit_comparability IN ('comparable', 'non_comparable')),
    departure_date           DATE NOT NULL,
    CONSTRAINT uq_pc_myweg_invoice_obs_items_line
        UNIQUE (observation_id, source_line_no),
    CONSTRAINT ck_pc_myweg_invoice_obs_items_qty_un CHECK (
        (
            unit_comparability = 'comparable'
            AND quantity_un IS NOT NULL
            AND quantity_un > 0
        )
        OR (
            unit_comparability = 'non_comparable'
            AND quantity_un IS NULL
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_items_observation
    ON production_control.myweg_invoice_observation_items (observation_id);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_items_material
    ON production_control.myweg_invoice_observation_items (observation_id, material_weg);

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_items_invoice
    ON production_control.myweg_invoice_observation_items (
        observation_id, invoice_number, invoice_series
    );

CREATE INDEX IF NOT EXISTS idx_pc_myweg_invoice_obs_items_departure
    ON production_control.myweg_invoice_observation_items (observation_id, departure_date);

COMMIT;
