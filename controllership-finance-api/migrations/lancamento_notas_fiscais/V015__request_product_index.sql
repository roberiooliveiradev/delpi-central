-- Índice de produtos efetivos das NF-e recebidas (código fornecedor → código Delpi).
-- V015 mantém o histórico V001–V014 intocado; sem alteração no Protheus.
CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_request_products (
    request_id UUID NOT NULL REFERENCES lancamento_notas_fiscais.invoice_posting_requests (id)
        ON DELETE CASCADE,
    item_position INTEGER NOT NULL CHECK (item_position > 0),
    supplier_product_code VARCHAR(60),
    internal_product_code VARCHAR(40),
    mapping_status VARCHAR(20) NOT NULL
        CHECK (mapping_status IN ('mapped', 'unmapped', 'ambiguous')),
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (request_id, item_position)
);

CREATE INDEX IF NOT EXISTS ix_lnf_request_products_delpi
    ON lancamento_notas_fiscais.invoice_posting_request_products
        (upper(btrim(internal_product_code)), request_id)
    WHERE internal_product_code IS NOT NULL;

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_request_products IS
    'Itens observados no XML NF-e com emitente validado contra SA2 e correspondência SA5; não inferir material recebido pelo PC.';
