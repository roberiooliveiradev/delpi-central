-- Persist who closed a request into a terminal success/reject outcome (completed_at path).
BEGIN;

ALTER TABLE my_requests.requests
    ADD COLUMN IF NOT EXISTS completed_by_user_id VARCHAR(100),
    ADD COLUMN IF NOT EXISTS completed_by_name VARCHAR(200);

CREATE INDEX IF NOT EXISTS ix_requests_completed_by_user
    ON my_requests.requests (completed_by_user_id)
    WHERE completed_by_user_id IS NOT NULL;

-- Backfill from the latest history row that entered completed/rejected.
UPDATE my_requests.requests AS r
SET
    completed_by_user_id = h.actor_user_id,
    completed_by_name = h.actor_name
FROM (
    SELECT DISTINCT ON (request_id)
        request_id,
        actor_user_id,
        actor_name
    FROM my_requests.request_status_history
    WHERE to_status IN ('completed', 'rejected')
      AND actor_user_id IS NOT NULL
      AND length(trim(actor_user_id)) > 0
    ORDER BY request_id, created_at DESC
) AS h
WHERE r.id = h.request_id
  AND r.completed_at IS NOT NULL
  AND (r.completed_by_user_id IS NULL OR length(trim(r.completed_by_user_id)) = 0);

COMMIT;
