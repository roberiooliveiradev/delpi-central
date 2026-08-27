BEGIN;

CREATE TABLE IF NOT EXISTS purchase_requests.dispatched_purchase_receipt_events (
    branch CHAR(2) NOT NULL,
    invoice_number TEXT NOT NULL,
    invoice_series TEXT NOT NULL DEFAULT '',
    invoice_item TEXT NOT NULL,
    request_number TEXT,
    order_number TEXT,
    recno BIGINT,
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (branch, invoice_number, invoice_series, invoice_item)
);

COMMENT ON TABLE purchase_requests.dispatched_purchase_receipt_events IS
    'Dedupe persistido: 1 aviso por linha de NF de entrada (filial + D1_DOC + D1_SERIE + D1_ITEM).';

COMMIT;
