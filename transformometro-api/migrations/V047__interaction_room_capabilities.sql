-- Recursos gerais da sala do processo: resposta, edição, leitura, reação, fixar, menção e anexo.
-- Sem mural, sem papel de membro e sem tabela comercial.
BEGIN;

ALTER TABLE transformometro.tm_interaction_messages
    ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES transformometro.tm_interaction_messages (id),
    ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_tm_interaction_messages_parent
    ON transformometro.tm_interaction_messages (parent_id);

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_mentions (
    message_id UUID NOT NULL REFERENCES transformometro.tm_interaction_messages (id) ON DELETE CASCADE,
    mentioned_user_id UUID NOT NULL,
    label TEXT NOT NULL,
    PRIMARY KEY (message_id, mentioned_user_id),
    CONSTRAINT tm_interaction_mentions_label_len CHECK (char_length(label) BETWEEN 1 AND 80)
);

CREATE INDEX IF NOT EXISTS idx_tm_interaction_mentions_user
    ON transformometro.tm_interaction_mentions (mentioned_user_id, message_id);

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_reactions (
    message_id UUID NOT NULL REFERENCES transformometro.tm_interaction_messages (id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (message_id, user_id, code),
    CONSTRAINT tm_interaction_reactions_code_len CHECK (char_length(code) BETWEEN 1 AND 32)
);

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_pins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES transformometro.tm_interaction_rooms (id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES transformometro.tm_interaction_messages (id) ON DELETE CASCADE,
    pinned_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tm_interaction_pins_message UNIQUE (room_id, message_id)
);

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_reads (
    room_id UUID NOT NULL REFERENCES transformometro.tm_interaction_rooms (id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    last_read_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (room_id, user_id)
);

CREATE TABLE IF NOT EXISTS transformometro.tm_interaction_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES transformometro.tm_interaction_messages (id) ON DELETE CASCADE,
    room_id UUID NOT NULL REFERENCES transformometro.tm_interaction_rooms (id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    stored_name TEXT NOT NULL,
    content_type TEXT NOT NULL,
    byte_size BIGINT NOT NULL CHECK (byte_size > 0),
    uploaded_by_user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tm_interaction_attachments_message
    ON transformometro.tm_interaction_attachments (message_id, created_at);

CREATE INDEX IF NOT EXISTS idx_tm_interaction_attachments_room
    ON transformometro.tm_interaction_attachments (room_id, created_at DESC);

COMMENT ON TABLE transformometro.tm_interaction_attachments IS
    'Anexo de uma mensagem da sala. Binário no volume da sala, não no Comercial.';
COMMENT ON COLUMN transformometro.tm_interaction_mentions.label IS
    'Texto do token @ usado na mensagem. Não é cargo nem e-mail.';

COMMIT;
