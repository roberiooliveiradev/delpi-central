BEGIN;

CREATE TABLE IF NOT EXISTS tv_dashboard.gpt_actions_idempotency_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(120) NOT NULL,
    operation VARCHAR(120) NOT NULL,
    actor_user_id VARCHAR(100) NOT NULL,
    request_fingerprint VARCHAR(128) NOT NULL,
    response_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gpt_actions_idempotency_key_op_actor
        UNIQUE (key, operation, actor_user_id)
);

CREATE INDEX IF NOT EXISTS ix_gpt_actions_idempotency_created
    ON tv_dashboard.gpt_actions_idempotency_keys (created_at);

COMMIT;
