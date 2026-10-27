-- PROC-0076 R5.S1 — MetalCharts verified bindings (homologated 2026-10-27).
--
-- Real-API homologation results (sanitized; no key material):
--   * /v1/prices/ 200 → 13 symbols; metals: HG USD/lb COMEX,
--     ALI USD/mt LME, NI USD/mt LME, ZN USD/mt SPOT, PB USD/mt SPOT.
--   * /v1/history/{HG,ALI,NI,ZN,PB} 200 → 22 daily bars each for the
--     2026-09-28..2026-10-27 window (Free = 30 days daily).
--   * SN → 400 "Invalid symbol"; tin is NOT covered by this API —
--     the binding stays INACTIVE with NULL source_series_key.
--   * Invalid key → 401 typed; per-minute window confirmed via 429.
--
-- Rights gate honoured: the terms verified in R5 (commercial internal
-- use, derived charts, operational cache within reasonable bounds) map
-- to the recorded scope collect+derive+internal_display+store_cache_only;
-- permanent retention remains ungranted (no ``store`` token),
-- redistribution ungranted (``no_redistribute``). license_reviewed_at
-- stays NULL — activation records verified permissions, not an
-- institutional license review.
--
-- Additive/catalog-update only: no destructive DDL.

-- 1) Activate the MetalCharts source — consulta, cache operacional e
--    exibição interna comprovados pelos termos verificados + respostas
--    reais homologadas. Escopo inalterado.
UPDATE external_data.market_data_sources
SET active = true
WHERE source_id = 'metalcharts'
  AND allowed_use_scope LIKE '%store_cache_only%'
  AND allowed_use_scope NOT LIKE '%;store;%'
  AND allowed_use_scope NOT LIKE 'store;%'
  AND allowed_use_scope <> 'store';

-- 2) Verified bindings — symbol, unit and quotation basis from real
--    responses. Tin remains inactive: SN is not a valid API symbol.
UPDATE external_data.metal_instrument_sources s
SET source_series_key = v.series_key,
    unit_code         = v.unit_code,
    quotation_basis   = v.quotation_basis,
    active            = true
FROM (
    VALUES
        ('copper',   'HG',  'usd_per_pound',      'comex_daily_close'),
        ('aluminum', 'ALI', 'usd_per_metric_ton', 'lme_daily_close'),
        ('nickel',   'NI',  'usd_per_metric_ton', 'lme_daily_close'),
        ('zinc',     'ZN',  'usd_per_metric_ton', 'spot_daily_close'),
        ('lead',     'PB',  'usd_per_metric_ton', 'spot_daily_close')
) AS v(instrument_code, series_key, unit_code, quotation_basis)
JOIN external_data.metal_instruments i
    ON i.instrument_code = v.instrument_code
WHERE s.instrument_id = i.instrument_id
  AND s.source_id = 'metalcharts';
