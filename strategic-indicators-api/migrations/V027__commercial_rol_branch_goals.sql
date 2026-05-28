-- Comercial (V026): copia metas dos indicadores legados matrix/branch para commercial-rol (01/02)
-- e duplica metas consolidadas dos demais per_unit comercial para filiais 01 e 02.

BEGIN;

-- ROL único: matriz legada → filial 01, filial legada → filial 02.
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
    'commercial-rol',
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
    TRIM(BOTH ' |' FROM COALESCE(src.notes, '') || ' | V027 de ' || src.indicator_id),
    src.id,
    src.goal_year,
    src.created_by_user_id,
    src.created_by_email,
    src.updated_by_user_id,
    src.updated_by_email
FROM strategic_indicators.indicator_goals src
CROSS JOIN (
    VALUES ('01', 'commercial-rol-matrix'), ('02', 'commercial-rol-branch')
) AS branch(goal_scope_branch, legacy_indicator_id)
WHERE src.indicator_id = branch.legacy_indicator_id
  AND src.is_active = TRUE
  AND COALESCE(src.goal_scope_branch, '') = ''
  AND NOT EXISTS (
      SELECT 1
      FROM strategic_indicators.indicator_goals existing
      WHERE existing.indicator_id = 'commercial-rol'
        AND existing.goal_year = src.goal_year
        AND existing.goal_scope_branch = branch.goal_scope_branch
        AND existing.is_active = TRUE
  );

INSERT INTO strategic_indicators.indicator_goal_monthly_targets (
    indicator_goal_id,
    month_number,
    target_value
)
SELECT
    dest.id,
    monthly.month_number,
    monthly.target_value
FROM strategic_indicators.indicator_goals dest
INNER JOIN strategic_indicators.indicator_goals src
    ON src.id = dest.copied_from_goal_id
INNER JOIN strategic_indicators.indicator_goal_monthly_targets monthly
    ON monthly.indicator_goal_id = src.id
WHERE dest.indicator_id = 'commercial-rol'
  AND dest.is_active = TRUE
  AND dest.goal_scope_branch IN ('01', '02')
  AND COALESCE(dest.notes, '') LIKE '%V027 de%'
ON CONFLICT (indicator_goal_id, month_number)
DO UPDATE SET
    target_value = EXCLUDED.target_value,
    updated_at = NOW();

-- Demais per_unit do Comercial: meta consolidada ativa → 01 e 02 (mesmo valor).
UPDATE strategic_indicators.indicator_goals g
SET
    is_active = FALSE,
    valid_to = COALESCE(g.valid_to, CURRENT_DATE - 1),
    notes = TRIM(BOTH ' |' FROM COALESCE(g.notes, '') || ' | V027 substituída por meta Filial 01/02'),
    updated_at = NOW()
FROM strategic_indicators.department_indicators di
WHERE g.indicator_id = di.indicator_id
  AND di.department_id = 'commercial'
  AND di.scope_type = 'per_unit'
  AND di.is_active = TRUE
  AND di.indicator_id <> 'commercial-rol'
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
    TRIM(BOTH ' |' FROM COALESCE(src.notes, '') || ' | V027 Filial ' || branch.goal_scope_branch),
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
WHERE di.department_id = 'commercial'
  AND di.scope_type = 'per_unit'
  AND di.is_active = TRUE
  AND di.indicator_id <> 'commercial-rol'
  AND COALESCE(src.goal_scope_branch, '') = ''
  AND src.is_active = FALSE
  AND COALESCE(src.notes, '') LIKE '%V027 substituída por meta Filial 01/02%'
  AND NOT EXISTS (
      SELECT 1
      FROM strategic_indicators.indicator_goals existing
      WHERE existing.indicator_id = src.indicator_id
        AND existing.goal_year = src.goal_year
        AND existing.goal_scope_branch = branch.goal_scope_branch
        AND existing.is_active = TRUE
  );

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
WHERE di.department_id = 'commercial'
  AND di.scope_type = 'per_unit'
  AND di.indicator_id <> 'commercial-rol'
  AND branch_goal.is_active = TRUE
  AND branch_goal.goal_scope_branch IN ('01', '02')
  AND COALESCE(branch_goal.notes, '') LIKE '%V027 Filial%'
ON CONFLICT (indicator_goal_id, month_number)
DO UPDATE SET
    target_value = EXCLUDED.target_value,
    updated_at = NOW();

COMMIT;
