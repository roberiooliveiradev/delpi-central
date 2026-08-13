-- Multi assignee / multi customer on tasks (mirror first on commercial.tasks).

CREATE TABLE IF NOT EXISTS commercial.task_assignees (
    task_id     UUID NOT NULL REFERENCES commercial.tasks (id) ON DELETE CASCADE,
    user_id     TEXT NOT NULL,
    sort_order  INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (task_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_commercial_task_assignees_user
    ON commercial.task_assignees (user_id, task_id);

CREATE TABLE IF NOT EXISTS commercial.task_customers (
    task_id         UUID NOT NULL REFERENCES commercial.tasks (id) ON DELETE CASCADE,
    customer_code   TEXT NOT NULL,
    customer_store  TEXT NOT NULL,
    customer_name   TEXT,
    sort_order      INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (task_id, customer_code, customer_store)
);

CREATE INDEX IF NOT EXISTS idx_commercial_task_customers_customer
    ON commercial.task_customers (customer_code, customer_store);

-- Backfill from legacy singular columns.
INSERT INTO commercial.task_assignees (task_id, user_id, sort_order)
SELECT id, assignee_user_id, 0
  FROM commercial.tasks
 WHERE deleted_at IS NULL
   AND assignee_user_id IS NOT NULL
   AND BTRIM(assignee_user_id) <> ''
ON CONFLICT DO NOTHING;

INSERT INTO commercial.task_customers (
    task_id, customer_code, customer_store, customer_name, sort_order
)
SELECT id, customer_code, customer_store, NULL, 0
  FROM commercial.tasks
 WHERE deleted_at IS NULL
   AND customer_code IS NOT NULL
   AND BTRIM(customer_code) <> ''
   AND customer_store IS NOT NULL
   AND BTRIM(customer_store) <> ''
ON CONFLICT DO NOTHING;
