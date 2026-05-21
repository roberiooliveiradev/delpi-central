-- Reestrutura indicadores do departamento Comercial (catálogo + metas 2026).
-- Novos: OTD de pedidos de venda (rota pendente), % ROL Novos Negócios (curva mensal %).
-- Inativos: Número de Novos Clientes, % ROL de Novos Clientes (legado).
-- Pesos: 25 + 25 + 15 + 15 + 15 = 95 (ajuste fino no admin se desejar 100).

UPDATE strategic_indicators.department_indicators
SET is_active = FALSE, updated_at = NOW()
WHERE indicator_id IN ('commercial-new-clients', 'commercial-new-rol');

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
VALUES
(
    'commercial-rol-matrix',
    'commercial',
    'ROL Matriz',
    25.00,
    'per_unit',
    'higher_is_better',
    'Atingimento da meta de receita da matriz (filial 01).',
    'commercial_head_office_rol_target',
    'currency',
    'R$',
    NULL,
    2,
    TRUE,
    1
),
(
    'commercial-rol-branch',
    'commercial',
    'ROL Filial',
    25.00,
    'per_unit',
    'higher_is_better',
    'Atingimento da meta de receita das filiais (demais unidades).',
    'commercial_branch_rol_target',
    'currency',
    'R$',
    NULL,
    2,
    TRUE,
    2
),
(
    'commercial-closing-rate',
    'commercial',
    'Taxa de Fechamento de Negócios',
    15.00,
    'consolidated',
    'higher_is_better',
    'Conversão de propostas em vendas fechadas.',
    'commercial_sales_conversion_rate',
    'percent',
    NULL,
    '%',
    2,
    TRUE,
    3
),
(
    'commercial-sales-order-otd',
    'commercial',
    'OTD de Pedidos de Venda',
    15.00,
    'consolidated',
    'higher_is_better',
    'Pedidos de venda entregues no prazo prometido ao cliente.',
    'commercial_sales_order_otd',
    'percent',
    NULL,
    '%',
    2,
    TRUE,
    4
),
(
    'commercial-new-business-rol',
    'commercial',
    '% ROL de Novos Negócios',
    15.00,
    'consolidated',
    'higher_is_better',
    'Participação da receita de novos negócios no ROL total.',
    'commercial_new_business_rol_pct',
    'percent',
    NULL,
    '%',
    2,
    TRUE,
    5
)
ON CONFLICT (indicator_id)
DO UPDATE SET
    department_id = EXCLUDED.department_id,
    indicator_name = EXCLUDED.indicator_name,
    weight_pct = EXCLUDED.weight_pct,
    scope_type = EXCLUDED.scope_type,
    performance_direction = EXCLUDED.performance_direction,
    strategic_description = EXCLUDED.strategic_description,
    source_key = EXCLUDED.source_key,
    value_unit = EXCLUDED.value_unit,
    value_prefix = EXCLUDED.value_prefix,
    value_suffix = EXCLUDED.value_suffix,
    value_decimals = EXCLUDED.value_decimals,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

UPDATE strategic_indicators.indicator_goals
SET
    goal_value = 10.0000,
    goal_label = '10%',
    notes = COALESCE(notes, '') || ' | V015 meta 10%',
    updated_at = NOW()
WHERE indicator_id = 'commercial-closing-rate'
  AND goal_year = 2026
  AND is_active = TRUE;

UPDATE strategic_indicators.indicator_goals
SET
    is_active = FALSE,
    valid_to = COALESCE(valid_to, CURRENT_DATE - 1),
    updated_at = NOW()
WHERE indicator_id IN ('commercial-new-clients', 'commercial-new-rol')
  AND is_active = TRUE;

INSERT INTO strategic_indicators.indicator_goals (
    indicator_id,
    goal_year,
    goal_label,
    goal_value,
    goal_periodicity,
    goal_mode,
    version,
    is_active,
    notes
)
SELECT v.indicator_id, v.goal_year, v.goal_label, v.goal_value, v.goal_periodicity, v.goal_mode, v.version, v.is_active, v.notes
FROM (
    VALUES
        ('commercial-sales-order-otd'::VARCHAR, 2026, '95%'::VARCHAR, 95.0000::NUMERIC, 'monthly'::VARCHAR, 'standard'::VARCHAR, 1, TRUE, 'V015 — rota TOTVS pendente'),
        ('commercial-new-business-rol', 2026, 'Curva mensal % Novos Negócios 2026', 12.0000, 'monthly', 'monthly_curve', 1, TRUE, 'V015 — curva mensal % (placeholder 12% / mês)')
) AS v(indicator_id, goal_year, goal_label, goal_value, goal_periodicity, goal_mode, version, is_active, notes)
WHERE NOT EXISTS (
    SELECT 1
    FROM strategic_indicators.indicator_goals g
    WHERE g.indicator_id = v.indicator_id
      AND g.goal_year = v.goal_year
      AND g.is_active = TRUE
);

INSERT INTO strategic_indicators.indicator_goal_monthly_targets (
    indicator_goal_id,
    month_number,
    target_value
)
SELECT g.id, m.month_number, 12.0000
FROM strategic_indicators.indicator_goals g
CROSS JOIN generate_series(1, 12) AS m(month_number)
WHERE g.indicator_id = 'commercial-new-business-rol'
  AND g.goal_year = 2026
  AND g.is_active = TRUE
  AND g.goal_mode = 'monthly_curve'
ON CONFLICT (indicator_goal_id, month_number)
DO UPDATE SET
    target_value = EXCLUDED.target_value,
    updated_at = NOW();
