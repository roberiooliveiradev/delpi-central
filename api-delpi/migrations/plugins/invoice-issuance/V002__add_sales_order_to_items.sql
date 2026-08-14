-- Invoice issuance — vínculo opcional item × pedido de venda (SC6)
-- Aplicar somente com `up`. Nunca editar V001.

ALTER TABLE invoice_issuance.invoice_issuance_request_items
    ADD COLUMN IF NOT EXISTS sales_order VARCHAR(20),
    ADD COLUMN IF NOT EXISTS sales_order_item VARCHAR(6),
    ADD COLUMN IF NOT EXISTS customer_order_number VARCHAR(60);

COMMENT ON COLUMN invoice_issuance.invoice_issuance_request_items.sales_order IS
    'Número do pedido de venda TOTVS (SC5.C5_NUM), quando o item veio de saldo em aberto.';
COMMENT ON COLUMN invoice_issuance.invoice_issuance_request_items.sales_order_item IS
    'Item do pedido de venda (SC6), quando aplicável.';
COMMENT ON COLUMN invoice_issuance.invoice_issuance_request_items.customer_order_number IS
    'Pedido informado pelo cliente (pedido_cliente da view de PV em aberto).';
