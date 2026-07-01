-- Revisões versionadas de planos PAC (snapshots restauráveis)

CREATE TABLE IF NOT EXISTS quality.quality_action_plan_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    revision_number INTEGER NOT NULL,
    snapshot_schema_version INTEGER NOT NULL DEFAULT 1,
    snapshot JSONB NOT NULL,
    change_scope VARCHAR(50) NOT NULL,
    change_summary VARCHAR(500),
    restored_from_revision INTEGER,
    created_by VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(300),
    created_by_email VARCHAR(300),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_action_plan_revisions_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT uq_quality_action_plan_revisions_plan_number
        UNIQUE (plan_id, revision_number),

    CONSTRAINT ck_quality_action_plan_revisions_scope CHECK (
        change_scope IN (
            'created',
            'identification',
            'status',
            'ishikawa',
            'five_whys',
            'rnc_8d',
            'actions',
            'effectiveness',
            'restore'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_action_plan_revisions_plan_created
    ON quality.quality_action_plan_revisions (plan_id, created_at DESC);

COMMENT ON TABLE quality.quality_action_plan_revisions IS
    'Snapshots JSON restauráveis do agregado PAC (plano + análises + ações + 8D).';

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS current_revision_number INTEGER NOT NULL DEFAULT 0;

ALTER TABLE quality.quality_action_history
    DROP CONSTRAINT IF EXISTS ck_quality_action_history_event_type;

ALTER TABLE quality.quality_action_history
    ADD CONSTRAINT ck_quality_action_history_event_type CHECK (
        event_type IN (
            'plan_created',
            'plan_updated',
            'plan_deleted',
            'plan_revision_restored',
            'status_changed',
            'action_created',
            'action_updated',
            'action_completed',
            'action_deleted',
            'ishikawa_updated',
            'five_whys_updated',
            'effectiveness_reviewed',
            'effectiveness_submitted',
            'effectiveness_approval_rejected',
            'plan_closed',
            'plan_reopened'
        )
    );
