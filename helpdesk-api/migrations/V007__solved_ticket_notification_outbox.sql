-- #1616. Delivery ledger isolado do GLPI e da tabela de notificações Core.
-- Nunca armazenar tokens GLPI, credenciais ou texto da solução neste outbox.
CREATE TABLE IF NOT EXISTS helpdesk.solved_ticket_notification_outbox (
    event_key TEXT PRIMARY KEY,
    ticket_id BIGINT NOT NULL CHECK (ticket_id > 0),
    solution_id BIGINT NOT NULL CHECK (solution_id > 0),
    recipient_user_id UUID NOT NULL,
    ticket_title VARCHAR(250) NOT NULL DEFAULT '',
    status VARCHAR(16) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'ignored')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_attempt_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    UNIQUE(ticket_id, solution_id)
);

CREATE INDEX IF NOT EXISTS idx_helpdesk_solved_notification_due
    ON helpdesk.solved_ticket_notification_outbox (next_attempt_at, created_at)
    WHERE status = 'pending';
