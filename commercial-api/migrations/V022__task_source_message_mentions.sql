-- E7.S2b — snapshot de menções da mensagem de origem na tarefa da sala.

ALTER TABLE commercial.tasks
    ADD COLUMN IF NOT EXISTS source_message_mentions JSONB NOT NULL DEFAULT '[]'::jsonb;

COMMENT ON COLUMN commercial.tasks.source_message_mentions IS
    'Snapshot das menções (@) da mensagem de origem ao criar tarefa da sala.';
