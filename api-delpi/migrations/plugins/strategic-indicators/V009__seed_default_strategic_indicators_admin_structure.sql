BEGIN;

-- =========================================================
-- 1) PARÂMETROS GLOBAIS
-- =========================================================

INSERT INTO strategic_indicators.module_settings (
    setting_key,
    setting_group,
    payload_json,
    is_active
)
VALUES
(
    'parameters.global',
    'parameters',
    '{
      "items": [
        { "key": "igd_scale", "label": "Escala oficial do IGD", "value": "0 a 10" },
        { "key": "executive_refresh", "label": "Frequência executiva", "value": "Mensal" },
        { "key": "source_of_truth", "label": "Fonte oficial", "value": "departments + department_indicators + indicator_goals + indicator_goal_monthly_targets + module_settings" }
      ]
    }'::jsonb,
    TRUE
)
ON CONFLICT (setting_key)
DO UPDATE SET
    payload_json = EXCLUDED.payload_json,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- =========================================================
-- 2) GOVERNANÇA GLOBAL
-- =========================================================

INSERT INTO strategic_indicators.module_settings (
    setting_key,
    setting_group,
    payload_json,
    is_active
)
VALUES
(
    'governance.notes',
    'governance',
    '{
      "items": [
        {
          "key": "catalog_owner",
          "label": "Responsável pelo catálogo",
          "value": "Administração do módulo",
          "observation": "Mudanças estruturais devem ser versionadas e auditadas"
        },
        {
          "key": "calculation_rule",
          "label": "Regra de cálculo",
          "value": "Backend",
          "observation": "Frontend não deve calcular score oficial"
        },
        {
          "key": "monthly_curve_rule",
          "label": "Curva mensal",
          "value": "Suportada",
          "observation": "Indicadores com sazonalidade podem usar tabela filha de metas mensais"
        }
      ]
    }'::jsonb,
    TRUE
)
ON CONFLICT (setting_key)
DO UPDATE SET
    payload_json = EXCLUDED.payload_json,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- =========================================================
-- 3) DEPARTAMENTOS ADMINISTRATIVOS
-- =========================================================

INSERT INTO strategic_indicators.departments (
    department_id,
    department_name,
    short_name,
    strategic_summary,
    headline_goal,
    supporting_focus,
    weight_pct,
    aggregation_mode,
    is_active,
    display_order
)
VALUES
(
    'financial',
    'Financeiro',
    'FIN',
    'Mede rentabilidade, estrutura de custos e eficiência financeira.',
    'Rentabilidade e disciplina financeira',
    'Eficiência operacional e caixa saudável',
    15.00,
    'consolidated',
    TRUE,
    1
),
(
    'hr',
    'RH',
    'RH',
    'Mede engajamento, retenção, desenvolvimento e clima organizacional.',
    'Pessoas engajadas e desenvolvidas',
    'Clima, capacitação e retenção',
    15.00,
    'consolidated',
    TRUE,
    2
),
(
    'commercial',
    'Comercial',
    'COM',
    'Mede atingimento de receita, conversão e expansão da base de clientes.',
    'Crescimento sustentável de receita',
    'Conversão, novos clientes e expansão',
    17.00,
    'average_of_units',
    TRUE,
    3
),
(
    'production',
    'Produção',
    'PRO',
    'Mede eficiência produtiva, custos, ativos e prazo de entrega.',
    'Eficiência produtiva e entrega',
    'Custos, OEE e prazo',
    17.00,
    'average_of_units',
    TRUE,
    4
),
(
    'quality',
    'Qualidade',
    'QUA',
    'Mede confiabilidade do produto e avanço da melhoria contínua.',
    'Confiabilidade e melhoria contínua',
    'PPM, 5S e Kaizen',
    14.00,
    'consolidated',
    TRUE,
    5
),
(
    'supplies',
    'Suprimentos',
    'SUP',
    'Mede eficiência de compras, estoque e negociação com fornecedores.',
    'Compras e estoque sob controle',
    'CPV, OTD e capital empatado',
    12.00,
    'consolidated',
    TRUE,
    6
),
(
    'engineering',
    'Engenharia',
    'ENG',
    'Mede entrega no prazo e geração de valor via inovação e digitalização.',
    'Entrega no prazo com geração de valor',
    'Projetos e inovação aplicada',
    10.00,
    'average_of_units',
    TRUE,
    7
)
ON CONFLICT (department_id)
DO UPDATE SET
    department_name = EXCLUDED.department_name,
    short_name = EXCLUDED.short_name,
    strategic_summary = EXCLUDED.strategic_summary,
    headline_goal = EXCLUDED.headline_goal,
    supporting_focus = EXCLUDED.supporting_focus,
    weight_pct = EXCLUDED.weight_pct,
    aggregation_mode = EXCLUDED.aggregation_mode,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

-- =========================================================
-- 4) INDICADORES ESTRUTURAIS POR DEPARTAMENTO
-- =========================================================

INSERT INTO strategic_indicators.department_indicators (
    indicator_id,
    department_id,
    indicator_name,
    weight_pct,
    scope_type,
    performance_direction,
    strategic_description,
    source_key,
    is_active,
    display_order
)
VALUES
-- FINANCIAL
('financial-ebitda', 'financial', 'EBITDA / Receita Operacional', 40.00, 'consolidated', 'higher_is_better', 'Mede a capacidade de geração de resultado operacional.', 'financial_ebitda', TRUE, 1),
('financial-fixed-cost', 'financial', '% Custos Fixos / Receita Operacional', 30.00, 'consolidated', 'lower_is_better', 'Indica eficiência e estrutura enxuta.', 'financial_fixed_cost', TRUE, 2),
('financial-pmr', 'financial', 'Prazo Médio de Recebimento (PMR)', 30.00, 'consolidated', 'lower_is_better', 'Indica eficiência de recebimentos e fluxo de caixa.', 'financial_pmr', TRUE, 3),

-- HR
('hr-absenteeism', 'hr', 'Absenteísmo', 20.00, 'consolidated', 'lower_is_better', 'Mede engajamento e bem-estar.', 'hr_absenteeism', TRUE, 1),
('hr-turnover', 'hr', 'Turnover (Rotatividade)', 20.00, 'consolidated', 'lower_is_better', 'Mede retenção e estabilidade.', 'hr_turnover', TRUE, 2),
('hr-satisfaction', 'hr', 'Satisfação Interna (Clima/Engajamento)', 20.00, 'consolidated', 'higher_is_better', 'Reputação interna da cultura.', 'hr_satisfaction', TRUE, 3),
('hr-pdi', 'hr', '% de PDIs Ativos', 20.00, 'consolidated', 'higher_is_better', 'Estruturação de desenvolvimento individual.', 'hr_pdi', TRUE, 4),
('hr-training-hours', 'hr', 'Horas de Treinamento / Colaborador / mês', 20.00, 'consolidated', 'higher_is_better', 'Investimento em formação e capacitação.', 'hr_training_hours', TRUE, 5),

-- COMMERCIAL
('commercial-rol-matrix', 'commercial', 'ROL Matriz / Meta', 25.00, 'per_unit', 'higher_is_better', 'Atingimento da receita da unidade matriz.', 'commercial_head_office_rol_target', TRUE, 1),
('commercial-rol-branch', 'commercial', 'ROL Filial / Meta', 25.00, 'per_unit', 'higher_is_better', 'Atingimento da receita da unidade filial.', 'commercial_branch_rol_target', TRUE, 2),
('commercial-closing-rate', 'commercial', 'Taxa de Fechamento de Negócios', 20.00, 'consolidated', 'higher_is_better', 'Conversão de propostas em vendas.', 'commercial_sales_conversion_rate', TRUE, 3),
('commercial-new-clients', 'commercial', 'Número de Novos Clientes (média mensal)', 15.00, 'consolidated', 'higher_is_better', 'Capacidade de abertura de mercado.', 'commercial_new_clients_average', TRUE, 4),
('commercial-new-rol', 'commercial', '% ROL de Novos Clientes', 15.00, 'consolidated', 'higher_is_better', 'Participação dos novos no total da receita.', 'commercial_new_clients_rol_pct', TRUE, 5),

-- PRODUCTION
('production-direct-labor', 'production', 'Custo Mão de Obra Direta / ROL', 25.00, 'per_unit', 'lower_is_better', 'Eficiência da mão de obra direta.', 'production_direct_labor', TRUE, 1),
('production-costs', 'production', 'Custos de Produção / ROL', 20.00, 'per_unit', 'lower_is_better', 'Controle de desperdícios e produtividade.', 'production_cost', TRUE, 2),
('production-depreciation', 'production', 'Depreciação / ROL', 10.00, 'per_unit', 'lower_is_better', 'Uso racional da capacidade instalada.', 'production_depreciation', TRUE, 3),
('production-oee', 'production', 'OEE (Eficiência Global dos Equip.)', 20.00, 'per_unit', 'higher_is_better', 'Utilização real dos ativos produtivos.', 'production_oee', TRUE, 4),
('production-otd', 'production', 'OTD (Entrega no Prazo)', 25.00, 'per_unit', 'higher_is_better', 'Cumprimento do prazo prometido ao cliente.', 'production_otd', TRUE, 5),

-- QUALITY
('quality-ppm-internal', 'quality', 'PPM Interno', 20.00, 'consolidated', 'lower_is_better', 'Indicador de falhas detectadas internamente.', 'quality_ppm_internal', TRUE, 1),
('quality-ppm-external', 'quality', 'PPM Externo', 30.00, 'consolidated', 'lower_is_better', 'Indicador de falhas detectadas pelo cliente.', 'quality_ppm_external', TRUE, 2),
('quality-kaizen-ideas', 'quality', 'Ideias Aprovadas para Kaizen/mês', 15.00, 'consolidated', 'higher_is_better', 'Cultura de melhoria e participação.', 'quality_kaizen_ideas', TRUE, 3),
('quality-audit-5s', 'quality', 'Nota Auditoria 5S', 15.00, 'consolidated', 'higher_is_better', 'Padronização, organização e disciplina.', 'quality_audit_5s', TRUE, 4),
('quality-kaizen-financial', 'quality', 'Ganhos Financeiros Kaizen/mês', 20.00, 'consolidated', 'higher_is_better', 'Impacto financeiro direto das melhorias Kaizen.', 'quality_kaizen_financial', TRUE, 5),

-- SUPPLIES
('supplies-cpv', 'supplies', 'CPV Consolidado (matriz e filial)', 30.00, 'consolidated', 'lower_is_better', 'Eficiência nas compras totais.', 'supplies_cpv', TRUE, 1),
('supplies-otd', 'supplies', 'OTD Consolidado de Compras', 20.00, 'consolidated', 'higher_is_better', 'Entregas dentro do prazo pelos fornecedores.', 'supplies_otd', TRUE, 2),
('supplies-stock-turnover', 'supplies', 'Giro de Estoque Consolidado', 20.00, 'consolidated', 'higher_is_better', 'Rotatividade do estoque total.', 'supplies_stock_turnover', TRUE, 3),
('supplies-stock-value', 'supplies', 'Valor Total do Estoque Consolidado', 15.00, 'consolidated', 'lower_is_better', 'Estoque como capital parado.', 'supplies_stock_value', TRUE, 4),
('supplies-negotiation-savings', 'supplies', 'Economia em Negociações de Compras', 15.00, 'consolidated', 'higher_is_better', 'Eficiência em negociações e renegociações com fornecedores.', 'supplies_negotiation_savings', TRUE, 5),

-- ENGINEERING
('engineering-projects-on-time', 'engineering', '% de Projetos Concluídos no Prazo', 60.00, 'per_unit', 'higher_is_better', 'Compromisso com entregas e gestão eficiente de escopo.', 'lmp', TRUE, 1),
('engineering-transforma-plus', 'engineering', 'Ganhos Financeiros do TRANSFORMA+ DELPI', 40.00, 'per_unit', 'higher_is_better', 'Valor gerado por inovações e digitalização via TRANSFORMA+.', 'transforma_mais', TRUE, 2)

ON CONFLICT (indicator_id)
DO UPDATE SET
    department_id = EXCLUDED.department_id,
    indicator_name = EXCLUDED.indicator_name,
    weight_pct = EXCLUDED.weight_pct,
    scope_type = EXCLUDED.scope_type,
    performance_direction = EXCLUDED.performance_direction,
    strategic_description = EXCLUDED.strategic_description,
    source_key = EXCLUDED.source_key,
    is_active = EXCLUDED.is_active,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

-- =========================================================
-- 5) METAS ANALÍTICAS INICIAIS 2026
-- =========================================================

INSERT INTO strategic_indicators.indicator_goals (
    indicator_id,
    goal_year,
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
    copied_from_year
)
VALUES
('financial-ebitda', 2026, '13,0%', 13.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('financial-fixed-cost', 2026, '14,0%', 14.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('financial-pmr', 2026, '39 dias', 39.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),

('hr-absenteeism', 2026, '2,0%', 2.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('hr-turnover', 2026, '1,5% ao mês', 1.5000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('hr-satisfaction', 2026, '85% de satisfação', 85.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('hr-pdi', 2026, '100%', 100.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('hr-training-hours', 2026, '2 horas/mês', 2.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),

('commercial-rol-matrix', 2026, 'Curva mensal ROL Matriz 2026', 11400000.0000, 'monthly', 'monthly_curve', 1, TRUE, NULL, NULL, 'Seed inicial 2026 com curva mensal', NULL, NULL),
('commercial-rol-branch', 2026, 'Curva mensal ROL Filial 2026', 40900000.0000, 'monthly', 'monthly_curve', 1, TRUE, NULL, NULL, 'Seed inicial 2026 com curva mensal', NULL, NULL),
('commercial-closing-rate', 2026, '30%', 30.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('commercial-new-clients', 2026, '10 novos/mês', 10.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('commercial-new-rol', 2026, '12%', 12.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),

('production-direct-labor', 2026, '10,0%', 10.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('production-costs', 2026, '32,0%', 32.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('production-depreciation', 2026, '1,5%', 1.5000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('production-oee', 2026, '70%', 70.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('production-otd', 2026, '92%', 92.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),

('quality-ppm-internal', 2026, '1.400 PPM', 1400.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('quality-ppm-external', 2026, '1.100 PPM', 1100.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('quality-kaizen-ideas', 2026, '8 ideias/mês', 8.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('quality-audit-5s', 2026, '80%', 80.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('quality-kaizen-financial', 2026, 'R$ 9.000/mês', 9000.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),

('supplies-cpv', 2026, '50,5%', 50.5000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('supplies-otd', 2026, '92%', 92.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('supplies-stock-turnover', 2026, '1,95 mês', 1.9500, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('supplies-stock-value', 2026, 'R$ 13.500.000,00', 13500000.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('supplies-negotiation-savings', 2026, 'R$ 20.000/mês', 20000.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),

('engineering-projects-on-time', 2026, '95%', 95.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL),
('engineering-transforma-plus', 2026, 'R$ 15.000/mês', 15000.0000, 'monthly', 'standard', 1, TRUE, NULL, NULL, 'Seed inicial 2026', NULL, NULL)

ON CONFLICT DO NOTHING;

-- =========================================================
-- 6) CURVAS MENSAIS INICIAIS 2026
-- =========================================================

INSERT INTO strategic_indicators.indicator_goal_monthly_targets (
    indicator_goal_id,
    month_number,
    target_value
)
SELECT g.id, t.month_number, t.target_value
FROM strategic_indicators.indicator_goals g
JOIN (
    VALUES
        ('commercial-rol-matrix', 2026, 1, 634000.0000),
        ('commercial-rol-matrix', 2026, 2, 708000.0000),
        ('commercial-rol-matrix', 2026, 3, 920000.0000),
        ('commercial-rol-matrix', 2026, 4, 748000.0000),
        ('commercial-rol-matrix', 2026, 5, 1006000.0000),
        ('commercial-rol-matrix', 2026, 6, 1026000.0000),
        ('commercial-rol-matrix', 2026, 7, 1051000.0000),
        ('commercial-rol-matrix', 2026, 8, 1076000.0000),
        ('commercial-rol-matrix', 2026, 9, 1160000.0000),
        ('commercial-rol-matrix', 2026, 10, 1180000.0000),
        ('commercial-rol-matrix', 2026, 11, 1062000.0000),
        ('commercial-rol-matrix', 2026, 12, 829000.0000),

        ('commercial-rol-branch', 2026, 1, 2882000.0000),
        ('commercial-rol-branch', 2026, 2, 3696000.0000),
        ('commercial-rol-branch', 2026, 3, 3476000.0000),
        ('commercial-rol-branch', 2026, 4, 2902000.0000),
        ('commercial-rol-branch', 2026, 5, 3466000.0000),
        ('commercial-rol-branch', 2026, 6, 3208000.0000),
        ('commercial-rol-branch', 2026, 7, 3386000.0000),
        ('commercial-rol-branch', 2026, 8, 3614000.0000),
        ('commercial-rol-branch', 2026, 9, 3614000.0000),
        ('commercial-rol-branch', 2026, 10, 4636000.0000),
        ('commercial-rol-branch', 2026, 11, 3584000.0000),
        ('commercial-rol-branch', 2026, 12, 2436000.0000)
) AS t(indicator_id, goal_year, month_number, target_value)
    ON g.indicator_id = t.indicator_id
   AND g.goal_year = t.goal_year
   AND g.version = 1
ON CONFLICT (indicator_goal_id, month_number)
DO UPDATE SET
    target_value = EXCLUDED.target_value,
    updated_at = NOW();

-- =========================================================
-- 7) BLOCOS LEGADOS DE COMPATIBILIDADE TEMPORÁRIA
-- =========================================================

INSERT INTO strategic_indicators.module_settings (
    setting_key,
    setting_group,
    payload_json,
    is_active
)
VALUES
(
    'weights.departments',
    'weights',
    '{
      "items": [
        { "department_id": "financial",   "department_name": "Financeiro",  "weight_pct": 15 },
        { "department_id": "hr",          "department_name": "RH",          "weight_pct": 15 },
        { "department_id": "commercial",  "department_name": "Comercial",   "weight_pct": 17 },
        { "department_id": "production",  "department_name": "Produção",    "weight_pct": 17 },
        { "department_id": "quality",     "department_name": "Qualidade",   "weight_pct": 14 },
        { "department_id": "supplies",    "department_name": "Suprimentos", "weight_pct": 12 },
        { "department_id": "engineering", "department_name": "Engenharia",  "weight_pct": 10 }
      ]
    }'::jsonb,
    TRUE
),
(
    'goals.summary',
    'goals',
    '{
      "items": [
        { "department_id": "financial",   "department_name": "Financeiro",  "headline_goal": "Rentabilidade e disciplina financeira", "supporting_focus": "Eficiência operacional e caixa saudável" },
        { "department_id": "hr",          "department_name": "RH",          "headline_goal": "Pessoas engajadas e desenvolvidas",     "supporting_focus": "Clima, capacitação e retenção" },
        { "department_id": "commercial",  "department_name": "Comercial",   "headline_goal": "Crescimento sustentável de receita",    "supporting_focus": "Conversão, novos clientes e expansão" },
        { "department_id": "production",  "department_name": "Produção",    "headline_goal": "Eficiência produtiva e entrega",        "supporting_focus": "Custos, OEE e prazo" },
        { "department_id": "quality",     "department_name": "Qualidade",   "headline_goal": "Confiabilidade e melhoria contínua",    "supporting_focus": "PPM, 5S e Kaizen" },
        { "department_id": "supplies",    "department_name": "Suprimentos", "headline_goal": "Compras e estoque sob controle",       "supporting_focus": "CPV, OTD e capital empatado" },
        { "department_id": "engineering", "department_name": "Engenharia",  "headline_goal": "Entrega no prazo com geração de valor", "supporting_focus": "Projetos e inovação aplicada" }
      ]
    }'::jsonb,
    TRUE
),
(
    'indicators.catalog',
    'indicators',
    '{
      "items": [
        {
          "department_id": "financial",
          "department_name": "Financeiro",
          "short_name": "FIN",
          "department_weight_pct": 15,
          "aggregation_mode": "consolidated",
          "strategic_summary": "Mede rentabilidade, estrutura de custos e eficiência financeira.",
          "indicators": [
            { "id": "financial-ebitda", "name": "EBITDA / Receita Operacional", "weight_pct": 40, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Mede a capacidade de geração de resultado operacional.", "source_key": "financial_ebitda" },
            { "id": "financial-fixed-cost", "name": "% Custos Fixos / Receita Operacional", "weight_pct": 30, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Indica eficiência e estrutura enxuta.", "source_key": "financial_fixed_cost" },
            { "id": "financial-pmr", "name": "Prazo Médio de Recebimento (PMR)", "weight_pct": 30, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Indica eficiência de recebimentos e fluxo de caixa.", "source_key": "financial_pmr" }
          ]
        },
        {
          "department_id": "hr",
          "department_name": "RH",
          "short_name": "RH",
          "department_weight_pct": 15,
          "aggregation_mode": "consolidated",
          "strategic_summary": "Mede engajamento, retenção, desenvolvimento e clima organizacional.",
          "indicators": [
            { "id": "hr-absenteeism", "name": "Absenteísmo", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Mede engajamento e bem-estar.", "source_key": "hr_absenteeism" },
            { "id": "hr-turnover", "name": "Turnover (Rotatividade)", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Mede retenção e estabilidade.", "source_key": "hr_turnover" },
            { "id": "hr-satisfaction", "name": "Satisfação Interna (Clima/Engajamento)", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Reputação interna da cultura.", "source_key": "hr_satisfaction" },
            { "id": "hr-pdi", "name": "% de PDIs Ativos", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Estruturação de desenvolvimento individual.", "source_key": "hr_pdi" },
            { "id": "hr-training-hours", "name": "Horas de Treinamento / Colaborador / mês", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Investimento em formação e capacitação.", "source_key": "hr_training_hours" }
          ]
        },
        {
          "department_id": "commercial",
          "department_name": "Comercial",
          "short_name": "COM",
          "department_weight_pct": 17,
          "aggregation_mode": "average_of_units",
          "strategic_summary": "Mede atingimento de receita, conversão e expansão da base de clientes.",
          "indicators": [
            { "id": "commercial-rol-matrix", "name": "ROL Matriz / Meta", "weight_pct": 25, "scope_type": "per_unit", "performance_direction": "higher_is_better", "strategic_description": "Atingimento da receita da unidade matriz.", "source_key": "commercial_head_office_rol_target" },
            { "id": "commercial-rol-branch", "name": "ROL Filial / Meta", "weight_pct": 25, "scope_type": "per_unit", "performance_direction": "higher_is_better", "strategic_description": "Atingimento da receita da unidade filial.", "source_key": "commercial_branch_rol_target" },
            { "id": "commercial-closing-rate", "name": "Taxa de Fechamento de Negócios", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Conversão de propostas em vendas.", "source_key": "commercial_sales_conversion_rate" },
            { "id": "commercial-new-clients", "name": "Número de Novos Clientes (média mensal)", "weight_pct": 15, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Capacidade de abertura de mercado.", "source_key": "commercial_new_clients_average" },
            { "id": "commercial-new-rol", "name": "% ROL de Novos Clientes", "weight_pct": 15, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Participação dos novos no total da receita.", "source_key": "commercial_new_clients_rol_pct" }
          ]
        },
        {
          "department_id": "production",
          "department_name": "Produção",
          "short_name": "PRO",
          "department_weight_pct": 17,
          "aggregation_mode": "average_of_units",
          "strategic_summary": "Mede eficiência produtiva, custos, ativos e prazo de entrega.",
          "indicators": [
            { "id": "production-direct-labor", "name": "Custo Mão de Obra Direta / ROL", "weight_pct": 25, "scope_type": "per_unit", "performance_direction": "lower_is_better", "strategic_description": "Eficiência da mão de obra direta.", "source_key": "production_direct_labor" },
            { "id": "production-costs", "name": "Custos de Produção / ROL", "weight_pct": 20, "scope_type": "per_unit", "performance_direction": "lower_is_better", "strategic_description": "Controle de desperdícios e produtividade.", "source_key": "production_cost" },
            { "id": "production-depreciation", "name": "Depreciação / ROL", "weight_pct": 10, "scope_type": "per_unit", "performance_direction": "lower_is_better", "strategic_description": "Uso racional da capacidade instalada.", "source_key": "production_depreciation" },
            { "id": "production-oee", "name": "OEE (Eficiência Global dos Equip.)", "weight_pct": 20, "scope_type": "per_unit", "performance_direction": "higher_is_better", "strategic_description": "Utilização real dos ativos produtivos.", "source_key": "production_oee" },
            { "id": "production-otd", "name": "OTD (Entrega no Prazo)", "weight_pct": 25, "scope_type": "per_unit", "performance_direction": "higher_is_better", "strategic_description": "Cumprimento do prazo prometido ao cliente.", "source_key": "production_otd" }
          ]
        },
        {
          "department_id": "quality",
          "department_name": "Qualidade",
          "short_name": "QUA",
          "department_weight_pct": 14,
          "aggregation_mode": "consolidated",
          "strategic_summary": "Mede confiabilidade do produto e avanço da melhoria contínua.",
          "indicators": [
            { "id": "quality-ppm-internal", "name": "PPM Interno", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Indicador de falhas detectadas internamente.", "source_key": "quality_ppm_internal" },
            { "id": "quality-ppm-external", "name": "PPM Externo", "weight_pct": 30, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Indicador de falhas detectadas pelo cliente.", "source_key": "quality_ppm_external" },
            { "id": "quality-kaizen-ideas", "name": "Ideias Aprovadas para Kaizen/mês", "weight_pct": 15, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Cultura de melhoria e participação.", "source_key": "quality_kaizen_ideas" },
            { "id": "quality-audit-5s", "name": "Nota Auditoria 5S", "weight_pct": 15, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Padronização, organização e disciplina.", "source_key": "quality_audit_5s" },
            { "id": "quality-kaizen-financial", "name": "Ganhos Financeiros Kaizen/mês", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Impacto financeiro direto das melhorias Kaizen.", "source_key": "quality_kaizen_financial" }
          ]
        },
        {
          "department_id": "supplies",
          "department_name": "Suprimentos",
          "short_name": "SUP",
          "department_weight_pct": 12,
          "aggregation_mode": "consolidated",
          "strategic_summary": "Mede eficiência de compras, estoque e negociação com fornecedores.",
          "indicators": [
            { "id": "supplies-cpv", "name": "CPV Consolidado (matriz e filial)", "weight_pct": 30, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Eficiência nas compras totais.", "source_key": "supplies_cpv" },
            { "id": "supplies-otd", "name": "OTD Consolidado de Compras", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Entregas dentro do prazo pelos fornecedores.", "source_key": "supplies_otd" },
            { "id": "supplies-stock-turnover", "name": "Giro de Estoque Consolidado", "weight_pct": 20, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Rotatividade do estoque total.", "source_key": "supplies_stock_turnover" },
            { "id": "supplies-stock-value", "name": "Valor Total do Estoque Consolidado", "weight_pct": 15, "scope_type": "consolidated", "performance_direction": "lower_is_better", "strategic_description": "Estoque como capital parado.", "source_key": "supplies_stock_value" },
            { "id": "supplies-negotiation-savings", "name": "Economia em Negociações de Compras", "weight_pct": 15, "scope_type": "consolidated", "performance_direction": "higher_is_better", "strategic_description": "Eficiência em negociações e renegociações com fornecedores.", "source_key": "supplies_negotiation_savings" }
          ]
        },
        {
          "department_id": "engineering",
          "department_name": "Engenharia",
          "short_name": "ENG",
          "department_weight_pct": 10,
          "aggregation_mode": "average_of_units",
          "strategic_summary": "Mede entrega no prazo e geração de valor via inovação e digitalização.",
          "indicators": [
            { "id": "engineering-projects-on-time", "name": "% de Projetos Concluídos no Prazo", "weight_pct": 60, "scope_type": "per_unit", "performance_direction": "higher_is_better", "strategic_description": "Compromisso com entregas e gestão eficiente de escopo.", "source_key": "lmp" },
            { "id": "engineering-transforma-plus", "name": "Ganhos Financeiros do TRANSFORMA+ DELPI", "weight_pct": 40, "scope_type": "per_unit", "performance_direction": "higher_is_better", "strategic_description": "Valor gerado por inovações e digitalização via TRANSFORMA+.", "source_key": "transforma_mais" }
          ]
        }
      ]
    }'::jsonb,
    TRUE
)
ON CONFLICT (setting_key)
DO UPDATE SET
    payload_json = EXCLUDED.payload_json,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

COMMIT;