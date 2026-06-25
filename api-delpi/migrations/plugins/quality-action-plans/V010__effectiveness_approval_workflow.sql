-- Onda 4.3 — workflow analista → coordenador para verificação de eficácia

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS effectiveness_approval_status VARCHAR(30),
    ADD COLUMN IF NOT EXISTS effectiveness_proposed_status VARCHAR(30),
    ADD COLUMN IF NOT EXISTS effectiveness_submitted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS effectiveness_submitted_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS effectiveness_reviewed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS effectiveness_reviewed_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS effectiveness_rejection_reason TEXT;

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS ck_quality_effectiveness_approval_status;

ALTER TABLE quality.quality_action_plans
    ADD CONSTRAINT ck_quality_effectiveness_approval_status CHECK (
        effectiveness_approval_status IS NULL
        OR effectiveness_approval_status IN ('pending_review', 'approved', 'rejected')
    );

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_effectiveness_pending
    ON quality.quality_action_plans (effectiveness_submitted_at)
    WHERE deleted_at IS NULL AND effectiveness_approval_status = 'pending_review';

ALTER TABLE quality.quality_action_history
    DROP CONSTRAINT IF EXISTS ck_quality_action_history_event_type;

ALTER TABLE quality.quality_action_history
    ADD CONSTRAINT ck_quality_action_history_event_type CHECK (
        event_type IN (
            'plan_created',
            'plan_updated',
            'status_changed',
            'action_created',
            'action_updated',
            'action_completed',
            'ishikawa_updated',
            'five_whys_updated',
            'effectiveness_reviewed',
            'effectiveness_submitted',
            'effectiveness_approval_rejected',
            'plan_closed',
            'plan_reopened'
        )
    );
