-- Traceability: tarefa criada a partir de mensagem da sala (1:N).
BEGIN;

ALTER TABLE transformometro.tm_tasks
    ADD COLUMN IF NOT EXISTS source_interaction_message_id UUID
        REFERENCES transformometro.tm_interaction_messages (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tm_tasks_source_interaction_message
    ON transformometro.tm_tasks (source_interaction_message_id)
    WHERE source_interaction_message_id IS NOT NULL;

COMMENT ON COLUMN transformometro.tm_tasks.source_interaction_message_id IS
    'Mensagem de origem quando a tarefa nasce da Sala de interação. Sem status duplicado na mensagem.';

COMMIT;
