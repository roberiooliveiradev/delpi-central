-- PAC Qualidade — classificação interna/externa (sem vínculo NC TOTVS)

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS nonconformity_scope VARCHAR(20) NOT NULL DEFAULT 'external';

UPDATE quality.quality_action_plans
   SET nonconformity_scope = 'internal'
 WHERE deleted_at IS NULL
   AND (customer_name IS NULL OR TRIM(customer_name) = '')
   AND department IS NOT NULL
   AND TRIM(department) <> '';

ALTER TABLE quality.quality_action_plans
    DROP CONSTRAINT IF EXISTS ck_quality_action_plans_nonconformity_scope;

ALTER TABLE quality.quality_action_plans
    ADD CONSTRAINT ck_quality_action_plans_nonconformity_scope CHECK (
        nonconformity_scope IN ('internal', 'external')
    );

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_nonconformity_scope
    ON quality.quality_action_plans (nonconformity_scope)
    WHERE deleted_at IS NULL;

COMMENT ON COLUMN quality.quality_action_plans.nonconformity_scope IS
    'Escopo do plano: internal (NC/processo interno) ou external (cliente/fornecedor). Sem FK NC TOTVS.';
