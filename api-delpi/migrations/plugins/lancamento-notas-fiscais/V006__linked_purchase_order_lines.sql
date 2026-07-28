-- Lançamento de Notas Fiscais — linhas SC7 selecionadas por PC amarrado
-- Schema: lancamento_notas_fiscais
-- Não altera V005; ausência de linhas = grupo inteiro (compatível).

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_request_linked_po_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linked_po_id UUID NOT NULL
        REFERENCES lancamento_notas_fiscais.invoice_posting_request_linked_pos(id)
        ON DELETE CASCADE,
    order_item VARCHAR(20) NOT NULL,
    product_code VARCHAR(40),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_request_linked_po_lines IS
    'Itens (C7_ITEM) do PC amarrados à solicitação; vazio no header = grupo inteiro.';

CREATE UNIQUE INDEX IF NOT EXISTS uq_lnf_linked_po_lines_po_item
    ON lancamento_notas_fiscais.invoice_posting_request_linked_po_lines (
        linked_po_id,
        order_item
    );

CREATE INDEX IF NOT EXISTS ix_lnf_linked_po_lines_linked_po_id
    ON lancamento_notas_fiscais.invoice_posting_request_linked_po_lines (linked_po_id);
