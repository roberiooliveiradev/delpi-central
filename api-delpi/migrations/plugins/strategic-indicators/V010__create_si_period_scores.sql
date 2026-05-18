BEGIN;

CREATE TABLE IF NOT EXISTS strategic_indicators.period_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    competence VARCHAR(7) NOT NULL,
    start_date VARCHAR(10) NOT NULL,
    end_date VARCHAR(10) NOT NULL,

    scope_branch VARCHAR(20) NOT NULL DEFAULT '',
    scope_department_id VARCHAR(150) NOT NULL DEFAULT '',

    igd NUMERIC(10, 4) NOT NULL,
    igd_exact NUMERIC(12, 6) NOT NULL,
    classification VARCHAR(50) NOT NULL,

    calculated_departments JSONB NOT NULL,
    calculated_indicators JSONB NOT NULL,
    measurement_errors JSONB NOT NULL DEFAULT '[]'::jsonb,

    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_si_period_scores_scope
        UNIQUE (competence, scope_branch, scope_department_id)
);

CREATE INDEX IF NOT EXISTS idx_si_period_scores_scope_competence
    ON strategic_indicators.period_scores (
        scope_branch,
        scope_department_id,
        competence DESC
    );

COMMENT ON TABLE strategic_indicators.period_scores IS
'Scores pré-calculados por competência para acelerar trends/presentation (evita reconsultar TOTVS/Sheets).';

COMMENT ON COLUMN strategic_indicators.period_scores.scope_branch IS
'Filial da consulta; vazio = consolidado.';

COMMENT ON COLUMN strategic_indicators.period_scores.scope_department_id IS
'Departamento filtrado; vazio = todos os departamentos (visão executiva).';

COMMIT;
