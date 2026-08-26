BEGIN;

CREATE TABLE IF NOT EXISTS purchase_requests.user_notification_subscriptions (
    user_id TEXT NOT NULL,
    event_key TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, event_key),
    CONSTRAINT purchase_requests_notification_event_key_check CHECK (
        event_key IN (
            'purchase_order_created',
            'purchase_receipt_recorded',
            'purchase_request_approved',
            'purchase_delivery_overdue'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_purchase_requests_notification_subscriptions_user
    ON purchase_requests.user_notification_subscriptions (user_id);

COMMENT ON TABLE purchase_requests.user_notification_subscriptions IS
    'Preferências de notificação por usuário do portal e tipo de evento operacional de SC.';

COMMIT;
