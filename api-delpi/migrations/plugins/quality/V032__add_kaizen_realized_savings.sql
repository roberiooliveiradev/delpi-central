-- F5: resultado real vs. estimado — economia efetivamente realizada.
-- `daily_savings`/`annual_savings` (V027) permanecem como estimativa calculada;
-- estes campos guardam o valor medido após a implantação (efetividade real).

ALTER TABLE quality.kaizens
    ADD COLUMN IF NOT EXISTS realized_daily_savings NUMERIC(14, 2),
    ADD COLUMN IF NOT EXISTS realized_annual_savings NUMERIC(14, 2);
