-- Lançamento de Notas Fiscais — vários pedidos de compra amarrados
-- Schema: lancamento_notas_fiscais
-- Não altera V004; colunas linked_po_* permanecem (legado / espelho do primeiro vínculo).

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_request_linked_pos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests(id) ON DELETE CASCADE,
    order_number VARCHAR(20) NOT NULL,
    delivery_date DATE,
    issue_date DATE,
    open_value NUMERIC(18, 2),
    product_count INTEGER,
    linked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    linked_by_user_id VARCHAR(100),
    linked_by_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_request_linked_pos IS
    'Pedidos de compra (PC + data de entrega) amarrados à solicitação — N por request.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_lnf_linked_pos_request_order_delivery
    ON lancamento_notas_fiscais.invoice_posting_request_linked_pos (
        request_id,
        order_number,
        (COALESCE(delivery_date, DATE '0001-01-01'))
    );

CREATE INDEX IF NOT EXISTS ix_lnf_linked_pos_request_id
    ON lancamento_notas_fiscais.invoice_posting_request_linked_pos (request_id);

-- Backfill a partir do vínculo singular V004
INSERT INTO lancamento_notas_fiscais.invoice_posting_request_linked_pos (
    request_id,
    order_number,
    delivery_date,
    issue_date,
    open_value,
    product_count,
    linked_at,
    linked_by_user_id,
    linked_by_name
)
SELECT
    r.id,
    r.linked_po_number,
    r.linked_po_delivery_date,
    r.linked_po_issue_date,
    r.linked_po_open_value,
    r.linked_po_product_count,
    COALESCE(r.linked_po_linked_at, NOW()),
    r.linked_po_linked_by_user_id,
    r.linked_po_linked_by_name
FROM lancamento_notas_fiscais.invoice_posting_requests r
WHERE r.linked_po_number IS NOT NULL
  AND BTRIM(r.linked_po_number) <> ''
  AND NOT EXISTS (
        SELECT 1
          FROM lancamento_notas_fiscais.invoice_posting_request_linked_pos lp
         WHERE lp.request_id = r.id
           AND lp.order_number = r.linked_po_number
           AND COALESCE(lp.delivery_date, DATE '0001-01-01')
             = COALESCE(r.linked_po_delivery_date, DATE '0001-01-01')
    );
