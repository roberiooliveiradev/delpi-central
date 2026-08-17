-- Anexos genéricos (P2) — metadado Postgres; bytes no volume commercial-attachments.

CREATE TABLE IF NOT EXISTS commercial.attachments (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_type           TEXT NOT NULL
        CHECK (owner_type IN ('task', 'customer', 'activity')),
    owner_id             TEXT NOT NULL,
    file_name            TEXT NOT NULL,
    storage_key          TEXT NOT NULL,
    content_type         TEXT NOT NULL,
    byte_size            BIGINT NOT NULL CHECK (byte_size > 0),
    uploaded_by_user_id  TEXT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commercial_attachments_owner
    ON commercial.attachments (owner_type, owner_id);

CREATE INDEX IF NOT EXISTS idx_commercial_attachments_created
    ON commercial.attachments (created_at DESC);
