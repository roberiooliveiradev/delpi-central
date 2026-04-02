-- ==========================================================
-- Strategic Indicators
-- V002__create_strategic_indicators_module_settings.sql
-- Tabela base de configurações persistidas do módulo
-- ==========================================================

BEGIN;

-- ==========================================================
-- TABELA BASE DE CONFIGURAÇÕES DO MÓDULO
-- ==========================================================
CREATE TABLE IF NOT EXISTS strategic_indicators.module_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    setting_key VARCHAR(100) NOT NULL,
    setting_group VARCHAR(50) NOT NULL,

    payload_json JSONB NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    updated_by_user_id UUID NULL,
    updated_by_email VARCHAR(255) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_strategic_indicators_module_settings_key UNIQUE (setting_key),

    CONSTRAINT ck_strategic_indicators_module_settings_group
        CHECK (
            setting_group IN (
                'weights',
                'goals',
                'parameters',
                'governance'
            )
        ),

    CONSTRAINT ck_strategic_indicators_module_settings_payload_is_object
        CHECK (jsonb_typeof(payload_json) = 'object')
);

-- ==========================================================
-- ÍNDICES
-- ==========================================================
CREATE INDEX IF NOT EXISTS idx_si_module_settings_group
    ON strategic_indicators.module_settings (setting_group);

CREATE INDEX IF NOT EXISTS idx_si_module_settings_active
    ON strategic_indicators.module_settings (is_active);

CREATE INDEX IF NOT EXISTS idx_si_module_settings_updated_at
    ON strategic_indicators.module_settings (updated_at DESC);

-- ==========================================================
-- DOCUMENTAÇÃO
-- ==========================================================
COMMENT ON TABLE strategic_indicators.module_settings IS
'Tabela base de configurações persistidas do plugin Strategic Indicators. Armazena pesos, metas, parâmetros e observações administrativas em blocos JSON versionáveis por chave lógica.';

COMMENT ON COLUMN strategic_indicators.module_settings.setting_key IS
'Chave lógica única da configuração. Exemplos: weights.departments, goals.summary, parameters.global, governance.notes.';

COMMENT ON COLUMN strategic_indicators.module_settings.setting_group IS
'Grupo funcional da configuração: weights, goals, parameters ou governance.';

COMMENT ON COLUMN strategic_indicators.module_settings.payload_json IS
'Payload JSONB da configuração, mantendo flexibilidade para evolução incremental do módulo.';

COMMENT ON COLUMN strategic_indicators.module_settings.is_active IS
'Define se o registro está ativo para leitura pelo módulo.';

COMMENT ON COLUMN strategic_indicators.module_settings.updated_by_user_id IS
'UUID do usuário que realizou a última atualização administrativa.';

COMMENT ON COLUMN strategic_indicators.module_settings.updated_by_email IS
'E-mail do usuário que realizou a última atualização administrativa.';

-- ==========================================================
-- SEED INICIAL
-- ==========================================================
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
          "headline_goal": "PPM Externo 1.100",
          "supporting_focus": "5S em 80% e ganhos Kaizen crescentes."
        },
        {
          "department_id": "supplies",
          "department_name": "Suprimentos",
          "headline_goal": "OTD Compras 92%",
          "supporting_focus": "CPV em 50,5% e estoque consolidado sob controle."
        },
        {
          "department_id": "engineering",
          "department_name": "Engenharia",
          "headline_goal": "Projetos no prazo 95%",
          "supporting_focus": "Ganhos do TRANSFORMA+ em R$ 15.000/mês."
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
        }
      ]
    }'::jsonb,
    TRUE,
    NULL,
    NULL
)
ON CONFLICT (setting_key) DO NOTHING;

COMMIT;