BEGIN;

CREATE TABLE IF NOT EXISTS purchase_requests.notification_cursors (
    job_key TEXT PRIMARY KEY,
    last_recno BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE purchase_requests.notification_cursors IS
    'Watermark incremental (SC7.R_E_C_N_O_) dos jobs de notificação de SC.';

CREATE TABLE IF NOT EXISTS purchase_requests.dispatched_purchase_order_events (
    branch CHAR(2) NOT NULL,
    order_number TEXT NOT NULL,
    order_item TEXT NOT NULL,
    request_number TEXT,
    recno BIGINT,
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (branch, order_number, order_item)
);

COMMENT ON TABLE purchase_requests.dispatched_purchase_order_events IS
    'Dedupe persistido: 1 aviso por linha de PC (filial + C7_NUM + C7_ITEM).';

COMMIT;
