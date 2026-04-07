BEGIN;

INSERT INTO strategic_indicators.module_settings (
    setting_key,
    setting_group,
    payload_json,
    is_active,
    updated_by_user_id,
    updated_by_email
)
VALUES
(
    'weights.departments',
    'weights',
    '{
      "items": [
        { "department_id": "financial", "department_name": "Financeiro", "weight_pct": 15 },
        { "department_id": "hr", "department_name": "RH", "weight_pct": 15 },
        { "department_id": "commercial", "department_name": "Comercial", "weight_pct": 17 },
        { "department_id": "production", "department_name": "Produção", "weight_pct": 17 },
        { "department_id": "quality", "department_name": "Qualidade", "weight_pct": 14 },
        { "department_id": "supplies", "department_name": "Suprimentos", "weight_pct": 12 },
        { "department_id": "engineering", "department_name": "Engenharia", "weight_pct": 10 }
      ]
    }'::jsonb,
    TRUE,
    NULL,
    NULL
),
(
    'goals.summary',
    'goals',
    '{
      "items": [
        {
          "department_id": "financial",
          "department_name": "Financeiro",
          "headline_goal": "EBITDA 13,0%",
          "supporting_focus": "Eficiência estrutural e PMR de 39 dias."
        },
        {
          "department_id": "hr",
          "department_name": "RH",
          "headline_goal": "Turnover 1,5% ao mês",
          "supporting_focus": "Satisfação interna de 85% e PDIs ativos em 100%."
        },
        {
          "department_id": "commercial",
          "department_name": "Comercial",
          "headline_goal": "Fechamento 30%",
          "supporting_focus": "ROL matriz/filial em 100% e novos clientes em 10/mês."
        },
        {
          "department_id": "production",
          "department_name": "Produção",
          "headline_goal": "OEE 70%",
          "supporting_focus": "OTD em 92% e controle dos custos de produção."
        },
        {
          "department_id": "quality",
          "department_name": "Qualidade",
          "headline_goal": "PPM Externo 1.100 PPM",
          "supporting_focus": "5S em 80% e ganhos financeiros Kaizen crescentes."
        },
        {
          "department_id": "supplies",
          "department_name": "Suprimentos",
          "headline_goal": "CPV 50,5%",
          "supporting_focus": "OTD compras em 92%, giro 1,95 mês e economia em negociações de R$ 20.000/mês."
        },
        {
          "department_id": "engineering",
          "department_name": "Engenharia",
          "headline_goal": "Projetos no prazo 95%",
          "supporting_focus": "Ganhos do TRANSFORMA+ DELPI em R$ 15.000/mês."
        }
      ]
    }'::jsonb,
    TRUE,
    NULL,
    NULL
),
(
    'parameters.global',
    'parameters',
    '{
      "items": [
        {
          "key": "panel_periodicity",
          "label": "Periodicidade do painel",
          "value": "Mensal"
        },
        {
          "key": "index_scale",
          "label": "Escala do índice",
          "value": "0 a 10"
        },
        {
          "key": "example_igd_value",
          "label": "IGD de exemplo consolidado",
          "value": "7,8"
        },
        {
          "key": "current_example_band",
          "label": "Faixa atual do exemplo consolidado",
          "value": "Satisfatório com Alertas"
        },
        {
          "key": "render_mode",
          "label": "Renderização do módulo",
          "value": "Federated"
        }
      ]
    }'::jsonb,
    TRUE,
    NULL,
    NULL
),
(
    'governance.notes',
    'governance',
    '{
      "items": [
        {
          "key": "settings_route",
          "label": "Rota administrativa",
          "value": "/apps/strategic-indicators/settings",
          "observation": "Protegida por strategic-indicators.settings.manage"
        },
        {
          "key": "backend_base_url",
          "label": "Backend base URL",
          "value": "/apps/api-delpi/strategic-indicators",
          "observation": "Backend compartilhado via api-delpi com JWT validado"
        },
        {
          "key": "official_reference",
          "label": "Fonte oficial do catálogo",
          "value": "IGD/IDD DELPI consolidado",
          "observation": "Seed default alinhado ao documento oficial consolidado."
        }
      ]
    }'::jsonb,
    TRUE,
    NULL,
    NULL
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
          "strategic_summary": "Geração de resultado operacional, eficiência da estrutura e fluxo de caixa.",
          "indicators": [
            {
              "id": "financial-ebitda",
              "name": "EBITDA / Receita Operacional",
              "weight_pct": 40,
              "goal_2026": "13,0%",
              "strategic_description": "Mede a capacidade de geração de resultado operacional."
            },
            {
              "id": "financial-fixed-costs",
              "name": "% Custos Fixos / Receita Operacional",
              "weight_pct": 30,
              "goal_2026": "14,0%",
              "strategic_description": "Indica eficiência e estrutura enxuta."
            },
            {
              "id": "financial-pmr",
              "name": "Prazo Médio de Recebimento (PMR)",
              "weight_pct": 30,
              "goal_2026": "39 dias",
              "strategic_description": "Indica eficiência de recebimentos e fluxo de caixa."
            }
          ]
        },
        {
          "department_id": "hr",
          "department_name": "RH",
          "short_name": "RH",
          "department_weight_pct": 15,
          "strategic_summary": "Mede engajamento, retenção, desenvolvimento individual e capacitação contínua.",
          "indicators": [
            {
              "id": "hr-absenteeism",
              "name": "Absenteísmo",
              "weight_pct": 20,
              "goal_2026": "2,0%",
              "strategic_description": "Mede engajamento e bem-estar."
            },
            {
              "id": "hr-turnover",
              "name": "Turnover (Rotatividade)",
              "weight_pct": 20,
              "goal_2026": "1,5% ao mês",
              "strategic_description": "Mede retenção e estabilidade."
            },
            {
              "id": "hr-satisfaction",
              "name": "Satisfação Interna (Clima/Engajamento)",
              "weight_pct": 20,
              "goal_2026": "85% de satisfação",
              "strategic_description": "Reputação interna da cultura."
            },
            {
              "id": "hr-pdi",
              "name": "% de PDIs Ativos",
              "weight_pct": 20,
              "goal_2026": "100%",
              "strategic_description": "Estruturação de desenvolvimento individual."
            },
            {
              "id": "hr-training",
              "name": "Horas de Treinamento/Colaborador/mês",
              "weight_pct": 20,
              "goal_2026": "2 horas/mês",
              "strategic_description": "Investimento em formação e capacitação."
            }
          ]
        },
        {
          "department_id": "commercial",
          "department_name": "Comercial",
          "short_name": "COM",
          "department_weight_pct": 17,
          "strategic_summary": "Mede receita, conversão de negócios e expansão da base de clientes.",
          "indicators": [
            {
              "id": "commercial-rol-matrix",
              "name": "ROL Matriz / Meta",
              "weight_pct": 25,
              "goal_2026": "100%",
              "strategic_description": "Atingimento da receita da unidade matriz."
            },
            {
              "id": "commercial-rol-branch",
              "name": "ROL Filial / Meta",
              "weight_pct": 25,
              "goal_2026": "100%",
              "strategic_description": "Atingimento da receita da unidade filial."
            },
            {
              "id": "commercial-closing-rate",
              "name": "Taxa de Fechamento de Negócios",
              "weight_pct": 20,
              "goal_2026": "30%",
              "strategic_description": "Conversão de propostas em vendas."
            },
            {
              "id": "commercial-new-clients",
              "name": "Número de Novos Clientes (média mensal)",
              "weight_pct": 15,
              "goal_2026": "10 novos/mês",
              "strategic_description": "Capacidade de abertura de mercado."
            },
            {
              "id": "commercial-new-rol",
              "name": "% ROL de Novos Clientes",
              "weight_pct": 15,
              "goal_2026": "12%",
              "strategic_description": "Participação dos novos no total da receita."
            }
          ]
        },
        {
          "department_id": "production",
          "department_name": "Produção",
          "short_name": "PRD",
          "department_weight_pct": 17,
          "strategic_summary": "Mede eficiência produtiva, uso dos ativos e cumprimento do prazo ao cliente.",
          "indicators": [
            {
              "id": "production-direct-labor",
              "name": "Custo Mão de Obra Direta / ROL",
              "weight_pct": 25,
              "goal_2026": "10,0%",
              "strategic_description": "Eficiência da mão de obra direta."
            },
            {
              "id": "production-costs",
              "name": "Custos de Produção / ROL",
              "weight_pct": 20,
              "goal_2026": "32,0%",
              "strategic_description": "Controle de desperdícios e produtividade."
            },
            {
              "id": "production-depreciation",
              "name": "Depreciação / ROL",
              "weight_pct": 10,
              "goal_2026": "1,5%",
              "strategic_description": "Uso racional da capacidade instalada."
            },
            {
              "id": "production-oee",
              "name": "OEE (Eficiência Global dos Equip.)",
              "weight_pct": 20,
              "goal_2026": "70%",
              "strategic_description": "Utilização real dos ativos produtivos."
            },
            {
              "id": "production-otd",
              "name": "OTD (Entrega no Prazo)",
              "weight_pct": 25,
              "goal_2026": "92%",
              "strategic_description": "Cumprimento do prazo prometido ao cliente."
            }
          ]
        },
        {
          "department_id": "quality",
          "department_name": "Qualidade",
          "short_name": "QLD",
          "department_weight_pct": 14,
          "strategic_summary": "Mede falhas internas e externas, disciplina operacional e ganhos com melhoria contínua.",
          "indicators": [
            {
              "id": "quality-ppm-internal",
              "name": "PPM Interno",
              "weight_pct": 20,
              "goal_2026": "1.400 PPM",
              "strategic_description": "Indicador de falhas detectadas internamente."
            },
            {
              "id": "quality-ppm-external",
              "name": "PPM Externo",
              "weight_pct": 30,
              "goal_2026": "1.100 PPM",
              "strategic_description": "Indicador de falhas detectadas pelo cliente."
            },
            {
              "id": "quality-kaizen-ideas",
              "name": "Ideias Aprovadas para Kaizen/mês",
              "weight_pct": 15,
              "goal_2026": "8 ideias/mês",
              "strategic_description": "Cultura de melhoria e participação."
            },
            {
              "id": "quality-audit-5s",
              "name": "Nota Auditoria 5S",
              "weight_pct": 15,
              "goal_2026": "80%",
              "strategic_description": "Padronização, organização e disciplina."
            },
            {
              "id": "quality-kaizen-financial",
              "name": "Ganhos Financeiros Kaizen/mês",
              "weight_pct": 20,
              "goal_2026": "R$ 4.500 (1º S), R$ 9.000 (2º S)",
              "strategic_description": "Impacto financeiro direto das melhorias Kaizen."
            }
          ]
        },
        {
          "department_id": "supplies",
          "department_name": "Suprimentos",
          "short_name": "SUP",
          "department_weight_pct": 12,
          "strategic_summary": "Mede eficiência em compras, estoque e negociações com fornecedores.",
          "indicators": [
            {
              "id": "supplies-cpv",
              "name": "CPV Consolidado (matriz e filial)",
              "weight_pct": 30,
              "goal_2026": "50,5%",
              "strategic_description": "Eficiência nas compras totais."
            },
            {
              "id": "supplies-otd-purchases",
              "name": "OTD Consolidado de Compras",
              "weight_pct": 20,
              "goal_2026": "92%",
              "strategic_description": "Entregas dentro do prazo pelos fornecedores."
            },
            {
              "id": "supplies-stock-turnover",
              "name": "Giro de Estoque Consolidado",
              "weight_pct": 20,
              "goal_2026": "1,95 mês",
              "strategic_description": "Rotatividade do estoque total."
            },
            {
              "id": "supplies-total-stock",
              "name": "Valor Total do Estoque Consolidado",
              "weight_pct": 15,
              "goal_2026": "R$ 13.500.000,00",
              "strategic_description": "Estoque como capital parado."
            },
            {
              "id": "supplies-purchase-savings",
              "name": "Economia em Negociações de Compras",
              "weight_pct": 15,
              "goal_2026": "R$ 20.000/mês",
              "strategic_description": "Eficiência em negociações e renegociações com fornecedores."
            }
          ]
        },
        {
          "department_id": "engineering",
          "department_name": "Engenharia",
          "short_name": "ENG",
          "department_weight_pct": 10,
          "strategic_summary": "Mede entrega no prazo e geração de valor via inovação e digitalização.",
          "indicators": [
            {
              "id": "engineering-projects-on-time",
              "name": "% de Projetos Concluídos no Prazo",
              "weight_pct": 60,
              "goal_2026": "95%",
              "strategic_description": "Compromisso com entregas e gestão eficiente de escopo."
            },
            {
              "id": "engineering-transforma-plus",
              "name": "Ganhos Financeiros do TRANSFORMA+ DELPI",
              "weight_pct": 40,
              "goal_2026": "R$ 15.000/mês",
              "strategic_description": "Valor gerado por inovações e digitalização via TRANSFORMA+."
            }
          ]
        }
      ]
    }'::jsonb,
    TRUE,
    NULL,
    NULL
)
ON CONFLICT (setting_key)
DO UPDATE SET
    setting_group = EXCLUDED.setting_group,
    payload_json = EXCLUDED.payload_json,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

COMMIT;