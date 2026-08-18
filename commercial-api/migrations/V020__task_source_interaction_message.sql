-- E8 — vínculo tarefa ← mensagem da sala de interação.

ALTER TABLE commercial.tasks
    ADD COLUMN IF NOT EXISTS source_interaction_message_id UUID;

CREATE INDEX IF NOT EXISTS idx_commercial_tasks_source_interaction_message
    ON commercial.tasks (source_interaction_message_id)
    WHERE source_interaction_message_id IS NOT NULL AND deleted_at IS NULL;

COMMENT ON COLUMN commercial.tasks.source_interaction_message_id IS
    'Mensagem da interaction room que originou a tarefa (create_task_from_interaction_message).';
