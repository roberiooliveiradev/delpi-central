-- D15 — baseline oficial imutável por solicitação UPDATE.
-- Capturado server-side via reader oficial (api-delpi → TOTVS).
-- Não aceitar snapshot arbitrário do browser como prova.

ALTER TABLE engineering.product_registration_requests
    ADD COLUMN IF NOT EXISTS official_baseline JSONB;

COMMENT ON COLUMN engineering.product_registration_requests.official_baseline IS
    'D15: snapshot SB1+SA5 capturado pela Engineering API na formalização UPDATE; imutável após insert.';
