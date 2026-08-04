-- Logos de clientes (código + loja) para avatar na Minha carteira.
-- Schema pedidos_venda_abertos (criado pelo runner).

CREATE TABLE IF NOT EXISTS pedidos_venda_abertos.customer_avatars (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_code        TEXT NOT NULL,
    customer_store       TEXT NOT NULL,
    file_name            TEXT NOT NULL,
    content_type         TEXT NOT NULL,
    uploaded_by_user_id  TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_code, customer_store)
);

CREATE INDEX IF NOT EXISTS idx_pva_customer_avatars_identity
    ON pedidos_venda_abertos.customer_avatars (customer_code, customer_store);
