-- PAC Qualidade — filial onde ocorreu o problema (alinhado a Kaizen / Strategic Indicators)

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS branch_code VARCHAR(10);

ALTER TABLE quality.quality_case_similarity_index
    ADD COLUMN IF NOT EXISTS branch_code VARCHAR(10);

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS ck_quality_action_plans_branch_code;

ALTER TABLE quality.quality_action_plans
    ADD CONSTRAINT ck_quality_action_plans_branch_code
    CHECK (branch_code IS NULL OR branch_code IN ('01', '02'));

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_branch_code
    ON quality.quality_action_plans (branch_code)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_quality_case_similarity_index_branch_code
    ON quality.quality_case_similarity_index (branch_code);

-- Backfill do índice de similaridade a partir do plano
UPDATE quality.quality_case_similarity_index idx
   SET branch_code = p.branch_code,
       updated_at = NOW()
  FROM quality.quality_action_plans p
 WHERE p.id = idx.plan_id
   AND idx.branch_code IS NULL
   AND p.branch_code IS NOT NULL;
