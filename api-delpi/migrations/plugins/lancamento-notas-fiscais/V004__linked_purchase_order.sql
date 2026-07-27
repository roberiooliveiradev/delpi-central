-- Lançamento de Notas Fiscais — vínculo de pedido de compra (PC + data entrega)
-- Schema: lancamento_notas_fiscais

ALTER TABLE lancamento_notas_fiscais.invoice_posting_requests
    ADD COLUMN IF NOT EXISTS linked_po_number VARCHAR(20),
    ADD COLUMN IF NOT EXISTS linked_po_delivery_date DATE,
    ADD COLUMN IF NOT EXISTS linked_po_issue_date DATE,
    ADD COLUMN IF NOT EXISTS linked_po_open_value NUMERIC(18, 2),
    ADD COLUMN IF NOT EXISTS linked_po_product_count INTEGER,
    ADD COLUMN IF NOT EXISTS linked_po_linked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS linked_po_linked_by_user_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS linked_po_linked_by_name VARCHAR(200);

COMMENT ON COLUMN lancamento_notas_fiscais.invoice_posting_requests.linked_po_number IS
    'Número do pedido de compra (SC7 C7_NUM) amarrado à solicitação.';
COMMENT ON COLUMN lancamento_notas_fiscais.invoice_posting_requests.linked_po_delivery_date IS
    'Data de entrega do grupo amarrado (NULL = sem data de entrega no Protheus).';
