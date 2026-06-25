-- Onda 4.1 — controle de deduplicação de notificações PAC

CREATE TABLE IF NOT EXISTS quality.quality_notification_dispatches (
    notification_key VARCHAR(200) PRIMARY KEY,
    event_type VARCHAR(80) NOT NULL,
    recipient_user_id VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id UUID,
    dispatched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quality_notification_dispatches_entity
    ON quality.quality_notification_dispatches (entity_type, entity_id, dispatched_at DESC);

CREATE INDEX IF NOT EXISTS idx_quality_notification_dispatches_recipient
    ON quality.quality_notification_dispatches (recipient_user_id, dispatched_at DESC);

COMMENT ON TABLE quality.quality_notification_dispatches IS
    'Chaves de notificação PAC já enviadas (evita duplicar alertas in-app).';
