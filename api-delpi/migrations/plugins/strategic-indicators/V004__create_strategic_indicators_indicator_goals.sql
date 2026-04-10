BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.indicator_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    indicator_id VARCHAR(120) NOT NULL,
    goal_year INT NOT NULL,

    goal_label VARCHAR(255) NOT NULL,
    goal_value NUMERIC(18,4) NOT NULL,
    goal_periodicity VARCHAR(30) NOT NULL,

    version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    valid_from DATE NULL,
    valid_to DATE NULL,

    notes TEXT NULL,

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,
    updated_by_user_id UUID NULL,
    updated_by_email VARCHAR(255) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_si_indicator_goals_year
        CHECK (goal_year >= 2020 AND goal_year <= 2100),

    CONSTRAINT ck_si_indicator_goals_goal_value_non_negative
        CHECK (goal_value >= 0),

    CONSTRAINT ck_si_indicator_goals_version_positive
        CHECK (version >= 1),

    CONSTRAINT ck_si_indicator_goals_periodicity
        CHECK (
            goal_periodicity IN (
                'monthly',
                'annual',
                'quarterly',
                'weekly'
            )
        ),

    CONSTRAINT ck_si_indicator_goals_valid_range
        CHECK (
            valid_from IS NULL
            OR valid_to IS NULL
            OR valid_from <= valid_to
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_si_indicator_goals_indicator_year_version
    ON strategic_indicators.indicator_goals (indicator_id, goal_year, version);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_indicator_year
    ON strategic_indicators.indicator_goals (indicator_id, goal_year);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_indicator_active
    ON strategic_indicators.indicator_goals (indicator_id, is_active);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_validity
    ON strategic_indicators.indicator_goals (valid_from, valid_to);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_created_at
    ON strategic_indicators.indicator_goals (created_at DESC);

COMMENT ON TABLE strategic_indicators.indicator_goals IS
'Tabela de metas analíticas versionadas por indicador. Permite múltiplas metas por ano, histórico de versões, ativação controlada e vigência temporal.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.indicator_id IS
'ID lógico do indicador conforme definido no catálogo estrutural em indicators.catalog.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.goal_year IS
'Ano-base da meta analítica do indicador. Exemplo: 2026.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.version IS
'Versão incremental da meta para o mesmo indicador e ano.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.is_active IS
'Define se esta versão da meta está ativa para resolução oficial do cálculo.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.valid_from IS
'Data inicial opcional de vigência da meta dentro do ano.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.valid_to IS
'Data final opcional de vigência da meta dentro do ano.';

COMMIT;