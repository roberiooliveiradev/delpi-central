-- Nome legível de quem submeteu o plano (Keycloak name), além do submitted_by (sub).
ALTER TABLE planejamento_orcamentario.capex_plans
    ADD COLUMN IF NOT EXISTS submitted_by_name VARCHAR(200);

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD COLUMN IF NOT EXISTS submitted_by_name VARCHAR(200);

COMMENT ON COLUMN planejamento_orcamentario.capex_plans.submitted_by_name IS
    'Nome completo de quem enviou o plano CAPEX para aprovação.';

COMMENT ON COLUMN planejamento_orcamentario.personnel_plans.submitted_by_name IS
    'Nome completo de quem enviou o plano de Pessoal para aprovação.';

-- Backfill a partir do histórico de submissão (último envio por plano).
UPDATE planejamento_orcamentario.capex_plans p
SET submitted_by_name = h.actor_name
FROM (
    SELECT DISTINCT ON (plan_id)
        plan_id,
        actor_name
    FROM planejamento_orcamentario.capex_plan_history
    WHERE action = 'submitted'
      AND actor_name IS NOT NULL
      AND BTRIM(actor_name) <> ''
    ORDER BY plan_id, created_at DESC
) h
WHERE p.id = h.plan_id
  AND (p.submitted_by_name IS NULL OR BTRIM(p.submitted_by_name) = '');

UPDATE planejamento_orcamentario.personnel_plans p
SET submitted_by_name = h.actor_name
FROM (
    SELECT DISTINCT ON (plan_id)
        plan_id,
        actor_name
    FROM planejamento_orcamentario.personnel_plan_history
    WHERE action = 'submitted'
      AND actor_name IS NOT NULL
      AND BTRIM(actor_name) <> ''
    ORDER BY plan_id, created_at DESC
) h
WHERE p.id = h.plan_id
  AND (p.submitted_by_name IS NULL OR BTRIM(p.submitted_by_name) = '');
