-- Qualidade: metas 2026 por unidade (Filial 01 / Filial 02).
-- Desativa metas consolidadas legado e cadastra escopos 01/02 conforme planilha operacional.

BEGIN;

UPDATE strategic_indicators.indicator_goals g
SET
    is_active = FALSE,
    valid_to = COALESCE(g.valid_to, CURRENT_DATE - 1),
    notes = TRIM(BOTH ' |' FROM COALESCE(g.notes, '') || ' | V018 substituída por meta por unidade'),
    updated_at = NOW()
FROM strategic_indicators.department_indicators di
WHERE g.indicator_id = di.indicator_id
  AND di.department_id = 'quality'
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
        ('quality-ppm-internal', 2026, '01', '1.400 PPM', 1400.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 01'),
        ('quality-ppm-internal', 2026, '02', '2.300 PPM', 2300.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 02'),
        ('quality-ppm-external', 2026, '01', '1.100 PPM', 1100.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 01'),
        ('quality-ppm-external', 2026, '02', '290 PPM', 290.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 02'),
        ('quality-kaizen-ideas', 2026, '01', '8 ideias/mês', 8.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 01'),
        ('quality-kaizen-ideas', 2026, '02', '8 ideias/mês', 8.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 02'),
        ('quality-audit-5s', 2026, '01', '80%', 80.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 01'),
        ('quality-audit-5s', 2026, '02', '80%', 80.0000, 'monthly', 'standard', 1, TRUE, 'V018 Filial 02'),
        (
            'quality-kaizen-financial',
            2026,
            '01',
            'Curva R$ 4.500 (jan-jun) / R$ 9.000 (jul-dez)',
            9000.0000,
            'monthly',
            'monthly_curve',
            1,
            TRUE,
            'V018 Filial 01 — curva mensal'
        ),
        (
            'quality-kaizen-financial',
            2026,
            '02',
            'R$ 4.500/mês',
            4500.0000,
            'monthly',
            'standard',
            1,
            TRUE,
            'V018 Filial 02 — meta padrão'
        )
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

INSERT INTO strategic_indicators.indicator_goal_monthly_targets (
    indicator_goal_id,
    month_number,
    target_value
)
SELECT
    g.id,
    m.month_number,
    CASE
        WHEN m.month_number <= 6 THEN 4500.0000
        ELSE 9000.0000
    END
FROM strategic_indicators.indicator_goals g
CROSS JOIN generate_series(1, 12) AS m(month_number)
WHERE g.indicator_id = 'quality-kaizen-financial'
  AND g.goal_year = 2026
  AND g.goal_scope_branch = '01'
  AND g.is_active = TRUE
  AND g.goal_mode = 'monthly_curve'
ON CONFLICT (indicator_goal_id, month_number)
DO UPDATE SET
    target_value = EXCLUDED.target_value,
    updated_at = NOW();

UPDATE strategic_indicators.department_indicators
SET
    supports_branch_goals = TRUE,
    updated_at = NOW()
WHERE department_id = 'quality'
  AND scope_type = 'consolidated'
  AND is_active = TRUE;

COMMIT;
