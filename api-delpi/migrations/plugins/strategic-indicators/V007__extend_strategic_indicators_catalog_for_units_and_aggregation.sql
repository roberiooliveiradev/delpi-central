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
    'indicators.catalog',
    'indicators',
    '{
      "items": [
        {
          "department_id": "financial",
          "department_name": "Financeiro",
          "short_name": "FIN",
          "department_weight_pct": 15,
          "aggregation_mode": "average_of_units",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede geração de resultado operacional, eficiência estrutural e fluxo de caixa.",
          "indicators": [
            {
              "id": "financial-ebitda",
              "name": "EBITDA / Receita Operacional",
              "weight_pct": 40,
              "goal_2026": "13,0%",
              "strategic_description": "Mede a capacidade de geração de resultado operacional.",
              "scope_type": "per_unit"
            },
            {
              "id": "financial-fixed-costs",
              "name": "% Custos Fixos / Receita Operacional",
              "weight_pct": 30,
              "goal_2026": "14,0%",
              "strategic_description": "Indica eficiência e estrutura enxuta.",
              "scope_type": "per_unit"
            },
            {
              "id": "financial-pmr",
              "name": "Prazo Médio de Recebimento (PMR)",
              "weight_pct": 30,
              "goal_2026": "39 dias",
              "strategic_description": "Indica eficiência de recebimentos e fluxo de caixa.",
              "scope_type": "per_unit"
            }
          ]
        },
        {
          "department_id": "hr",
          "department_name": "RH",
          "short_name": "RH",
          "department_weight_pct": 15,
          "aggregation_mode": "average_of_units",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede engajamento, retenção, desenvolvimento individual e capacitação contínua.",
          "indicators": [
            {
              "id": "hr-absenteeism",
              "name": "Absenteísmo",
              "weight_pct": 20,
              "goal_2026": "2,0%",
              "strategic_description": "Mede engajamento e bem-estar.",
              "scope_type": "per_unit"
            },
            {
              "id": "hr-turnover",
              "name": "Turnover (Rotatividade)",
              "weight_pct": 20,
              "goal_2026": "1,5% ao mês",
              "strategic_description": "Mede retenção e estabilidade.",
              "scope_type": "per_unit"
            },
            {
              "id": "hr-satisfaction",
              "name": "Satisfação Interna (Clima/Engajamento)",
              "weight_pct": 20,
              "goal_2026": "85% de satisfação",
              "strategic_description": "Reputação interna da cultura.",
              "scope_type": "per_unit"
            },
            {
              "id": "hr-pdi",
              "name": "% de PDIs Ativos",
              "weight_pct": 20,
              "goal_2026": "100%",
              "strategic_description": "Estruturação de desenvolvimento individual.",
              "scope_type": "per_unit"
            },
            {
              "id": "hr-training",
              "name": "Horas de Treinamento/Colaborador/mês",
              "weight_pct": 20,
              "goal_2026": "2 horas/mês",
              "strategic_description": "Investimento em formação e capacitação.",
              "scope_type": "per_unit"
            }
          ]
        },
        {
          "department_id": "commercial",
          "department_name": "Comercial",
          "short_name": "COM",
          "department_weight_pct": 17,
          "aggregation_mode": "mixed_scope",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede receita, conversão de negócios e expansão da base de clientes.",
          "indicators": [
            {
              "id": "commercial-rol-matrix",
              "name": "ROL Matriz / Meta",
              "weight_pct": 25,
              "goal_2026": "100%",
              "strategic_description": "Atingimento da receita da unidade matriz.",
              "scope_type": "matrix_only"
            },
            {
              "id": "commercial-rol-branch",
              "name": "ROL Filial / Meta",
              "weight_pct": 25,
              "goal_2026": "100%",
              "strategic_description": "Atingimento da receita da unidade filial.",
              "scope_type": "branch_only"
            },
            {
              "id": "commercial-closing-rate",
              "name": "Taxa de Fechamento de Negócios",
              "weight_pct": 20,
              "goal_2026": "30%",
              "strategic_description": "Conversão de propostas em vendas.",
              "scope_type": "consolidated"
            },
            {
              "id": "commercial-new-clients",
              "name": "Número de Novos Clientes (média mensal)",
              "weight_pct": 15,
              "goal_2026": "10 novos/mês",
              "strategic_description": "Capacidade de abertura de mercado.",
              "scope_type": "consolidated"
            },
            {
              "id": "commercial-new-rol",
              "name": "% ROL de Novos Clientes",
              "weight_pct": 15,
              "goal_2026": "12%",
              "strategic_description": "Participação dos novos no total da receita.",
              "scope_type": "consolidated"
            }
          ]
        },
        {
          "department_id": "production",
          "department_name": "Produção",
          "short_name": "PRD",
          "department_weight_pct": 17,
          "aggregation_mode": "average_of_units",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede eficiência produtiva, uso dos ativos e cumprimento do prazo ao cliente.",
          "indicators": [
            {
              "id": "production-direct-labor",
              "name": "Custo Mão de Obra Direta / ROL",
              "weight_pct": 25,
              "goal_2026": "10,0%",
              "strategic_description": "Eficiência da mão de obra direta.",
              "scope_type": "per_unit"
            },
            {
              "id": "production-costs",
              "name": "Custos de Produção / ROL",
              "weight_pct": 20,
              "goal_2026": "32,0%",
              "strategic_description": "Controle de desperdícios e produtividade.",
              "scope_type": "per_unit"
            },
            {
              "id": "production-depreciation",
              "name": "Depreciação / ROL",
              "weight_pct": 10,
              "goal_2026": "1,5%",
              "strategic_description": "Uso racional da capacidade instalada.",
              "scope_type": "per_unit"
            },
            {
              "id": "production-oee",
              "name": "OEE (Eficiência Global dos Equip.)",
              "weight_pct": 20,
              "goal_2026": "70%",
              "strategic_description": "Utilização real dos ativos produtivos.",
              "scope_type": "per_unit"
            },
            {
              "id": "production-otd",
              "name": "OTD (Entrega no Prazo)",
              "weight_pct": 25,
              "goal_2026": "92%",
              "strategic_description": "Cumprimento do prazo prometido ao cliente.",
              "scope_type": "per_unit"
            }
          ]
        },
        {
          "department_id": "quality",
          "department_name": "Qualidade",
          "short_name": "QLD",
          "department_weight_pct": 14,
          "aggregation_mode": "average_of_units",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede falhas internas e externas, disciplina operacional e ganhos com melhoria contínua.",
          "indicators": [
            {
              "id": "quality-ppm-internal",
              "name": "PPM Interno",
              "weight_pct": 20,
              "goal_2026": "1.400 PPM",
              "strategic_description": "Indicador de falhas detectadas internamente.",
              "scope_type": "per_unit"
            },
            {
              "id": "quality-ppm-external",
              "name": "PPM Externo",
              "weight_pct": 30,
              "goal_2026": "1.100 PPM",
              "strategic_description": "Indicador de falhas detectadas pelo cliente.",
              "scope_type": "per_unit"
            },
            {
              "id": "quality-kaizen-ideas",
              "name": "Ideias Aprovadas para Kaizen/mês",
              "weight_pct": 15,
              "goal_2026": "8 ideias/mês",
              "strategic_description": "Cultura de melhoria e participação.",
              "scope_type": "per_unit"
            },
            {
              "id": "quality-audit-5s",
              "name": "Nota Auditoria 5S",
              "weight_pct": 15,
              "goal_2026": "80%",
              "strategic_description": "Padronização, organização e disciplina.",
              "scope_type": "per_unit"
            },
            {
              "id": "quality-kaizen-financial",
              "name": "Ganhos Financeiros Kaizen/mês",
              "weight_pct": 20,
              "goal_2026": "R$ 4.500 (1º S), R$ 9.000 (2º S)",
              "strategic_description": "Impacto financeiro direto das melhorias Kaizen.",
              "scope_type": "per_unit"
            }
          ]
        },
        {
          "department_id": "supplies",
          "department_name": "Suprimentos",
          "short_name": "SUP",
          "department_weight_pct": 12,
          "aggregation_mode": "consolidated",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede eficiência em compras, estoque e negociações com fornecedores.",
          "indicators": [
            {
              "id": "supplies-cpv",
              "name": "CPV Consolidado (matriz e filial)",
              "weight_pct": 30,
              "goal_2026": "50,5%",
              "strategic_description": "Eficiência nas compras totais.",
              "scope_type": "consolidated"
            },
            {
              "id": "supplies-otd-purchases",
              "name": "OTD Consolidado de Compras",
              "weight_pct": 20,
              "goal_2026": "92%",
              "strategic_description": "Entregas dentro do prazo pelos fornecedores.",
              "scope_type": "consolidated"
            },
            {
              "id": "supplies-stock-turnover",
              "name": "Giro de Estoque Consolidado",
              "weight_pct": 20,
              "goal_2026": "1,95 mês",
              "strategic_description": "Rotatividade do estoque total.",
              "scope_type": "consolidated"
            },
            {
              "id": "supplies-total-stock",
              "name": "Valor Total do Estoque Consolidado",
              "weight_pct": 15,
              "goal_2026": "R$ 13.500.000,00",
              "strategic_description": "Estoque como capital parado.",
              "scope_type": "consolidated"
            },
            {
              "id": "supplies-purchase-savings",
              "name": "Economia em Negociações de Compras",
              "weight_pct": 15,
              "goal_2026": "R$ 20.000/mês",
              "strategic_description": "Eficiência em negociações e renegociações com fornecedores.",
              "scope_type": "consolidated"
            }
          ]
        },
        {
          "department_id": "engineering",
          "department_name": "Engenharia",
          "short_name": "ENG",
          "department_weight_pct": 10,
          "aggregation_mode": "average_of_units",
          "units": [
            { "unit_id": "matrix", "unit_name": "Matriz" },
            { "unit_id": "branch", "unit_name": "Filial" }
          ],
          "strategic_summary": "Mede entrega no prazo e geração de valor via inovação e digitalização.",
          "indicators": [
            {
              "id": "engineering-projects-on-time",
              "name": "% de Projetos Concluídos no Prazo",
              "weight_pct": 60,
              "goal_2026": "95%",
              "strategic_description": "Compromisso com entregas e gestão eficiente de escopo.",
              "scope_type": "per_unit"
            },
            {
              "id": "engineering-transforma-plus",
              "name": "Ganhos Financeiros do TRANSFORMA+ DELPI",
              "weight_pct": 40,
              "goal_2026": "R$ 15.000/mês",
              "strategic_description": "Valor gerado por inovações e digitalização via TRANSFORMA+.",
              "scope_type": "per_unit"
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