BEGIN;

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
    'parameters.global',
    'parameters',
    '{
      "items": [
        { "key": "igd_scale", "label": "Escala oficial do IGD", "value": "0 a 10" },
        { "key": "executive_refresh", "label": "Frequência executiva", "value": "Mensal" },
        { "key": "source_of_truth", "label": "Fonte oficial", "value": "api-delpi + strategic_indicators.module_settings + strategic_indicators.indicator_goals" }
      ]
    }'::jsonb,
    TRUE
),
(
    'governance.notes',
    'governance',
    '{
      "items": [
        { "key": "catalog_owner", "label": "Responsável pelo catálogo", "value": "Administração do módulo", "observation": "Mudanças estruturais devem ser versionadas" },
        { "key": "calculation_rule", "label": "Regra de cálculo", "value": "Backend", "observation": "Frontend não deve calcular score oficial" },
        { "key": "goal_versioning", "label": "Versionamento de metas", "value": "Ativo", "observation": "Metas analíticas agora são resolvidas pela tabela indicator_goals" }
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
            {
              "id": "financial-ebitda",
              "name": "EBITDA / Receita Operacional",
              "weight_pct": 40,
              "strategic_description": "Mede a capacidade de geração de resultado operacional.",
              "scope_type": "consolidated",
              "source_key": "financial_ebitda"
            },
            {
              "id": "financial-fixed-cost",
              "name": "% Custos Fixos / Receita Operacional",
              "weight_pct": 30,
              "strategic_description": "Indica eficiência e estrutura enxuta.",
              "scope_type": "consolidated",
              "source_key": "financial_fixed_cost"
            },
            {
              "id": "financial-pmr",
              "name": "Prazo Médio de Recebimento (PMR)",
              "weight_pct": 30,
              "strategic_description": "Indica eficiência de recebimentos e fluxo de caixa.",
              "scope_type": "consolidated",
              "source_key": "financial_pmr"
            }
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
            {
              "id": "hr-absenteeism",
              "name": "Absenteísmo",
              "weight_pct": 20,
              "strategic_description": "Mede engajamento e bem-estar.",
              "scope_type": "consolidated",
              "source_key": "hr_absenteeism"
            },
            {
              "id": "hr-turnover",
              "name": "Turnover (Rotatividade)",
              "weight_pct": 20,
              "strategic_description": "Mede retenção e estabilidade.",
              "scope_type": "consolidated",
              "source_key": "hr_turnover"
            },
            {
              "id": "hr-satisfaction",
              "name": "Satisfação Interna (Clima/Engajamento)",
              "weight_pct": 20,
              "strategic_description": "Reputação interna da cultura.",
              "scope_type": "consolidated",
              "source_key": "hr_satisfaction"
            },
            {
              "id": "hr-pdi",
              "name": "% de PDIs Ativos",
              "weight_pct": 20,
              "strategic_description": "Estruturação de desenvolvimento individual.",
              "scope_type": "consolidated",
              "source_key": "hr_pdi"
            },
            {
              "id": "hr-training-hours",
              "name": "Horas de Treinamento / Colaborador / mês",
              "weight_pct": 20,
              "strategic_description": "Investimento em formação e capacitação.",
              "scope_type": "consolidated",
              "source_key": "hr_training_hours"
            }
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
            {
              "id": "commercial-rol-matrix",
              "name": "ROL Matriz / Meta",
              "weight_pct": 25,
              "strategic_description": "Atingimento da receita da unidade matriz.",
              "scope_type": "per_unit",
              "source_key": "commercial_head_office_rol_target"
            },
            {
              "id": "commercial-rol-branch",
              "name": "ROL Filial / Meta",
              "weight_pct": 25,
              "strategic_description": "Atingimento da receita da unidade filial.",
              "scope_type": "per_unit",
              "source_key": "commercial_branch_rol_target"
            },
            {
              "id": "commercial-closing-rate",
              "name": "Taxa de Fechamento de Negócios",
              "weight_pct": 20,
              "strategic_description": "Conversão de propostas em vendas.",
              "scope_type": "consolidated",
              "source_key": "commercial_sales_conversion_rate"
            },
            {
              "id": "commercial-new-clients",
              "name": "Número de Novos Clientes (média mensal)",
              "weight_pct": 15,
              "strategic_description": "Capacidade de abertura de mercado.",
              "scope_type": "consolidated",
              "source_key": "commercial_new_clients_average"
            },
            {
              "id": "commercial-new-rol",
              "name": "% ROL de Novos Clientes",
              "weight_pct": 15,
              "strategic_description": "Participação dos novos no total da receita.",
              "scope_type": "consolidated",
              "source_key": "commercial_new_clients_rol_pct"
            }
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
            {
              "id": "production-direct-labor",
              "name": "Custo Mão de Obra Direta / ROL",
              "weight_pct": 25,
              "strategic_description": "Eficiência da mão de obra direta.",
              "scope_type": "per_unit",
              "source_key": "production_direct_labor"
            },
            {
              "id": "production-costs",
              "name": "Custos de Produção / ROL",
              "weight_pct": 20,
              "strategic_description": "Controle de desperdícios e produtividade.",
              "scope_type": "per_unit",
              "source_key": "production_cost"
            },
            {
              "id": "production-depreciation",
              "name": "Depreciação / ROL",
              "weight_pct": 10,
              "strategic_description": "Uso racional da capacidade instalada.",
              "scope_type": "per_unit",
              "source_key": "production_depreciation"
            },
            {
              "id": "production-oee",
              "name": "OEE (Eficiência Global dos Equip.)",
              "weight_pct": 20,
              "strategic_description": "Utilização real dos ativos produtivos.",
              "scope_type": "per_unit",
              "source_key": "production_oee"
            },
            {
              "id": "production-otd",
              "name": "OTD (Entrega no Prazo)",
              "weight_pct": 25,
              "strategic_description": "Cumprimento do prazo prometido ao cliente.",
              "scope_type": "per_unit",
              "source_key": "production_otd"
            }
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
            {
              "id": "quality-ppm-internal",
              "name": "PPM Interno",
              "weight_pct": 20,
              "strategic_description": "Indicador de falhas detectadas internamente.",
              "scope_type": "consolidated",
              "source_key": "quality_ppm_internal"
            },
            {
              "id": "quality-ppm-external",
              "name": "PPM Externo",
              "weight_pct": 30,
              "strategic_description": "Indicador de falhas detectadas pelo cliente.",
              "scope_type": "consolidated",
              "source_key": "quality_ppm_external"
            },
            {
              "id": "quality-kaizen-ideas",
              "name": "Ideias Aprovadas para Kaizen/mês",
              "weight_pct": 15,
              "strategic_description": "Cultura de melhoria e participação.",
              "scope_type": "consolidated",
              "source_key": "quality_kaizen_ideas"
            },
            {
              "id": "quality-audit-5s",
              "name": "Nota Auditoria 5S",
              "weight_pct": 15,
              "strategic_description": "Padronização, organização e disciplina.",
              "scope_type": "consolidated",
              "source_key": "quality_audit_5s"
            },
            {
              "id": "quality-kaizen-financial",
              "name": "Ganhos Financeiros Kaizen/mês",
              "weight_pct": 20,
              "strategic_description": "Impacto financeiro direto das melhorias Kaizen.",
              "scope_type": "consolidated",
              "source_key": "quality_kaizen_financial"
            }
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
            {
              "id": "supplies-cpv",
              "name": "CPV Consolidado (matriz e filial)",
              "weight_pct": 30,
              "strategic_description": "Eficiência nas compras totais.",
              "scope_type": "consolidated",
              "source_key": "supplies_cpv"
            },
            {
              "id": "supplies-otd",
              "name": "OTD Consolidado de Compras",
              "weight_pct": 20,
              "strategic_description": "Entregas dentro do prazo pelos fornecedores.",
              "scope_type": "consolidated",
              "source_key": "supplies_otd"
            },
            {
              "id": "supplies-stock-turnover",
              "name": "Giro de Estoque Consolidado",
              "weight_pct": 20,
              "strategic_description": "Rotatividade do estoque total.",
              "scope_type": "consolidated",
              "source_key": "supplies_stock_turnover"
            },
            {
              "id": "supplies-stock-value",
              "name": "Valor Total do Estoque Consolidado",
              "weight_pct": 15,
              "strategic_description": "Estoque como capital parado.",
              "scope_type": "consolidated",
              "source_key": "supplies_stock_value"
            },
            {
              "id": "supplies-negotiation-savings",
              "name": "Economia em Negociações de Compras",
              "weight_pct": 15,
              "strategic_description": "Eficiência em negociações e renegociações com fornecedores.",
              "scope_type": "consolidated",
              "source_key": "supplies_negotiation_savings"
            }
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
            {
              "id": "engineering-projects-on-time",
              "name": "% de Projetos Concluídos no Prazo",
              "weight_pct": 60,
              "strategic_description": "Compromisso com entregas e gestão eficiente de escopo.",
              "scope_type": "per_unit",
              "source_key": "lmp"
            },
            {
              "id": "engineering-transforma-plus",
              "name": "Ganhos Financeiros do TRANSFORMA+ DELPI",
              "weight_pct": 40,
              "strategic_description": "Valor gerado por inovações e digitalização via TRANSFORMA+.",
              "scope_type": "per_unit",
              "source_key": "transforma_mais"
            }
          ]
        }
      ]
    }'::jsonb,
    TRUE
);

INSERT INTO strategic_indicators.indicator_goals (
    indicator_id,
    goal_year,
    goal_label,
    goal_value,
    goal_periodicity,
    version,
    is_active,
    created_by_email,
    updated_by_email
)
VALUES
    ('financial-ebitda', 2026, '13,0%', 13.0, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('financial-fixed-cost', 2026, '14,0%', 14.0, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('financial-pmr', 2026, '39 dias', 39, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),

    ('hr-absenteeism', 2026, '2,0%', 2.0, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('hr-turnover', 2026, '1,5% ao mês', 1.5, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('hr-satisfaction', 2026, '85% de satisfação', 85, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('hr-pdi', 2026, '100%', 100, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('hr-training-hours', 2026, '2 horas/mês', 2, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),

    ('commercial-rol-matrix', 2026, '100%', 100, 'annual', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('commercial-rol-branch', 2026, '100%', 100, 'annual', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('commercial-closing-rate', 2026, '30%', 30, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('commercial-new-clients', 2026, '10 novos/mês', 10, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('commercial-new-rol', 2026, '12%', 12, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),

    ('production-direct-labor', 2026, '10,0%', 10, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('production-costs', 2026, '32,0%', 32, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('production-depreciation', 2026, '1,5%', 1.5, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('production-oee', 2026, '70%', 70, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('production-otd', 2026, '92%', 92, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),

    ('quality-ppm-internal', 2026, '1.400 PPM', 1400, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('quality-ppm-external', 2026, '1.100 PPM', 1100, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('quality-kaizen-ideas', 2026, '8 ideias/mês', 8, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('quality-audit-5s', 2026, '80%', 80, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('quality-kaizen-financial', 2026, 'R$ 9.000/mês', 9000, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),

    ('supplies-cpv', 2026, '50,5%', 50.5, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('supplies-otd', 2026, '92%', 92, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('supplies-stock-turnover', 2026, '1,95 mês', 1.95, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('supplies-stock-value', 2026, 'R$ 13.500.000,00', 13500000, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('supplies-negotiation-savings', 2026, 'R$ 20.000/mês', 20000, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),

    ('engineering-projects-on-time', 2026, '95%', 95, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local'),
    ('engineering-transforma-plus', 2026, 'R$ 15.000/mês', 15000, 'monthly', 1, TRUE, 'seed@delpi.local', 'seed@delpi.local');

COMMIT;