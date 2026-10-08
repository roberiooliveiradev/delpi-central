-- Transformômetro — referência explícita processo ↔ modelo BPMN (G5).
-- Ownership: Transformômetro owns the business relation; the BPMN Modeler
-- remains sole authority for models, working copies, revisions and artifacts.
-- Deliberately WITHOUT a foreign key into the BPMN Modeler schema — the
-- boundary is logical (HTTP contract + user-delegated auth), not physical.
-- One active reference per processo (process-level granularity, matching
-- processo_diagramas granularity).
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processo_bpmn_references (
    reference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id UUID NOT NULL
        REFERENCES transformometro.processos (processo_id),
    bpmn_model_id UUID NOT NULL,
    bpmn_revision_number INTEGER NOT NULL,
    created_by_user_id VARCHAR(100) NOT NULL,
    updated_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    CONSTRAINT chk_bpmn_revision_number_positive
        CHECK (bpmn_revision_number > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_processo_bpmn_ref_active
    ON transformometro.processo_bpmn_references (processo_id)
    WHERE deleted_at IS NULL;

COMMIT;
