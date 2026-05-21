BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.calculation_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    competence VARCHAR(7) NOT NULL,
    start_date VARCHAR(10) NOT NULL,
    end_date VARCHAR(10) NOT NULL,

    scope_branch VARCHAR(20) NOT NULL DEFAULT '',
    scope_department_id VARCHAR(150) NOT NULL DEFAULT '',

    schema_version SMALLINT NOT NULL DEFAULT 1,

    departments_catalog JSONB NOT NULL,
    indicators_catalog JSONB NOT NULL,
    goals_by_department JSONB NOT NULL DEFAULT '{}'::jsonb,
    measurements JSONB NOT NULL,
    measurement_errors JSONB NOT NULL DEFAULT '[]'::jsonb,

    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_si_calculation_snapshots_scope
        UNIQUE (competence, scope_branch, scope_department_id)
);

CREATE INDEX IF NOT EXISTS idx_si_calculation_snapshots_scope_competence
    ON strategic_indicators.calculation_snapshots (
        scope_branch,
        scope_department_id,
        competence DESC
    );

CREATE INDEX IF NOT EXISTS idx_si_calculation_snapshots_computed_at
    ON strategic_indicators.calculation_snapshots (computed_at DESC);

COMMENT ON TABLE strategic_indicators.calculation_snapshots IS
'Insumos materializados usados no cálculo do SI (catálogo resolvido, metas e medições brutas) por competência/escopo. Atualizado pelo job periódico (padrão 5 min).';

COMMENT ON COLUMN strategic_indicators.calculation_snapshots.departments_catalog IS
'Departamentos ativos e pesos no momento do snapshot.';

COMMENT ON COLUMN strategic_indicators.calculation_snapshots.indicators_catalog IS
'Indicadores com metas resolvidas para a competência.';

COMMENT ON COLUMN strategic_indicators.calculation_snapshots.measurements IS
'Valores realizados coletados das fontes externas (TOTVS, Sheets, RH).';

COMMIT;
