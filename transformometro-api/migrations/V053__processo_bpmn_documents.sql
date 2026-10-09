-- V053 — Transformômetro: documento BPMN nativo por processo (G7).
-- Ownership: o Transformômetro é autoridade dos artefatos BPMN nativos
-- vinculados ao processo (working copy + revisões imutáveis), espelhando
-- o modelo probado do bpmn_modeler (documento + revisions append-only).
-- XOR com transformometro.processo_bpmn_references (G5) é enforcement
-- de aplicação: um processo OU referencia um modelo externo OU possui
-- um documento nativo — nunca ambos (ADR-006).
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processo_bpmn_documents (
    document_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id          uuid NOT NULL
        REFERENCES transformometro.processos (processo_id),
    working_copy_xml     text NOT NULL,
    working_copy_sha256  char(64) NOT NULL,
    version              bigint NOT NULL CHECK (version >= 1),
    created_by_user_id   varchar(100) NOT NULL,
    updated_by_user_id   varchar(100) NOT NULL,
    created_at           timestamptz NOT NULL DEFAULT NOW(),
    updated_at           timestamptz NOT NULL DEFAULT NOW(),
    deleted_at           timestamptz,

    CONSTRAINT chk_bpmn_doc_xml_size
        CHECK (octet_length(working_copy_xml) <= 10485760),
    CONSTRAINT chk_bpmn_doc_sha256
        CHECK (working_copy_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_processo_bpmn_doc_active
    ON transformometro.processo_bpmn_documents (processo_id)
    WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS transformometro.processo_bpmn_revisions (
    revision_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id               uuid NOT NULL
        REFERENCES transformometro.processo_bpmn_documents (document_id)
        ON DELETE RESTRICT,
    revision_number           integer NOT NULL CHECK (revision_number >= 1),
    artifact_xml              text NOT NULL,
    artifact_sha256           char(64) NOT NULL
        CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
    origin                    varchar(16) NOT NULL
        CHECK (origin IN ('explicit', 'restore')),
    restored_from_revision_id uuid NULL
        REFERENCES transformometro.processo_bpmn_revisions (revision_id)
        ON DELETE RESTRICT,
    name                      varchar(120) NULL,
    description               varchar(500) NULL,
    created_by_user_id        varchar(100) NOT NULL,
    created_by_name           text NULL,
    created_at                timestamptz NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_bpmn_rev_xml_size
        CHECK (octet_length(artifact_xml) <= 10485760),
    CONSTRAINT chk_bpmn_rev_name_len
        CHECK (name IS NULL OR (btrim(name) <> '' AND char_length(name) <= 120)),
    CONSTRAINT chk_bpmn_rev_desc_len
        CHECK (description IS NULL OR char_length(description) <= 500),
    CONSTRAINT uq_bpmn_rev_number UNIQUE (document_id, revision_number)
);

CREATE INDEX IF NOT EXISTS idx_processo_bpmn_rev_doc
    ON transformometro.processo_bpmn_revisions (document_id, revision_number DESC);
CREATE INDEX IF NOT EXISTS idx_processo_bpmn_rev_restored
    ON transformometro.processo_bpmn_revisions (restored_from_revision_id)
    WHERE restored_from_revision_id IS NOT NULL;

COMMIT;
