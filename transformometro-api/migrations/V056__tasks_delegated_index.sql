-- Transformômetro — listagem "Atribuídas por mim" (created_by != assignee).
-- Espelha idx_tm_tasks_assignee_status para a consulta por criador.
BEGIN;

CREATE INDEX IF NOT EXISTS idx_tm_tasks_created_by_status
    ON transformometro.tm_tasks (created_by_user_id, status);

COMMIT;
