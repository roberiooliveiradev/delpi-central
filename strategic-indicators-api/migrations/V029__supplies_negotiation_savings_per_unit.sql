-- Economia em negociações de compras: indicador por unidade (filial) com metas 01/02.

BEGIN;

UPDATE strategic_indicators.department_indicators
SET
    scope_type = 'per_unit',
    supports_branch_goals = TRUE,
    updated_at = NOW()
WHERE indicator_id = 'supplies-negotiation-savings';

UPDATE strategic_indicators.indicator_goals g
SET
    is_active = FALSE,
    valid_to = COALESCE(g.valid_to, CURRENT_DATE - 1),
    notes = TRIM(BOTH ' |' FROM COALESCE(g.notes, '') || ' | V029 substituída por meta Filial 01/02'),
    updated_at = NOW()
WHERE g.indicator_id = 'supplies-negotiation-savings'
  AND g.goal_year = 2026
  AND g.is_active = TRUE
  AND COALESCE(g.goal_scope_branch, '') = '';

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
    TRIM(BOTH ' |' FROM COALESCE(src.notes, '') || ' | V029 Filial ' || branch.goal_scope_branch),
    src.id,
    src.goal_year,
    src.created_by_user_id,
    src.created_by_email,
    src.updated_by_user_id,
    src.updated_by_email
FROM strategic_indicators.indicator_goals src
CROSS JOIN (
    VALUES ('01'), ('02')
) AS branch(goal_scope_branch)
WHERE src.indicator_id = 'supplies-negotiation-savings'
  AND src.goal_year = 2026
  AND COALESCE(src.goal_scope_branch, '') = ''
  AND src.is_active = FALSE
  AND COALESCE(src.notes, '') LIKE '%V029 substituída por meta Filial 01/02%'
  AND NOT EXISTS (
      SELECT 1
      FROM strategic_indicators.indicator_goals existing
      WHERE existing.indicator_id = src.indicator_id
        AND existing.goal_year = src.goal_year
        AND existing.goal_scope_branch = branch.goal_scope_branch
        AND existing.is_active = TRUE
  );

COMMIT;
