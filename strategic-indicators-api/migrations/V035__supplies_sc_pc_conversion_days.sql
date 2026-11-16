-- GLPI #635 / PROC-0075.
-- Informational indicator: no arbitrary target or weight until business homologation.
-- Date anchor = final SCR approval; first linked PC; unit=calendar days.
BEGIN;

INSERT INTO strategic_indicators.department_indicators (
    indicator_id, department_id, indicator_name, weight_pct, scope_type,
    performance_direction, strategic_description, source_key,
    value_unit, value_suffix, value_decimals,
    is_active, display_order, supports_branch_goals,
    branch_value_aggregation
) VALUES (
    'supplies-sc-pc-conversion-days',
    'supplies',
    'Tempo médio da liberação da SC até o primeiro PC',
    0,
    'per_unit',
    'lower_is_better',
    'Média dos dias corridos entre a última liberação comprovada em SCR010 e o primeiro pedido vinculado em SC7010. Cada SC convertida entra uma vez; consolidação ponderada pela quantidade de SCs. Sem metas validadas.',
    'supplies_sc_pc_conversion',
    'days', 'dias', 2,
    TRUE, 10, TRUE, 'source_consolidated'
)
ON CONFLICT (indicator_id) DO NOTHING;

COMMIT;
