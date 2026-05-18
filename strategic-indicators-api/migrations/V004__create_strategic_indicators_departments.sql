BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    department_id VARCHAR(100) NOT NULL,
    department_name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50) NOT NULL,

    strategic_summary TEXT NOT NULL DEFAULT '',
    headline_goal TEXT NOT NULL DEFAULT '',
    supporting_focus TEXT NOT NULL DEFAULT '',

    weight_pct NUMERIC(8,2) NOT NULL DEFAULT 0,

    aggregation_mode VARCHAR(40) NOT NULL DEFAULT 'consolidated',

    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INT NOT NULL DEFAULT 0,

    created_by_user_id UUID NULL,
    created_by_email VARCHAR(255) NULL,
    updated_by_user_id UUID NULL,
    updated_by_email VARCHAR(255) NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_strategic_indicators_departments_department_id
        UNIQUE (department_id),

    CONSTRAINT ck_strategic_indicators_departments_weight_pct
        CHECK (weight_pct >= 0 AND weight_pct <= 100),

    CONSTRAINT ck_strategic_indicators_departments_aggregation_mode
        CHECK (
            aggregation_mode IN (
                'consolidated',
                'average_of_units'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_si_departments_active
    ON strategic_indicators.departments (is_active);

CREATE INDEX IF NOT EXISTS idx_si_departments_display_order
    ON strategic_indicators.departments (display_order);

CREATE INDEX IF NOT EXISTS idx_si_departments_name
    ON strategic_indicators.departments (department_name);

COMMENT ON TABLE strategic_indicators.departments IS
'Catálogo administrativo principal dos departamentos do Strategic Indicators. Centraliza identidade, governança executiva, peso, status e ordenação.';

COMMENT ON COLUMN strategic_indicators.departments.department_id IS
'Chave lógica estável do departamento. Ex.: financial, hr, production.';

COMMENT ON COLUMN strategic_indicators.departments.department_name IS
'Nome oficial exibido ao usuário.';

COMMENT ON COLUMN strategic_indicators.departments.short_name IS
'Sigla amigável utilizada em interfaces e visões compactas.';

COMMENT ON COLUMN strategic_indicators.departments.strategic_summary IS
'Resumo estratégico do departamento.';

COMMENT ON COLUMN strategic_indicators.departments.headline_goal IS
'Meta executiva principal do departamento.';

COMMENT ON COLUMN strategic_indicators.departments.supporting_focus IS
'Foco complementar de apoio à meta principal.';

COMMENT ON COLUMN strategic_indicators.departments.weight_pct IS
'Peso do departamento no cálculo do IGD.';

COMMENT ON COLUMN strategic_indicators.departments.aggregation_mode IS
'Modo de agregação oficial do departamento: consolidated ou average_of_units.';

COMMENT ON COLUMN strategic_indicators.departments.is_active IS
'Define se o departamento está ativo para leitura e configuração.';

COMMIT;