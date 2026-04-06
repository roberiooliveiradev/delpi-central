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
          "supporting_focus": "OTD de compras em 92% e economia em negociações de R$ 20.000/mês."
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
          "key": "index_reference",
          "label": "Referência oficial do índice",
          "value": "IGD/IDD DELPI",
          "observation": "Seed default alinhado ao documento consolidado oficial do IGD e IDD."
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