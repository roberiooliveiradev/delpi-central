BEGIN;

CREATE TABLE IF NOT EXISTS purchase_requests.daily_approval_reminders (
    reminder_date DATE NOT NULL,
    branch TEXT NOT NULL,
    request_number TEXT NOT NULL,
    user_id TEXT NOT NULL,
    recipient_role TEXT NOT NULL CHECK (recipient_role IN ('requester', 'approver')),
    claim_token UUID NOT NULL UNIQUE,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    result TEXT,
    PRIMARY KEY (reminder_date, branch, request_number, user_id, recipient_role)
);

COMMIT;
