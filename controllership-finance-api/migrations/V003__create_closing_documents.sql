-- V003 — P2-Upload SLICE-1 (GO CF-C3-P2-UPLOAD-IMPL-GO-001): evidências
-- documentais do fechamento. Metadados no schema próprio; binários ficam
-- no volume persistente (CF_DOCUMENT_UPLOAD_DIR) — o par é indissociável.
-- Idempotência D-U7=A: padrão supplies-api (UNIQUE(competence_id, key) +
-- request_hash + registros persistentes, sem TTL).
BEGIN;

-- Par binário↔metadado: 1 arquivo físico = 1 linha (storage_key única).
CREATE TABLE IF NOT EXISTS controllership_finance.document_file (
    file_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    storage_key     VARCHAR(512) NOT NULL UNIQUE,
    original_name   VARCHAR(255) NOT NULL,
    stored_name     VARCHAR(255) NOT NULL,
    mime_type       VARCHAR(128) NOT NULL,
    extension       VARCHAR(16)  NOT NULL,
    size_bytes      BIGINT       NOT NULL
        CHECK (size_bytes > 0 AND size_bytes <= 26214400),
    checksum_sha256 CHAR(64)     NOT NULL,
    created_by      UUID         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- FK composta (competence_id, snapshot_item_id) exige índice único pai —
-- prova no banco que item vinculado pertence à competência (D-U6=A).
CREATE UNIQUE INDEX IF NOT EXISTS competence_item_competence_snapshot_uq
    ON controllership_finance.competence_checklist_item
    (competence_id, snapshot_item_id);

CREATE TABLE IF NOT EXISTS controllership_finance.closing_document (
    document_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id    UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    snapshot_item_id UUID,
    link_kind        VARCHAR(16)  NOT NULL
        CHECK (link_kind IN ('competence', 'competence_item')),
    title            VARCHAR(255),
    attachment_role  VARCHAR(32)  NOT NULL DEFAULT 'generic'
        CHECK (attachment_role = 'generic'),
    state            VARCHAR(16)  NOT NULL DEFAULT 'ATTACHED'
        CHECK (state IN ('ATTACHED', 'SUPERSEDED', 'CANCELLED')),
    current_version_no INT        NOT NULL DEFAULT 1
        CHECK (current_version_no >= 1),
    revision         INT          NOT NULL DEFAULT 1 CHECK (revision >= 1),
    idempotency_key  VARCHAR(128) NOT NULL,
    request_hash     CHAR(64)     NOT NULL,
    uploaded_by      UUID         NOT NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK (
        (link_kind = 'competence' AND snapshot_item_id IS NULL)
        OR (link_kind = 'competence_item' AND snapshot_item_id IS NOT NULL)
    ),
    UNIQUE (competence_id, idempotency_key),
    FOREIGN KEY (competence_id, snapshot_item_id)
        REFERENCES controllership_finance.competence_checklist_item
        (competence_id, snapshot_item_id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS closing_document_competence_idx
    ON controllership_finance.closing_document (competence_id);

CREATE INDEX IF NOT EXISTS closing_document_item_idx
    ON controllership_finance.closing_document (snapshot_item_id)
    WHERE snapshot_item_id IS NOT NULL;

-- Versões imutáveis: histórico nunca é reescrito (SUPERSEDED != DELETED).
CREATE TABLE IF NOT EXISTS controllership_finance.document_version (
    document_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID         NOT NULL
        REFERENCES controllership_finance.closing_document (document_id)
        ON DELETE RESTRICT,
    version_no          INT          NOT NULL CHECK (version_no >= 1),
    file_id             UUID         NOT NULL
        REFERENCES controllership_finance.document_file (file_id)
        ON DELETE RESTRICT,
    state               VARCHAR(16)  NOT NULL DEFAULT 'ATTACHED'
        CHECK (state IN ('ATTACHED', 'SUPERSEDED')),
    uploaded_by         UUID         NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (document_id, version_no)
);

CREATE INDEX IF NOT EXISTS document_version_document_idx
    ON controllership_finance.document_version (document_id);

COMMIT;
