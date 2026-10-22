-- ================================================================
-- SUPPLIES-ENRICHMENT-01 / S2 REWORK
-- Decision operations: separates the idempotent *request* from the
-- per-field decisions it produced.
--
-- Root cause of the rework: V002 put UNIQUE(review_id, idempotency_key)
-- on supplier_enrichment_decisions, but a bulk request inserts one
-- decision row per field with the same key — every batch with more
-- than one field violated the constraint at the second row.
--
-- New shape:
--   supplier_enrichment_decision_operations — one row per request,
--   holds the idempotency key, request hash, revision and actor.
--   UNIQUE(review_id, idempotency_key) lives here.
--
--   supplier_enrichment_decisions — one row per field decision,
--   linked to its operation via operation_id.
--
-- Upgrade path: additive. V002 was never deployed (DEPLOY=NOT RUN), so
-- no environment holds decision rows; environments that hypothetically
-- applied V002 with rows must truncate the four enrichment tables or
-- backfill operation rows before V003 sets operation_id NOT NULL.
-- ================================================================

CREATE TABLE supplies.supplier_enrichment_decision_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL
        REFERENCES supplies.supplier_enrichment_reviews (review_id) ON DELETE RESTRICT,
    actor_subject UUID NOT NULL,
    decision VARCHAR(8) NOT NULL CHECK (decision IN ('ACCEPT', 'REJECT')),
    reason_code VARCHAR(64),
    idempotency_key VARCHAR(128) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    review_revision INTEGER NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (review_id, idempotency_key)
);

-- Re-link decisions to their operation; request-level metadata moves
-- to the operation row.
ALTER TABLE supplies.supplier_enrichment_decisions
    ADD COLUMN operation_id UUID
        REFERENCES supplies.supplier_enrichment_decision_operations (operation_id)
        ON DELETE RESTRICT;

ALTER TABLE supplies.supplier_enrichment_decisions
    DROP CONSTRAINT supplier_enrichment_decisions_review_id_idempotency_key_key,
    DROP COLUMN idempotency_key,
    DROP COLUMN request_hash,
    DROP COLUMN reason_code,
    DROP COLUMN review_revision;

-- No V002 environment carries decision rows (service never deployed);
-- NOT NULL is safe on the only real upgrade path.
ALTER TABLE supplies.supplier_enrichment_decisions
    ALTER COLUMN operation_id SET NOT NULL;

CREATE INDEX idx_enrichment_decision_ops_review
    ON supplies.supplier_enrichment_decision_operations (review_id, decided_at);

CREATE INDEX idx_enrichment_decisions_operation
    ON supplies.supplier_enrichment_decisions (operation_id);
