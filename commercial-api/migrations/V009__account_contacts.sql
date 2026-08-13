-- Contatos comerciais mantidos por conta de cliente.

CREATE TABLE IF NOT EXISTS commercial.account_contacts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code      TEXT NOT NULL,
    customer_store     TEXT NOT NULL,
    full_name          TEXT NOT NULL,
    role_title         TEXT,
    channel            TEXT NOT NULL
        CHECK (channel IN ('phone', 'mobile', 'email', 'whatsapp', 'other')),
    email              TEXT,
    phone_e164         TEXT,
    is_whatsapp        BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary         BOOLEAN NOT NULL DEFAULT FALSE,
    source             TEXT NOT NULL DEFAULT 'manual',
    deleted_at         TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_commercial_account_contacts_customer
    ON commercial.account_contacts (customer_code, customer_store)
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_commercial_account_contacts_primary
    ON commercial.account_contacts (customer_code, customer_store)
    WHERE is_primary = TRUE AND deleted_at IS NULL;
