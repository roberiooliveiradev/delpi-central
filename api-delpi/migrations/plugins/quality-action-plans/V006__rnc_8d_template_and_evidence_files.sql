-- Relatório 8D (materiais adquiridos) — template do cliente, equipe, trilha dupla de 5 Porquês e evidências

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS customer_template VARCHAR(50) NOT NULL DEFAULT 'generic',
    ADD COLUMN IF NOT EXISTS client_nc_registry VARCHAR(100),
    ADD COLUMN IF NOT EXISTS template_payload JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS ck_quality_action_plans_customer_template;

ALTER TABLE quality.quality_action_plans
    ADD CONSTRAINT ck_quality_action_plans_customer_template CHECK (
        customer_template IN ('generic', 'rnc_8d')
    );

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_customer_template
    ON quality.quality_action_plans (customer_template)
    WHERE deleted_at IS NULL;

COMMENT ON COLUMN quality.quality_action_plans.customer_template IS
    'Formulário do cliente: generic (PAC padrão) ou rnc_8d (relatório 8D materiais adquiridos).';

COMMENT ON COLUMN quality.quality_action_plans.client_nc_registry IS
    'Número de registro da NC no cliente (ex.: 215571003).';

COMMENT ON COLUMN quality.quality_action_plans.template_payload IS
    'Campos estruturados do template do cliente (contenção, preventiva, documentação, etc.).';

ALTER TABLE quality.quality_five_whys
    ADD COLUMN IF NOT EXISTS detection_why_1 TEXT,
    ADD COLUMN IF NOT EXISTS detection_why_2 TEXT,
    ADD COLUMN IF NOT EXISTS detection_why_3 TEXT,
    ADD COLUMN IF NOT EXISTS detection_why_4 TEXT,
    ADD COLUMN IF NOT EXISTS detection_why_5 TEXT;

ALTER TABLE quality.quality_actions
    ADD COLUMN IF NOT EXISTS cause_track VARCHAR(20);

ALTER TABLE quality.quality_actions
    DROP CONSTRAINT IF EXISTS ck_quality_actions_cause_track;

ALTER TABLE quality.quality_actions
    ADD CONSTRAINT ck_quality_actions_cause_track CHECK (
        cause_track IS NULL OR cause_track IN ('occurrence', 'detection')
    );

CREATE TABLE IF NOT EXISTS quality.quality_analysis_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    member_name VARCHAR(200) NOT NULL,
    department VARCHAR(200),
    is_leader BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_analysis_team_members_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_quality_analysis_team_members_plan
    ON quality.quality_analysis_team_members (plan_id, sort_order);

ALTER TABLE quality.quality_problem_evidences
    ADD COLUMN IF NOT EXISTS stored_name VARCHAR(500),
    ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
    ADD COLUMN IF NOT EXISTS size_bytes BIGINT,
    ADD COLUMN IF NOT EXISTS section VARCHAR(50) NOT NULL DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS description TEXT,
    ADD COLUMN IF NOT EXISTS knowledge_visible BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE quality.quality_problem_evidences
    DROP CONSTRAINT IF EXISTS ck_quality_problem_evidences_section;

ALTER TABLE quality.quality_problem_evidences
    ADD CONSTRAINT ck_quality_problem_evidences_section CHECK (
        section IN (
            'general',
            'nc_description',
            'containment',
            'root_cause',
            'corrective',
            'effectiveness',
            'preventive',
            'documentation',
            'attachments'
        )
    );

COMMENT ON COLUMN quality.quality_problem_evidences.knowledge_visible IS
    'Se true, entra no repositório de conhecimento do caso (busca por agente/usuário).';
