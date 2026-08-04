-- Portal do Vendedor — carteira manual (usuário Minha DELPI ↔ clientes).
-- Schema pedidos_venda_abertos (criado pelo runner: slug pedidos-venda-abertos).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS pedidos_venda_abertos.sellers (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              TEXT NOT NULL UNIQUE,
    display_name         TEXT NOT NULL,
    active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id   TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pva_sellers_active
    ON pedidos_venda_abertos.sellers (active);

CREATE TABLE IF NOT EXISTS pedidos_venda_abertos.seller_customers (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id            UUID NOT NULL
        REFERENCES pedidos_venda_abertos.sellers (id) ON DELETE CASCADE,
    customer_code        TEXT NOT NULL,
    customer_store       TEXT NOT NULL,
    customer_name        TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (seller_id, customer_code, customer_store)
);

CREATE INDEX IF NOT EXISTS idx_pva_seller_customers_seller
    ON pedidos_venda_abertos.seller_customers (seller_id);

CREATE INDEX IF NOT EXISTS idx_pva_seller_customers_identity
    ON pedidos_venda_abertos.seller_customers (customer_code, customer_store);
