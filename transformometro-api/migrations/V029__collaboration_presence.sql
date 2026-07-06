-- Presença e travas de edição colaborativa (cadastro Transformômetro)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.collaboration_presence (
    presence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(32) NOT NULL,
    entity_id UUID NOT NULL,
    section_key VARCHAR(64) NOT NULL DEFAULT '',
    user_id VARCHAR(128) NOT NULL,
    user_name VARCHAR(256),
    user_email VARCHAR(256),
    mode VARCHAR(16) NOT NULL DEFAULT 'viewing',
    heartbeat_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    lock_expires_at TIMESTAMPTZ,
    CONSTRAINT collaboration_presence_mode_chk CHECK (mode IN ('viewing', 'editing')),
    CONSTRAINT collaboration_presence_entity_section_user_uq
        UNIQUE (entity_type, entity_id, section_key, user_id)
);

CREATE INDEX IF NOT EXISTS idx_collaboration_presence_entity
    ON transformometro.collaboration_presence (entity_type, entity_id, heartbeat_at DESC);

COMMENT ON TABLE transformometro.collaboration_presence IS
    'Presença e trava soft por seção (processo, instância, revisão) — heartbeat + lock TTL.';

COMMIT;
