-- Logos de clientes — metadado Postgres; bytes no volume commercial-avatars.

CREATE TABLE IF NOT EXISTS commercial.customer_avatars (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code        TEXT NOT NULL,
    customer_store       TEXT NOT NULL,
    file_name            TEXT NOT NULL,
    storage_key          TEXT NOT NULL,
    content_type         TEXT NOT NULL,
    byte_size            BIGINT,
    uploaded_by_user_id  TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_code, customer_store)
);

CREATE INDEX IF NOT EXISTS idx_commercial_customer_avatars_identity
    ON commercial.customer_avatars (customer_code, customer_store);
