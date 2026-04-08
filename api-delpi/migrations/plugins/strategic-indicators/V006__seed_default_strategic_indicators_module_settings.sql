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
        { "key": "source_of_truth", "label": "Fonte oficial", "value": "api-delpi + strategic_indicators.module_settings" }
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
        { "key": "calculation_rule", "label": "Regra de cálculo", "value": "Backend", "observation": "Frontend não deve calcular score oficial" }
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
              "goal_label": "13,0%",
              "goal_value": 13.0,
              "goal_periodicity": "monthly",
              "strategic_description": "Mede a capacidade de geração de resultado operacional.",
              "scope_type": "consolidated",
              "source_key": "financial_ebitda"
            },
            {
              "id": "financial-fixed-cost",
              "name": "% Custos Fixos / Receita Operacional",
              "weight_pct": 30,
              "goal_label": "14,0%",
              "goal_value": 14.0,
              "goal_periodicity": "monthly",
              "strategic_description": "Indica eficiência e estrutura enxuta.",
              "scope_type": "consolidated",
              "source_key": "financial_fixed_cost"
            },
            {
              "id": "financial-pmr",
              "name": "Prazo Médio de Recebimento (PMR)",
              "weight_pct": 30,
              "goal_label": "39 dias",
              "goal_value": 39,
              "goal_periodicity": "monthly",
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
              "goal_label": "2,0%",
              "goal_value": 2.0,
              "goal_periodicity": "monthly",
              "strategic_description": "Mede engajamento e bem-estar.",
              "scope_type": "consolidated",
              "source_key": "hr_absenteeism"
            },
            {
              "id": "hr-turnover",
              "name": "Turnover (Rotatividade)",
              "weight_pct": 20,
              "goal_label": "1,5% ao mês",
              "goal_value": 1.5,
              "goal_periodicity": "monthly",
              "strategic_description": "Mede retenção e estabilidade.",
              "scope_type": "consolidated",
              "source_key": "hr_turnover"
            },
            {
              "id": "hr-satisfaction",
              "name": "Satisfação Interna (Clima/Engajamento)",
              "weight_pct": 20,
              "goal_label": "85% de satisfação",
              "goal_value": 85,
              "goal_periodicity": "monthly",
              "strategic_description": "Reputação interna da cultura.",
              "scope_type": "consolidated",
              "source_key": "hr_satisfaction"
            },
            {
              "id": "hr-pdi",
              "name": "% de PDIs Ativos",
              "weight_pct": 20,
              "goal_label": "100%",
              "goal_value": 100,
              "goal_periodicity": "monthly",
              "strategic_description": "Estruturação de desenvolvimento individual.",
              "scope_type": "consolidated",
              "source_key": "hr_pdi"
            },
            {
              "id": "hr-training-hours",
              "name": "Horas de Treinamento / Colaborador / mês",
              "weight_pct": 20,
              "goal_label": "2 horas/mês",
              "goal_value": 2,
              "goal_periodicity": "monthly",
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
              "goal_label": "100%",
              "goal_value": 100,
              "goal_periodicity": "annual",
              "strategic_description": "Atingimento da receita da unidade matriz.",
              "scope_type": "per_unit",
              "source_key": "commercial_head_office_rol_target"
            },
            {
              "id": "commercial-rol-branch",
              "name": "ROL Filial / Meta",
              "weight_pct": 25,
              "goal_label": "100%",
              "goal_value": 100,
              "goal_periodicity": "annual",
              "strategic_description": "Atingimento da receita da unidade filial.",
              "scope_type": "per_unit",
              "source_key": "commercial_branch_rol_target"
            },
            {
              "id": "commercial-closing-rate",
              "name": "Taxa de Fechamento de Negócios",
              "weight_pct": 20,
              "goal_label": "30%",
              "goal_value": 30,
              "goal_periodicity": "monthly",
              "strategic_description": "Conversão de propostas em vendas.",
              "scope_type": "consolidated",
              "source_key": "commercial_sales_conversion_rate"
            },
            {
              "id": "commercial-new-clients",
              "name": "Número de Novos Clientes (média mensal)",
              "weight_pct": 15,
              "goal_label": "10 novos/mês",
              "goal_value": 10,
              "goal_periodicity": "monthly",
              "strategic_description": "Capacidade de abertura de mercado.",
              "scope_type": "consolidated",
              "source_key": "commercial_new_clients_average"
            },
            {
              "id": "commercial-new-rol",
              "name": "% ROL de Novos Clientes",
              "weight_pct": 15,
              "goal_label": "12%",
              "goal_value": 12,
              "goal_periodicity": "monthly",
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
              "goal_label": "10,0%",
              "goal_value": 10,
              "goal_periodicity": "monthly",
              "strategic_description": "Eficiência da mão de obra direta.",
              "scope_type": "per_unit",
              "source_key": "production_direct_labor"
            },
            {
              "id": "production-costs",
              "name": "Custos de Produção / ROL",
              "weight_pct": 20,
              "goal_label": "32,0%",
              "goal_value": 32,
              "goal_periodicity": "monthly",
              "strategic_description": "Controle de desperdícios e produtividade.",
              "scope_type": "per_unit",
              "source_key": "production_cost"
            },
            {
              "id": "production-depreciation",
              "name": "Depreciação / ROL",
              "weight_pct": 10,
              "goal_label": "1,5%",
              "goal_value": 1.5,
              "goal_periodicity": "monthly",
              "strategic_description": "Uso racional da capacidade instalada.",
              "scope_type": "per_unit",
              "source_key": "production_depreciation"
            },
            {
              "id": "production-oee",
              "name": "OEE (Eficiência Global dos Equip.)",
              "weight_pct": 20,
              "goal_label": "70%",
              "goal_value": 70,
              "goal_periodicity": "monthly",
              "strategic_description": "Utilização real dos ativos produtivos.",
              "scope_type": "per_unit",
              "source_key": "production_oee"
            },
            {
              "id": "production-otd",
              "name": "OTD (Entrega no Prazo)",
              "weight_pct": 25,
              "goal_label": "92%",
              "goal_value": 92,
              "goal_periodicity": "monthly",
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
              "goal_label": "1.400 PPM",
              "goal_value": 1400,
              "goal_periodicity": "monthly",
              "strategic_description": "Indicador de falhas detectadas internamente.",
              "scope_type": "consolidated",
              "source_key": "quality_ppm_internal"
            },
            {
              "id": "quality-ppm-external",
              "name": "PPM Externo",
              "weight_pct": 30,
              "goal_label": "1.100 PPM",
              "goal_value": 1100,
              "goal_periodicity": "monthly",
              "strategic_description": "Indicador de falhas detectadas pelo cliente.",
              "scope_type": "consolidated",
              "source_key": "quality_ppm_external"
            },
            {
              "id": "quality-kaizen-ideas",
              "name": "Ideias Aprovadas para Kaizen/mês",
              "weight_pct": 15,
              "goal_label": "8 ideias/mês",
              "goal_value": 8,
              "goal_periodicity": "monthly",
              "strategic_description": "Cultura de melhoria e participação.",
              "scope_type": "consolidated",
              "source_key": "quality_kaizen_ideas"
            },
            {
              "id": "quality-audit-5s",
              "name": "Nota Auditoria 5S",
              "weight_pct": 15,
              "goal_label": "80%",
              "goal_value": 80,
              "goal_periodicity": "monthly",
              "strategic_description": "Padronização, organização e disciplina.",
              "scope_type": "consolidated",
              "source_key": "quality_audit_5s"
            },
            {
              "id": "quality-kaizen-financial",
              "name": "Ganhos Financeiros Kaizen/mês",
              "weight_pct": 20,
              "goal_label": "R$ 9.000/mês",
              "goal_value": 9000,
              "goal_periodicity": "monthly",
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
              "goal_label": "50,5%",
              "goal_value": 50.5,
              "goal_periodicity": "monthly",
              "strategic_description": "Eficiência nas compras totais.",
              "scope_type": "consolidated",
              "source_key": "supplies_cpv"
            },
            {
              "id": "supplies-otd",
              "name": "OTD Consolidado de Compras",
              "weight_pct": 20,
              "goal_label": "92%",
              "goal_value": 92,
              "goal_periodicity": "monthly",
              "strategic_description": "Entregas dentro do prazo pelos fornecedores.",
              "scope_type": "consolidated",
              "source_key": "supplies_otd"
            },
            {
              "id": "supplies-stock-turnover",
              "name": "Giro de Estoque Consolidado",
              "weight_pct": 20,
              "goal_label": "1,95 mês",
              "goal_value": 1.95,
              "goal_periodicity": "monthly",
              "strategic_description": "Rotatividade do estoque total.",
              "scope_type": "consolidated",
              "source_key": "supplies_stock_turnover"
            },
            {
              "id": "supplies-stock-value",
              "name": "Valor Total do Estoque Consolidado",
              "weight_pct": 15,
              "goal_label": "R$ 13.500.000,00",
              "goal_value": 13500000,
              "goal_periodicity": "monthly",
              "strategic_description": "Estoque como capital parado.",
              "scope_type": "consolidated",
              "source_key": "supplies_stock_value"
            },
            {
              "id": "supplies-negotiation-savings",
              "name": "Economia em Negociações de Compras",
              "weight_pct": 15,
              "goal_label": "R$ 20.000/mês",
              "goal_value": 20000,
              "goal_periodicity": "monthly",
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
              "goal_label": "95%",
              "goal_value": 95,
              "goal_periodicity": "monthly",
              "strategic_description": "Compromisso com entregas e gestão eficiente de escopo.",
              "scope_type": "per_unit",
              "source_key": "lmp"
            },
            {
              "id": "engineering-transforma-plus",
              "name": "Ganhos Financeiros do TRANSFORMA+ DELPI",
              "weight_pct": 40,
              "goal_label": "R$ 15.000/mês",
              "goal_value": 15000,
              "goal_periodicity": "monthly",
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