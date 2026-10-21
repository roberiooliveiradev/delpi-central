-- Idempotency index fix — NULL caller_app must also deduplicate.
-- PostgreSQL UNIQUE treats NULLs as distinct, so V001's partial index
-- allowed duplicate (caller_app=NULL, idempotency_key=X) rows.
-- COALESCE normalizes NULL caller_app to '' making the key effective.

DROP INDEX IF EXISTS integration_tracking.uq_integration_operations_idem_key;

CREATE UNIQUE INDEX uq_integration_operations_idem_key
    ON integration_tracking.integration_operations (
        (COALESCE(caller_app, '')),
        idempotency_key
    )
    WHERE idempotency_key IS NOT NULL;
