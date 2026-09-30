-- V002 — BPMN Modeler revision provenance
-- Revisões de origem 'restore' exigem provenance (restored_from_revision_id)
-- conforme a entidade de domínio Revision. Migration aditiva, up-only:
-- V001 permanece imutável (checksum enforcement).

BEGIN;

ALTER TABLE bpmn_modeler.revisions
    ADD COLUMN restored_from_revision_id uuid NULL
        REFERENCES bpmn_modeler.revisions(id) ON DELETE RESTRICT;

CREATE INDEX idx_revisions_restored_from
    ON bpmn_modeler.revisions (restored_from_revision_id)
    WHERE restored_from_revision_id IS NOT NULL;

COMMIT;
