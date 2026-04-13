BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.indicator_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    indicator_id VARCHAR(150) NOT NULL,
    goal_year INT NOT NULL,

    goal_label VARCHAR(255) NOT NULL,
    goal_value NUMERIC(18,4) NOT NULL,
    goal_periodicity VARCHAR(30) NOT NULL,
    goal_mode VARCHAR(30) NOT NULL DEFAULT 'standard',

    version INT NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    valid_from DATE NULL,
    valid_to DATE NULL,
    notes TEXT NULL,

    copied_from_goal_id UUID NULL,
    copied_from_year INT NULL,

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,
    updated_by_user_id UUID NULL,
    updated_by_email VARCHAR(255) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_si_indicator_goals_indicator_id
        FOREIGN KEY (indicator_id)
        REFERENCES strategic_indicators.department_indicators (indicator_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT fk_si_indicator_goals_copied_from_goal_id
        FOREIGN KEY (copied_from_goal_id)
        REFERENCES strategic_indicators.indicator_goals (id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT ck_si_indicator_goals_goal_year
        CHECK (goal_year >= 2000 AND goal_year <= 2100),

    CONSTRAINT ck_si_indicator_goals_goal_value
        CHECK (goal_value >= 0),

    CONSTRAINT ck_si_indicator_goals_version
        CHECK (version >= 1),

    CONSTRAINT ck_si_indicator_goals_goal_periodicity
        CHECK (
            goal_periodicity IN (
                'monthly',
                'annual',
                'quarterly',
                'weekly'
            )
        ),

    CONSTRAINT ck_si_indicator_goals_goal_mode
        CHECK (
            goal_mode IN (
                'standard',
                'monthly_curve'
            )
        ),

    CONSTRAINT ck_si_indicator_goals_valid_range
        CHECK (
            valid_from IS NULL
            OR valid_to IS NULL
            OR valid_from <= valid_to
        )
);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_indicator_id
    ON strategic_indicators.indicator_goals (indicator_id);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_year
    ON strategic_indicators.indicator_goals (goal_year);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_active
    ON strategic_indicators.indicator_goals (is_active);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_indicator_year
    ON strategic_indicators.indicator_goals (indicator_id, goal_year);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_indicator_year_version
    ON strategic_indicators.indicator_goals (indicator_id, goal_year, version DESC);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goals_goal_mode
    ON strategic_indicators.indicator_goals (goal_mode);

CREATE TABLE IF NOT EXISTS strategic_indicators.indicator_goal_monthly_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    indicator_goal_id UUID NOT NULL,
    month_number SMALLINT NOT NULL,
    target_value NUMERIC(18,4) NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_si_indicator_goal_monthly_targets_goal_id
        FOREIGN KEY (indicator_goal_id)
        REFERENCES strategic_indicators.indicator_goals (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT uq_si_indicator_goal_monthly_targets_goal_month
        UNIQUE (indicator_goal_id, month_number),

    CONSTRAINT ck_si_indicator_goal_monthly_targets_month
        CHECK (month_number BETWEEN 1 AND 12),

    CONSTRAINT ck_si_indicator_goal_monthly_targets_target_value
        CHECK (target_value >= 0)
);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goal_monthly_targets_goal_id
    ON strategic_indicators.indicator_goal_monthly_targets (indicator_goal_id);

CREATE INDEX IF NOT EXISTS idx_si_indicator_goal_monthly_targets_goal_id_month
    ON strategic_indicators.indicator_goal_monthly_targets (indicator_goal_id, month_number);

COMMENT ON TABLE strategic_indicators.indicator_goals IS
'Tabela de metas analíticas versionadas por indicador e ano. Pode operar em modo escalar padrão ou curva mensal.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.goal_mode IS
'Modo de resolução da meta. standard = valor escalar compatível com periodicidade. monthly_curve = tabela filha com metas mensais por indicador/ano.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.copied_from_goal_id IS
'Meta de origem utilizada em duplicações controladas entre ciclos.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.copied_from_year IS
'Ano de origem utilizado para preencher metas em lote.';

COMMENT ON TABLE strategic_indicators.indicator_goal_monthly_targets IS
'Tabela filha com a curva mensal da meta para indicadores cujo alvo varia ao longo dos meses do ano.';

COMMENT ON COLUMN strategic_indicators.indicator_goal_monthly_targets.month_number IS
'Mês do alvo dentro do ano da meta: 1=jan, 12=dez.';

COMMIT;