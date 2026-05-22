-- Produção (e demais per_unit): metas por filial 01/02.
-- Duplica metas consolidadas ativas de indicadores per_unit do departamento Produção.

BEGIN;

UPDATE strategic_indicators.department_indicators
SET
    supports_branch_goals = TRUE,
    updated_at = NOW()
WHERE scope_type = 'per_unit'
  AND supports_branch_goals IS DISTINCT FROM TRUE;

COMMENT ON COLUMN strategic_indicators.department_indicators.supports_branch_goals IS
'TRUE quando o indicador aceita metas por filial (consolidated e per_unit).';

-- Metas consolidadas de Produção deixam de ser a referência ativa (visão por filial usa 01/02).
UPDATE strategic_indicators.indicator_goals g
SET
    is_active = FALSE,
    valid_to = COALESCE(g.valid_to, CURRENT_DATE - 1),
    notes = TRIM(BOTH ' |' FROM COALESCE(g.notes, '') || ' | V021 substituída por meta Filial 01/02'),
    updated_at = NOW()
FROM strategic_indicators.department_indicators di
WHERE g.indicator_id = di.indicator_id
  AND di.department_id = 'production'
  AND di.scope_type = 'per_unit'
  AND di.is_active = TRUE
  AND g.is_active = TRUE
  AND COALESCE(g.goal_scope_branch, '') = '';

-- Duplica cada meta consolidada inativa recente para Filial 01 e 02 (mesmos valores).
INSERT INTO strategic_indicators.indicator_goals (
    indicator_id,
    goal_year,
    goal_scope_branch,
    goal_label,
    goal_value,
    goal_periodicity,
    goal_mode,
    version,
    is_active,
    valid_from,
    valid_to,
    notes,
    copied_from_goal_id,
    copied_from_year,
    created_by_user_id,
    created_by_email,
    updated_by_user_id,
    updated_by_email
)
SELECT
    src.indicator_id,
    src.goal_year,
    branch.goal_scope_branch,
    src.goal_label,
    src.goal_value,
    src.goal_periodicity,
    src.goal_mode,
    src.version,
    TRUE,
    src.valid_from,
    src.valid_to,
    TRIM(BOTH ' |' FROM COALESCE(src.notes, '') || ' | V021 Filial ' || branch.goal_scope_branch),
    src.id,
    src.goal_year,
    src.created_by_user_id,
    src.created_by_email,
    src.updated_by_user_id,
    src.updated_by_email
FROM strategic_indicators.indicator_goals src
INNER JOIN strategic_indicators.department_indicators di
    ON di.indicator_id = src.indicator_id
CROSS JOIN (
    VALUES ('01'), ('02')
) AS branch(goal_scope_branch)
WHERE di.department_id = 'production'
  AND di.scope_type = 'per_unit'
  AND di.is_active = TRUE
  AND COALESCE(src.goal_scope_branch, '') = ''
  AND src.is_active = FALSE
  AND COALESCE(src.notes, '') LIKE '%V021 substituída por meta Filial 01/02%'
  AND NOT EXISTS (
      SELECT 1
      FROM strategic_indicators.indicator_goals existing
      WHERE existing.indicator_id = src.indicator_id
        AND existing.goal_year = src.goal_year
        AND existing.goal_scope_branch = branch.goal_scope_branch
        AND existing.is_active = TRUE
  );

-- Curvas mensais: replica targets da meta consolidada de origem.
INSERT INTO strategic_indicators.indicator_goal_monthly_targets (
    indicator_goal_id,
    month_number,
    target_value
)
SELECT
    branch_goal.id,
    monthly.month_number,
    monthly.target_value
FROM strategic_indicators.indicator_goals branch_goal
INNER JOIN strategic_indicators.indicator_goals src
    ON src.id = branch_goal.copied_from_goal_id
INNER JOIN strategic_indicators.indicator_goal_monthly_targets monthly
    ON monthly.indicator_goal_id = src.id
INNER JOIN strategic_indicators.department_indicators di
    ON di.indicator_id = branch_goal.indicator_id
WHERE di.department_id = 'production'
  AND di.scope_type = 'per_unit'
  AND branch_goal.is_active = TRUE
  AND branch_goal.goal_scope_branch IN ('01', '02')
  AND branch_goal.goal_mode = 'monthly_curve'
  AND COALESCE(branch_goal.notes, '') LIKE '%V021 Filial%'
ON CONFLICT (indicator_goal_id, month_number)
DO UPDATE SET
    target_value = EXCLUDED.target_value,
    updated_at = NOW();

COMMIT;
