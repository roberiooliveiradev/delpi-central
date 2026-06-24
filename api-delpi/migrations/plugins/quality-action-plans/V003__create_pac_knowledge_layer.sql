-- Knowledge Layer PAC — padrões de solução e índice de similaridade (Fase 2)

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS quality.quality_solution_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    problem_category VARCHAR(200),
    failure_mode VARCHAR(300),
    root_cause_category VARCHAR(200),
    symptom_tags TEXT[] NOT NULL DEFAULT '{}',
    recommended_actions TEXT[] NOT NULL DEFAULT '{}',
    actions_to_avoid TEXT[] NOT NULL DEFAULT '{}',
    evidence_summary TEXT,
    effectiveness_rate NUMERIC(5, 4),
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_from_plan_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_quality_solution_patterns_plan
        FOREIGN KEY (created_from_plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE SET NULL,

    CONSTRAINT ck_quality_solution_patterns_usage_count
        CHECK (usage_count >= 0),

    CONSTRAINT ck_quality_solution_patterns_effectiveness_rate
        CHECK (
            effectiveness_rate IS NULL
            OR (effectiveness_rate >= 0 AND effectiveness_rate <= 1)
        )
);

CREATE INDEX IF NOT EXISTS ix_quality_solution_patterns_failure_mode
    ON quality.quality_solution_patterns (failure_mode);

CREATE INDEX IF NOT EXISTS ix_quality_solution_patterns_problem_category
    ON quality.quality_solution_patterns (problem_category);

CREATE INDEX IF NOT EXISTS ix_quality_solution_patterns_symptom_tags
    ON quality.quality_solution_patterns USING GIN (symptom_tags);

CREATE TABLE IF NOT EXISTS quality.quality_case_similarity_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL,
    search_text TEXT NOT NULL,
    product_code VARCHAR(50),
    customer_name VARCHAR(300),
    problem_category VARCHAR(200),
    failure_mode VARCHAR(300),
    root_cause_category VARCHAR(200),
    symptom_tags TEXT[] NOT NULL DEFAULT '{}',
    embedding_vector BYTEA,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_quality_case_similarity_index_plan UNIQUE (plan_id),

    CONSTRAINT fk_quality_case_similarity_index_plan
        FOREIGN KEY (plan_id)
        REFERENCES quality.quality_action_plans (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_quality_case_similarity_index_product
    ON quality.quality_case_similarity_index (product_code);

CREATE INDEX IF NOT EXISTS ix_quality_case_similarity_index_failure_mode
    ON quality.quality_case_similarity_index (failure_mode);

CREATE INDEX IF NOT EXISTS ix_quality_case_similarity_index_symptom_tags
    ON quality.quality_case_similarity_index USING GIN (symptom_tags);

CREATE INDEX IF NOT EXISTS ix_quality_case_similarity_index_search_trgm
    ON quality.quality_case_similarity_index USING GIN (search_text gin_trgm_ops);

-- Backfill inicial do índice a partir de planos existentes
INSERT INTO quality.quality_case_similarity_index (
    plan_id,
    search_text,
    product_code,
    customer_name,
    problem_category,
    failure_mode,
    root_cause_category,
    symptom_tags
)
SELECT
    p.id,
    trim(
        concat_ws(
            ' ',
            p.title,
            p.reported_problem,
            p.failure_mode,
            p.problem_category,
            p.product_description,
            fw.root_cause
        )
    ),
    p.product_code,
    p.customer_name,
    p.problem_category,
    p.failure_mode,
    COALESCE(p.root_cause_category, fw.root_cause),
    COALESCE(p.symptom_tags, '{}')
  FROM quality.quality_action_plans p
  LEFT JOIN quality.quality_five_whys fw ON fw.plan_id = p.id
 WHERE p.deleted_at IS NULL
ON CONFLICT (plan_id) DO NOTHING;
