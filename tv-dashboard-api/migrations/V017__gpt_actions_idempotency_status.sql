BEGIN;

-- Atomic acquire support for GPT commit idempotency (V016 table).
ALTER TABLE tv_dashboard.gpt_actions_idempotency_keys
  ADD COLUMN IF NOT EXISTS status VARCHAR(32) NOT NULL DEFAULT 'completed';

ALTER TABLE tv_dashboard.gpt_actions_idempotency_keys
  DROP CONSTRAINT IF EXISTS gpt_actions_idempotency_status_check;

ALTER TABLE tv_dashboard.gpt_actions_idempotency_keys
  ADD CONSTRAINT gpt_actions_idempotency_status_check
  CHECK (status IN ('in_progress', 'completed'));

COMMIT;
