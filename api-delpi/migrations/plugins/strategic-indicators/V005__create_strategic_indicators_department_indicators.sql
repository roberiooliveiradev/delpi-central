BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.department_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    indicator_id VARCHAR(150) NOT NULL,
    department_id VARCHAR(100) NOT NULL,

    indicator_name VARCHAR(255) NOT NULL,
    weight_pct NUMERIC(8,2) NOT NULL DEFAULT 0,

    scope_type VARCHAR(40) NOT NULL DEFAULT 'consolidated',
    performance_direction VARCHAR(30) NOT NULL DEFAULT 'higher_is_better',
    strategic_description TEXT NOT NULL DEFAULT '',
    source_key VARCHAR(150) NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INT NOT NULL DEFAULT 0,

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,
    updated_by_user_id UUID NULL,
    updated_by_email VARCHAR(255) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_strategic_indicators_department_indicators_indicator_id
        UNIQUE (indicator_id),

    CONSTRAINT fk_si_department_indicators_department_id
        FOREIGN KEY (department_id)
        REFERENCES strategic_indicators.departments (department_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT ck_si_department_indicators_weight_pct
        CHECK (weight_pct >= 0 AND weight_pct <= 100),

    CONSTRAINT ck_si_department_indicators_scope_type
        CHECK (
            scope_type IN (
                'consolidated',
                'per_unit'
            )
        ),

    CONSTRAINT ck_si_department_indicators_performance_direction
        CHECK (
            performance_direction IN (
                'higher_is_better',
                'lower_is_better'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_si_department_indicators_department_id
    ON strategic_indicators.department_indicators (department_id);

CREATE INDEX IF NOT EXISTS idx_si_department_indicators_active
    ON strategic_indicators.department_indicators (is_active);

CREATE INDEX IF NOT EXISTS idx_si_department_indicators_display_order
    ON strategic_indicators.department_indicators (display_order);

CREATE INDEX IF NOT EXISTS idx_si_department_indicators_source_key
    ON strategic_indicators.department_indicators (source_key);

CREATE INDEX IF NOT EXISTS idx_si_department_indicators_performance_direction
    ON strategic_indicators.department_indicators (performance_direction);

COMMENT ON TABLE strategic_indicators.department_indicators IS
'Catálogo estrutural dos indicadores por departamento.';

COMMENT ON COLUMN strategic_indicators.department_indicators.indicator_id IS
'Chave lógica estável do indicador. Ex.: financial-ebitda, hr-turnover.';

COMMENT ON COLUMN strategic_indicators.department_indicators.department_id IS
'Departamento ao qual o indicador pertence.';

COMMENT ON COLUMN strategic_indicators.department_indicators.weight_pct IS
'Peso interno do indicador dentro do departamento.';

COMMENT ON COLUMN strategic_indicators.department_indicators.scope_type IS
'Escopo do indicador: consolidated ou per_unit.';

COMMENT ON COLUMN strategic_indicators.department_indicators.performance_direction IS
'Direção de performance do indicador. higher_is_better = quanto maior, melhor. lower_is_better = quanto menor, melhor.';

COMMENT ON COLUMN strategic_indicators.department_indicators.source_key IS
'Chave de origem usada pela camada de medições reais.';

COMMIT;