-- PAC Qualidade DELPI — núcleo transacional (Fase 1)
-- Schema de dados: quality (compartilhado com kaizen, auditoria 5S, etc.)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS quality;

CREATE TABLE IF NOT EXISTS quality.quality_action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(30) NOT NULL,
    title VARCHAR(500) NOT NULL,
    customer_name VARCHAR(300),
    customer_contact VARCHAR(300),
    source_type VARCHAR(50),
    source_reference VARCHAR(500),
    product_code VARCHAR(50),
    product_description VARCHAR(500),
    batch_number VARCHAR(100),
    reported_problem TEXT,
    detected_at TIMESTAMPTZ,
    reported_at TIMESTAMPTZ,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(40) NOT NULL DEFAULT 'draft',
    created_by_user_id VARCHAR(100) NOT NULL,
    owner_user_id VARCHAR(100),
    department VARCHAR(200),
    problem_category VARCHAR(200),
    symptom_tags TEXT[] NOT NULL DEFAULT '{}',
    root_cause_category VARCHAR(200),
    failure_mode VARCHAR(300),
    effectiveness_status VARCHAR(30),
    effectiveness_verified_at TIMESTAMPTZ,
    effectiveness_notes TEXT,
    recurrence_key VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,

    CONSTRAINT uq_quality_action_plans_code UNIQUE (code),
    CONSTRAINT ck_quality_action_plans_severity CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT ck_quality_action_plans_status CHECK (
        status IN (
            'draft',
            'triage',
            'containment',
            'root_cause_analysis',
            'action_plan_defined',
            'in_progress',
            'waiting_validation',
            'completed',
            'cancelled'
        )
    ),
    CONSTRAINT ck_quality_action_plans_source_type CHECK (
        source_type IS NULL OR source_type IN (
            'email',
            'message',
            'spreadsheet',
            'pdf',
            'image',
            'manual_text',
            'system_reference',
            'other'
        )
    ),
    CONSTRAINT ck_quality_action_plans_effectiveness_status CHECK (
        effectiveness_status IS NULL OR effectiveness_status IN (
            'pending',
            'effective',
            'partially_effective',
            'ineffective',
            'not_verified'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_status
    ON quality.quality_action_plans (status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_product_code
    ON quality.quality_action_plans (product_code)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_customer_name
    ON quality.quality_action_plans (customer_name)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_owner
    ON quality.quality_action_plans (owner_user_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_recurrence_key
    ON quality.quality_action_plans (recurrence_key)
    WHERE deleted_at IS NULL AND recurrence_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS quality.quality_problem_evidences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    file_name VARCHAR(500),
    file_url TEXT,
    text_excerpt TEXT,
    uploaded_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_problem_evidences_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_quality_problem_evidences_type CHECK (
        type IN (
            'email',
            'message',
            'spreadsheet',
            'pdf',
            'image',
            'manual_text',
            'system_reference',
            'other'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_problem_evidences_plan
    ON quality.quality_problem_evidences (plan_id);

CREATE TABLE IF NOT EXISTS quality.quality_ishikawa_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL UNIQUE,
    machine TEXT,
    method_process TEXT,
    material TEXT,
    manpower TEXT,
    measurement TEXT,
    environment TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_ishikawa_analysis_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quality.quality_five_whys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL UNIQUE,
    why_1 TEXT,
    why_2 TEXT,
    why_3 TEXT,
    why_4 TEXT,
    why_5 TEXT,
    root_cause TEXT,
    confidence_level VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_five_whys_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_quality_five_whys_confidence CHECK (
        confidence_level IS NULL OR confidence_level IN ('low', 'medium', 'high')
    )
);

CREATE TABLE IF NOT EXISTS quality.quality_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    action_type VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    responsible_user_id VARCHAR(100),
    responsible_name VARCHAR(200),
    department VARCHAR(200),
    due_date DATE,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    evidence_required BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_actions_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_quality_actions_type CHECK (
        action_type IN (
            'containment',
            'corrective',
            'preventive',
            'verification',
            'standardization',
            'training'
        )
    ),
    CONSTRAINT ck_quality_actions_status CHECK (
        status IN ('pending', 'in_progress', 'blocked', 'completed', 'cancelled', 'overdue')
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_actions_plan
    ON quality.quality_actions (plan_id);

CREATE INDEX IF NOT EXISTS ix_quality_actions_due_date
    ON quality.quality_actions (due_date)
    WHERE status NOT IN ('completed', 'cancelled');

CREATE TABLE IF NOT EXISTS quality.quality_action_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    comment TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_action_history_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_quality_action_history_event_type CHECK (
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
            'plan_closed',
            'plan_reopened'
        )
    )
);

CREATE INDEX IF NOT EXISTS ix_quality_action_history_plan
    ON quality.quality_action_history (plan_id, created_at DESC);
