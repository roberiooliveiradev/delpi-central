BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.indicator_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    indicator_id VARCHAR(150) NOT NULL,
    goal_year INT NOT NULL,

    goal_label VARCHAR(255) NOT NULL,
    goal_value NUMERIC(18,4) NOT NULL,
    goal_periodicity VARCHAR(30) NOT NULL,

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

COMMENT ON TABLE strategic_indicators.indicator_goals IS
'Tabela de metas analíticas versionadas por indicador e ano.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.copied_from_goal_id IS
'Meta de origem utilizada em duplicações controladas entre ciclos.';

COMMENT ON COLUMN strategic_indicators.indicator_goals.copied_from_year IS
'Ano de origem utilizado para preencher metas em lote.';
COMMIT;