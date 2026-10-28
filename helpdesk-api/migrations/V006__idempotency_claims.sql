-- Idempotency claim protocol: a key is atomically claimed BEFORE the
-- external side effect and marked completed AFTER the governed result
-- is known. A row stuck 'in_flight' means a prior execution may have
-- persisted the write — same-key retries must fail closed instead of
-- re-executing blindly.
ALTER TABLE helpdesk.idempotency_keys
    ALTER COLUMN response_status DROP NOT NULL,
    ALTER COLUMN response_body DROP NOT NULL,
    ADD COLUMN IF NOT EXISTS state TEXT NOT NULL DEFAULT 'completed',
    ADD COLUMN IF NOT EXISTS intent JSONB,
    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

ALTER TABLE helpdesk.idempotency_keys
    DROP CONSTRAINT IF EXISTS idempotency_keys_state_check,
    ADD CONSTRAINT idempotency_keys_state_check
        CHECK (state IN ('in_flight', 'completed'));

UPDATE helpdesk.idempotency_keys
   SET claimed_at = created_at,
       completed_at = created_at
 WHERE claimed_at IS NULL;
