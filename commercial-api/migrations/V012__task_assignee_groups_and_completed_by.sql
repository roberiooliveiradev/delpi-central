-- Task assignee groups + completed_by (Portal Comercial E6).
-- Do not expand group members into task_assignees; visibility uses current membership.

ALTER TABLE commercial.tasks
    ADD COLUMN IF NOT EXISTS completed_by_user_id TEXT NULL;

CREATE TABLE IF NOT EXISTS commercial.task_assignee_groups (
    task_id     UUID NOT NULL
        REFERENCES commercial.tasks (id) ON DELETE CASCADE,
    group_id    UUID NOT NULL
        REFERENCES commercial.commercial_groups (id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (task_id, group_id)
);

CREATE INDEX IF NOT EXISTS idx_commercial_task_assignee_groups_group
    ON commercial.task_assignee_groups (group_id, task_id);

CREATE INDEX IF NOT EXISTS idx_commercial_tasks_completed_by
    ON commercial.tasks (completed_by_user_id)
    WHERE completed_by_user_id IS NOT NULL AND deleted_at IS NULL;
