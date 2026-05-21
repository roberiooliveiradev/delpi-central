BEGIN;

ALTER TABLE strategic_indicators.calculation_snapshots
    ADD COLUMN IF NOT EXISTS catalog_inputs_hash VARCHAR(64) NULL;

ALTER TABLE strategic_indicators.period_scores
    ADD COLUMN IF NOT EXISTS catalog_inputs_hash VARCHAR(64) NULL;

COMMENT ON COLUMN strategic_indicators.calculation_snapshots.catalog_inputs_hash IS
'Fingerprint SHA-256 (truncado) do catálogo+metas usados no cálculo; útil para detectar snapshot desatualizado.';

COMMENT ON COLUMN strategic_indicators.period_scores.catalog_inputs_hash IS
'Fingerprint do catálogo+metas no momento do cálculo persistido.';

COMMIT;
