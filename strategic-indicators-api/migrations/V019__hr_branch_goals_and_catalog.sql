-- RH: catálogo 2026 (6 indicadores, pesos da planilha) e metas por filial 01/02.

BEGIN;

UPDATE strategic_indicators.department_indicators
SET
    weight_pct = 25.00,
    display_order = 1,
    updated_at = NOW()
WHERE indicator_id = 'hr-absenteeism';

UPDATE strategic_indicators.department_indicators
SET
    weight_pct = 25.00,
    display_order = 2,
    updated_at = NOW()
WHERE indicator_id = 'hr-turnover';

UPDATE strategic_indicators.department_indicators
SET
    weight_pct = 20.00,
    display_order = 3,
    updated_at = NOW()
WHERE indicator_id = 'hr-satisfaction';

UPDATE strategic_indicators.department_indicators
SET
    indicator_name = 'Número de PDI''s Ativos',
    weight_pct = 10.00,
    value_unit = 'count',
    value_suffix = NULL,
    display_order = 4,
    updated_at = NOW()
WHERE indicator_id = 'hr-pdi';

UPDATE strategic_indicators.department_indicators
SET
    weight_pct = 10.00,
    display_order = 6,
    updated_at = NOW()
WHERE indicator_id = 'hr-training-hours';

INSERT INTO strategic_indicators.department_indicators (
    indicator_id,
    department_id,
    indicator_name,
    weight_pct,
    scope_type,
    performance_direction,
    strategic_description,
    source_key,
    value_unit,
    value_prefix,
    value_suffix,
    value_decimals,
    is_active,
    display_order
)
SELECT
    'hr-performance-reviews',
    'hr',
    '% de Avaliações de Desempenho Concluídas',
    10.00,
    'consolidated',
    'higher_is_better',
    'Percentual de avaliações de desempenho finalizadas no período.',
    'hr_performance_reviews_completion',
    'percent',
    NULL,
    '%',
    2,
    TRUE,
    5
WHERE NOT EXISTS (
    SELECT 1
    FROM strategic_indicators.department_indicators
    WHERE indicator_id = 'hr-performance-reviews'
);

UPDATE strategic_indicators.indicator_goals g
SET
    is_active = FALSE,
    valid_to = COALESCE(g.valid_to, CURRENT_DATE - 1),
    notes = TRIM(BOTH ' |' FROM COALESCE(g.notes, '') || ' | V019 substituída por meta por unidade'),
    updated_at = NOW()
FROM strategic_indicators.department_indicators di
WHERE g.indicator_id = di.indicator_id
  AND di.department_id = 'hr'
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
    notes
)
SELECT
    v.indicator_id,
    v.goal_year,
    v.goal_scope_branch,
    v.goal_label,
    v.goal_value,
    v.goal_periodicity,
    v.goal_mode,
    v.version,
    v.is_active,
    v.notes
FROM (
    VALUES
        ('hr-absenteeism', 2026, '01', '3%', 3.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 01'),
        ('hr-absenteeism', 2026, '02', '2%', 2.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 02'),
        ('hr-turnover', 2026, '01', '5%', 5.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 01'),
        ('hr-turnover', 2026, '02', '4,5%', 4.5000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 02'),
        ('hr-satisfaction', 2026, '01', '80%', 80.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 01'),
        ('hr-satisfaction', 2026, '02', '80%', 80.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 02'),
        ('hr-pdi', 2026, '01', '15 PDIs', 15.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 01'),
        ('hr-pdi', 2026, '02', '8 PDIs', 8.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 02'),
        ('hr-performance-reviews', 2026, '01', '90%', 90.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 01'),
        ('hr-performance-reviews', 2026, '02', '90%', 90.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 02'),
        ('hr-training-hours', 2026, '01', '2h/mês', 2.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 01'),
        ('hr-training-hours', 2026, '02', '2h/mês', 2.0000, 'monthly', 'standard', 1, TRUE, 'V019 Filial 02')
) AS v(
    indicator_id,
    goal_year,
    goal_scope_branch,
    goal_label,
    goal_value,
    goal_periodicity,
    goal_mode,
    version,
    is_active,
    notes
)
WHERE NOT EXISTS (
    SELECT 1
    FROM strategic_indicators.indicator_goals g
    WHERE g.indicator_id = v.indicator_id
      AND g.goal_year = v.goal_year
      AND COALESCE(g.goal_scope_branch, '') = v.goal_scope_branch
      AND g.is_active = TRUE
);

UPDATE strategic_indicators.department_indicators
SET
    supports_branch_goals = TRUE,
    updated_at = NOW()
WHERE department_id = 'hr'
  AND scope_type = 'consolidated'
  AND is_active = TRUE;

COMMIT;
