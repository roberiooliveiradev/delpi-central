BEGIN;

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
                'governance',
                'indicators'
            )
        ),

    CONSTRAINT ck_strategic_indicators_module_settings_payload_is_object
        CHECK (jsonb_typeof(payload_json) = 'object')
);

CREATE INDEX IF NOT EXISTS idx_si_module_settings_group
    ON strategic_indicators.module_settings (setting_group);

CREATE INDEX IF NOT EXISTS idx_si_module_settings_active
    ON strategic_indicators.module_settings (is_active);

CREATE INDEX IF NOT EXISTS idx_si_module_settings_updated_at
    ON strategic_indicators.module_settings (updated_at DESC);

COMMENT ON TABLE strategic_indicators.module_settings IS
'Tabela base de configurações persistidas do plugin Strategic Indicators. Armazena pesos, metas executivas resumidas, parâmetros, governança e catálogo estrutural de departamentos e indicadores em blocos JSON versionáveis por chave lógica.';

COMMENT ON COLUMN strategic_indicators.module_settings.setting_key IS
'Chave lógica única da configuração. Exemplos: weights.departments, goals.summary, parameters.global, governance.notes, indicators.catalog.';

COMMENT ON COLUMN strategic_indicators.module_settings.setting_group IS
'Grupo funcional da configuração: weights, goals, parameters, governance ou indicators.';

COMMENT ON COLUMN strategic_indicators.module_settings.payload_json IS
'Payload JSONB da configuração. No caso de indicators.catalog, armazena apenas a estrutura do catálogo e não mais as metas analíticas por ano.';

COMMENT ON COLUMN strategic_indicators.module_settings.is_active IS
'Define se o registro está ativo para leitura pelo módulo.';

COMMENT ON COLUMN strategic_indicators.module_settings.updated_by_user_id IS
'UUID do usuário que realizou a última atualização administrativa.';

COMMENT ON COLUMN strategic_indicators.module_settings.updated_by_email IS
'E-mail do usuário que realizou a última atualização administrativa.';

COMMIT;