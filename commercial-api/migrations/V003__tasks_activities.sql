-- Wave G / M2 parcial — tasks + activities (worklist).

CREATE TABLE IF NOT EXISTS commercial.tasks (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title                TEXT NOT NULL,
    description          TEXT,
    task_type            TEXT NOT NULL DEFAULT 'follow_up'
        CHECK (task_type IN ('follow_up', 'call', 'email', 'visit', 'internal', 'other')),
    status               TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'done', 'cancelled', 'deferred')),
    priority             TEXT NOT NULL DEFAULT 'normal'
        CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    due_at               TIMESTAMPTZ,
    completed_at         TIMESTAMPTZ,
    assignee_user_id     TEXT NOT NULL,
    created_by_user_id   TEXT NOT NULL,
    customer_code        TEXT,
    customer_store       TEXT,
    opportunity_id       UUID,
    prospect_id          UUID,
    related_entity_type  TEXT,
    related_entity_id    TEXT,
    version              INT NOT NULL DEFAULT 1,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at           TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_commercial_tasks_assignee_status_due
    ON commercial.tasks (assignee_user_id, status, due_at)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_commercial_tasks_customer
    ON commercial.tasks (customer_code, customer_store)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_commercial_tasks_open_due
    ON commercial.tasks (due_at)
    WHERE status = 'open' AND deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS commercial.activities (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_type    TEXT NOT NULL
        CHECK (activity_type IN ('call', 'email', 'meeting', 'visit', 'note', 'system')),
    subject          TEXT,
    body             TEXT,
    occurred_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_user_id    TEXT NOT NULL,
    customer_code    TEXT,
    customer_store   TEXT,
    prospect_id      UUID,
    opportunity_id   UUID,
    task_id          UUID REFERENCES commercial.tasks (id) ON DELETE SET NULL,
    metadata         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commercial_activities_customer_occurred
    ON commercial.activities (customer_code, customer_store, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_commercial_activities_task
    ON commercial.activities (task_id)
    WHERE task_id IS NOT NULL;
