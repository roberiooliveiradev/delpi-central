BEGIN;

-- Snapshot do último estado de aprovação observado por SC (grão filial + C1_NUM).
-- A detecção é por mudança de estado (C1_APROV muda in-place no Protheus, sem
-- novo RECNO). ``notify_pending`` funciona como claim atômico: só uma
-- instância consegue reivindicar a transição; a linha só sai de pending após
-- entrega confirmada ou rejeição permanente, permitindo retry seguro.
CREATE TABLE IF NOT EXISTS purchase_requests.purchase_request_approval_states (
    branch CHAR(2) NOT NULL,
    request_number TEXT NOT NULL,
    requester_protheus_user_id TEXT,
    approval_status TEXT NOT NULL,
    approver_name TEXT,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notify_pending BOOLEAN NOT NULL DEFAULT FALSE,
    notify_claimed_at TIMESTAMPTZ,
    notified_at TIMESTAMPTZ,
    dispatch_attempts INTEGER NOT NULL DEFAULT 0,
    dispatch_result TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (branch, request_number)
);

CREATE INDEX IF NOT EXISTS idx_pr_approval_states_notify_pending
    ON purchase_requests.purchase_request_approval_states (notify_claimed_at)
    WHERE notify_pending;

COMMENT ON TABLE purchase_requests.purchase_request_approval_states IS
    'Último estado de aprovação conhecido por SC (agregado dos itens SC1); claim idempotente de notificação.';

COMMENT ON COLUMN purchase_requests.purchase_request_approval_states.observed_at IS
    'Quando o status atual foi observado pela primeira vez.';
COMMENT ON COLUMN purchase_requests.purchase_request_approval_states.notify_pending IS
    'Transição reivindicada aguardando confirmação de entrega ou retry.';
COMMENT ON COLUMN purchase_requests.purchase_request_approval_states.dispatch_result IS
    'delivered | skipped | superseded — último desfecho de dispatch.';

-- Novo evento de rejeição precisa entrar no CHECK da tabela de preferências.
ALTER TABLE purchase_requests.user_notification_subscriptions
    DROP CONSTRAINT purchase_requests_notification_event_key_check;

ALTER TABLE purchase_requests.user_notification_subscriptions
    ADD CONSTRAINT purchase_requests_notification_event_key_check CHECK (
        event_key IN (
            'purchase_order_created',
            'purchase_receipt_recorded',
            'purchase_request_approved',
            'purchase_request_rejected',
            'purchase_delivery_overdue'
        )
    );

COMMIT;
