-- Até 3 versões materializadas por competência/escopo; leitura prioriza versão limpa.

BEGIN;

ALTER TABLE strategic_indicators.period_scores
    ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1;

ALTER TABLE strategic_indicators.period_scores
    ADD COLUMN IF NOT EXISTS is_clean BOOLEAN NOT NULL DEFAULT TRUE;

UPDATE strategic_indicators.period_scores
SET
    is_clean = (
        measurement_errors IS NULL
        OR measurement_errors = '[]'::jsonb
        OR jsonb_array_length(measurement_errors) = 0
    )
WHERE is_clean IS DISTINCT FROM (
    measurement_errors IS NULL
    OR measurement_errors = '[]'::jsonb
    OR jsonb_array_length(measurement_errors) = 0
);

ALTER TABLE strategic_indicators.period_scores
    DROP CONSTRAINT IF EXISTS uq_si_period_scores_scope;

ALTER TABLE strategic_indicators.period_scores
    ADD CONSTRAINT uq_si_period_scores_scope_version
        UNIQUE (competence, scope_branch, scope_department_id, version_number);

CREATE INDEX IF NOT EXISTS idx_si_period_scores_scope_versions
    ON strategic_indicators.period_scores (
        scope_branch,
        scope_department_id,
        competence DESC,
        version_number DESC
    );

COMMENT ON COLUMN strategic_indicators.period_scores.version_number IS
'Versão monotônica por escopo/competência (máx. 3 retidas na aplicação).';

COMMENT ON COLUMN strategic_indicators.period_scores.is_clean IS
'TRUE quando measurement_errors está vazio e a coleta atende política de cache.';

COMMIT;
