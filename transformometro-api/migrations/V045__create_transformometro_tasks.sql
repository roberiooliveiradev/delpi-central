-- Transformômetro — tarefas manuais do portal (set/2026)
-- Referências de usuário são identidade Core, sem FK cross-context.
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.tm_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    assignee_user_id UUID NOT NULL,
    created_by_user_id UUID NOT NULL,
    due_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    CONSTRAINT tm_tasks_title_not_blank CHECK (btrim(title) <> ''),
    CONSTRAINT tm_tasks_status_check CHECK (status IN ('pending', 'completed', 'cancelled')),
    CONSTRAINT tm_tasks_completed_at_matches CHECK (
        (status = 'completed' AND completed_at IS NOT NULL)
        OR (status <> 'completed' AND completed_at IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_tm_tasks_assignee_status
    ON transformometro.tm_tasks (assignee_user_id, status);

CREATE INDEX IF NOT EXISTS idx_tm_tasks_due_date
    ON transformometro.tm_tasks (due_date)
    WHERE due_date IS NOT NULL AND status = 'pending';

COMMENT ON TABLE transformometro.tm_tasks IS
    'Tarefa manual do Portal Transforma+. Não materializa assinatura de ata.';
COMMENT ON COLUMN transformometro.tm_tasks.assignee_user_id IS
    'Identificador Core do responsável. Não é nome nem cargo.';

COMMIT;
