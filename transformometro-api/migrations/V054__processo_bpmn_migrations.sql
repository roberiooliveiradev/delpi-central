-- V054 — G8: migração governada flowchart_v1 → BPMN nativo.
--
-- 1) Estende o CHECK de origin das revisões BPMN com 'migration'
--    (R1 de uma migração é proveniente de migração, não de
--    checkpoint manual 'explicit' nem 'restore').
-- 2) Cria transformometro.processo_bpmn_migrations — metadados
--    EXTERNOS de migração. O legado (process_diagram flowchart_v1)
--    NÃO é mutado: a proveniência vive aqui, não no payload legado.
BEGIN;

ALTER TABLE transformometro.processo_bpmn_revisions
    DROP CONSTRAINT IF EXISTS processo_bpmn_revisions_origin_check;

ALTER TABLE transformometro.processo_bpmn_revisions
    ADD CONSTRAINT processo_bpmn_revisions_origin_check
    CHECK (origin IN ('explicit', 'restore', 'migration'));

CREATE TABLE IF NOT EXISTS transformometro.processo_bpmn_migrations (
    migration_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id               uuid NOT NULL
        REFERENCES transformometro.processos (processo_id),
    document_id               uuid NOT NULL
        REFERENCES transformometro.processo_bpmn_documents (document_id)
        ON DELETE RESTRICT,
    revision_id               uuid NOT NULL
        REFERENCES transformometro.processo_bpmn_revisions (revision_id)
        ON DELETE RESTRICT,
    legacy_source_fingerprint char(64) NOT NULL
        CHECK (legacy_source_fingerprint ~ '^[0-9a-f]{64}$'),
    candidate_sha256          char(64) NOT NULL
        CHECK (candidate_sha256 ~ '^[0-9a-f]{64}$'),
    mapping_report            jsonb NOT NULL,
    source_summary            jsonb NOT NULL DEFAULT '{}'::jsonb,
    migrated_by_user_id       varchar(100) NOT NULL,
    migrated_by_name          text NULL,
    created_at                timestamptz NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bpmn_migrations_processo
    ON transformometro.processo_bpmn_migrations (processo_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bpmn_migrations_document
    ON transformometro.processo_bpmn_migrations (document_id);

COMMIT;
