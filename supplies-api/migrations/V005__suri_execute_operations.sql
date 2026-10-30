-- ================================================================
-- SURI-MCP-SUPPLIERS-DEPLOY-001 / GATE D1
-- Durable idempotency claim store for the SURI ``execute`` tool.
--
-- Owner: supplies-api (schema supplies). Stores ONLY the idempotent
-- request envelope — actor, (entity, action), key, payload fingerprint,
-- correlation id and the sanitized operational result (outcome,
-- operation_id, supplier_id, http_status). No ERP cadastral payload is
-- mirrored here: the Protheus write record remains owned by the
-- api-delpi integration tracker.
--
-- Guarantees:
--   UNIQUE (actor_subject, entity, action, idempotency_key) makes the
--   claim atomic across processes, workers and restarts — the first
--   claim wins; concurrent same-key callers see 'in_progress' and never
--   re-execute; completed rows replay the stored result.
--   expires_at bounds retention; lazy GC deletes expired rows on claim.
--
-- Upgrade path: additive, no changes to existing tables.
-- Rollback: DROP TABLE supplies.suri_execute_operations (the MCP
-- execute path fails closed for keyed operations while the store is
-- absent — no ERP write is issued without a successful claim).
-- ================================================================

CREATE TABLE IF NOT EXISTS supplies.suri_execute_operations (
    operation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_subject VARCHAR(120) NOT NULL,
    entity VARCHAR(40) NOT NULL,
    action VARCHAR(20) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('in_progress', 'completed')),
    correlation_id VARCHAR(64),
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_suri_execute_operations_key
        UNIQUE (actor_subject, entity, action, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_suri_execute_operations_expiry
    ON supplies.suri_execute_operations (expires_at);
