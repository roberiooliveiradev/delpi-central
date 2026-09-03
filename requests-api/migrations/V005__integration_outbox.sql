BEGIN;

CREATE TABLE IF NOT EXISTS my_requests.integration_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(80) NOT NULL,
    aggregate_type VARCHAR(80) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    request_id UUID,
    request_version INT,
    dedupe_key VARCHAR(200),
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    attempts INT NOT NULL DEFAULT 0,
    last_error TEXT,
    next_retry_at TIMESTAMPTZ,
    dead_letter_at TIMESTAMPTZ,
    CONSTRAINT uq_integration_outbox_dedupe UNIQUE (dedupe_key)
);

CREATE INDEX IF NOT EXISTS ix_integration_outbox_pending
    ON my_requests.integration_outbox (available_at)
    WHERE published_at IS NULL AND dead_letter_at IS NULL;

COMMIT;
