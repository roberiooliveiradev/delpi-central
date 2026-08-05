-- Schema commercial — carteiras de vendedor (migrado de pedidos_venda_abertos.sellers).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS commercial;

CREATE TABLE IF NOT EXISTS commercial.seller_portfolios (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              TEXT NOT NULL UNIQUE,
    display_name         TEXT NOT NULL,
    active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id   TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commercial_seller_portfolios_active
    ON commercial.seller_portfolios (active);

CREATE TABLE IF NOT EXISTS commercial.seller_customers (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_portfolio_id  UUID NOT NULL
        REFERENCES commercial.seller_portfolios (id) ON DELETE CASCADE,
    customer_code        TEXT NOT NULL,
    customer_store       TEXT NOT NULL,
    customer_name        TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (seller_portfolio_id, customer_code, customer_store)
);

CREATE INDEX IF NOT EXISTS idx_commercial_seller_customers_portfolio
    ON commercial.seller_customers (seller_portfolio_id);

CREATE INDEX IF NOT EXISTS idx_commercial_seller_customers_identity
    ON commercial.seller_customers (customer_code, customer_store);

CREATE TABLE IF NOT EXISTS commercial.audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id   TEXT NOT NULL,
    action          TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commercial_audit_log_entity
    ON commercial.audit_log (entity_type, entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_commercial_audit_log_actor
    ON commercial.audit_log (actor_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_commercial_audit_log_created
    ON commercial.audit_log (created_at DESC);
