-- #1618. Append-only delivery ledger para retornos; não alterar checksum V007.
-- Armazenar somente prévia sanitizada, nunca o HTML original ou credenciais.
CREATE TABLE IF NOT EXISTS helpdesk.followup_ticket_notification_outbox (
    event_key TEXT PRIMARY KEY,
    ticket_id BIGINT NOT NULL CHECK (ticket_id > 0),
    followup_id BIGINT NOT NULL CHECK (followup_id > 0),
    recipient_user_id UUID NOT NULL,
    ticket_title VARCHAR(250) NOT NULL DEFAULT '',
    preview VARCHAR(160) NOT NULL DEFAULT '',
    status VARCHAR(16) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'ignored')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_attempt_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    UNIQUE(ticket_id, followup_id)
);
CREATE INDEX IF NOT EXISTS idx_helpdesk_followup_notification_due
    ON helpdesk.followup_ticket_notification_outbox (next_attempt_at, created_at)
    WHERE status = 'pending';
