-- Sala de interação do Transformômetro, uma por processo.
-- Identificadores de usuário são Core, sem FK cross-context.
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id UUID NOT NULL REFERENCES transformometro.processos (processo_id),
    created_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tm_interaction_rooms_processo UNIQUE (processo_id)
);

CREATE INDEX IF NOT EXISTS idx_tm_interaction_rooms_updated
    ON transformometro.tm_interaction_rooms (updated_at DESC);

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES transformometro.tm_interaction_rooms (id) ON DELETE CASCADE,
    author_user_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT tm_interaction_messages_content_not_blank CHECK (btrim(content) <> ''),
    CONSTRAINT tm_interaction_messages_content_len CHECK (char_length(content) <= 4000)
);

CREATE INDEX IF NOT EXISTS idx_tm_interaction_messages_room_created
    ON transformometro.tm_interaction_messages (room_id, created_at ASC, id ASC);

COMMENT ON TABLE transformometro.tm_interaction_rooms IS
    'Sala de interação de um processo do Transformômetro. Não é sala comercial.';
COMMENT ON COLUMN transformometro.tm_interaction_rooms.created_by_user_id IS
    'Identificador Core de quem abriu a sala. Não é nome nem cargo.';
COMMENT ON COLUMN transformometro.tm_interaction_messages.author_user_id IS
    'Identificador Core do autor. Não é nome nem cargo.';
COMMENT ON COLUMN transformometro.tm_interaction_messages.content IS
    'Texto puro. Sem HTML.';

COMMIT;
