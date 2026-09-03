BEGIN;

CREATE TABLE IF NOT EXISTS my_requests.idempotency_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(120) NOT NULL,
    route VARCHAR(200) NOT NULL,
    actor_user_id VARCHAR(100) NOT NULL,
    response_snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_idempotency_keys_key_route_actor
        UNIQUE (key, route, actor_user_id)
);

CREATE INDEX IF NOT EXISTS ix_idempotency_keys_created
    ON my_requests.idempotency_keys (created_at);

COMMIT;
