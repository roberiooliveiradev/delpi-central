-- Outbox + checkpoints for commercial side-effects (ready_to_invoice notifications).
-- Spec: docs/12-roadmap-e-evolucao/commercial/DATA-MODEL.md § 4.7–4.8

CREATE TABLE IF NOT EXISTS commercial.integration_outbox (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type       TEXT NOT NULL,
    aggregate_type   TEXT NOT NULL,
    aggregate_id     TEXT NOT NULL,
    payload          JSONB NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    available_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at     TIMESTAMPTZ,
    attempts         INT NOT NULL DEFAULT 0,
    last_error       TEXT
);

CREATE INDEX IF NOT EXISTS idx_commercial_integration_outbox_pending
    ON commercial.integration_outbox (available_at)
    WHERE published_at IS NULL;

CREATE TABLE IF NOT EXISTS commercial.integration_checkpoints (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_key        TEXT NOT NULL UNIQUE,
    cursor_value      TEXT,
    last_success_at   TIMESTAMPTZ,
    metadata          JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
