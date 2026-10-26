-- PROC-0076 P0 — catalog seed: licensed sources + approved instruments.
--
-- License evidence reviewed 2026-10-26:
--   * BCB PTAX — Portal de Dados Abertos do Banco Central do Brasil,
--     dataset "Dólar comercial (venda e compra) - cotações diárias",
--     license: Open Data Commons Open Database License (ODbL), marked
--     [[Open Data]] in the official catalog. Public OData API intended
--     for automated access. Attribution to Banco Central do Brasil is
--     required and shipped in every payload that surfaces this data.
--   * World Bank Commodity Markets "Pink Sheet" — World Bank datasets
--     default license is Creative Commons Attribution 4.0 (CC BY 4.0)
--     per the official Data Access and Licensing page; allows copy,
--     modification and distribution for any purpose with attribution.
--
-- Unlicensed sources (LME, Shockmetais, or any page without documented
-- usage rights) are NOT seeded — there is nothing to activate.

INSERT INTO external_data.market_data_sources
    (source_id, provider_id, source_kind, attribution, license_reference,
     license_reviewed_at, allowed_use_scope, active)
VALUES
    ('bcb-ptax', 'bcb-ptax', 'api',
     'Banco Central do Brasil — PTAX (dados abertos)',
     'ODbL-1.0 — https://dadosabertos.bcb.gov.br/dataset/dolar-americano-usd-todos-os-boletins-diarios',
     DATE '2026-10-26',
     'collect;store;derive;internal_display',
     true),
    ('world-bank-pink-sheet', 'world-bank-pink-sheet', 'file',
     'World Bank — Commodity Markets "Pink Sheet" (monthly prices)',
     'CC BY 4.0 — https://datacatalog.worldbank.org/public-licenses',
     DATE '2026-10-26',
     'collect;store;derive;internal_display',
     true);

-- Monthly series from the World Bank "Pink Sheet" monthly workbook.
-- quotation_basis 'monthly_average' — the workbook publishes the monthly
-- average quotation per commodity, nominal USD per metric ton.
-- ``source_series_key`` is the workbook column name on "Monthly Prices".
INSERT INTO external_data.metal_instruments
    (instrument_code, metal_code, label, market, quotation_basis,
     native_currency, unit_code, unit_label, source_id, source_series_key,
     granularity, active)
VALUES
    ('copper',    'copper',    'Cobre',    'world_bank_pink_sheet', 'monthly_average', 'USD', 'metric_ton', 'USD/metric ton', 'world-bank-pink-sheet', 'Copper',    'month', true),
    ('aluminum',  'aluminum',  'Alumínio', 'world_bank_pink_sheet', 'monthly_average', 'USD', 'metric_ton', 'USD/metric ton', 'world-bank-pink-sheet', 'Aluminum',  'month', true),
    ('zinc',      'zinc',      'Zinco',    'world_bank_pink_sheet', 'monthly_average', 'USD', 'metric_ton', 'USD/metric ton', 'world-bank-pink-sheet', 'Zinc',      'month', true),
    ('nickel',    'nickel',    'Níquel',   'world_bank_pink_sheet', 'monthly_average', 'USD', 'metric_ton', 'USD/metric ton', 'world-bank-pink-sheet', 'Nickel',    'month', true),
    ('lead',      'lead',      'Chumbo',   'world_bank_pink_sheet', 'monthly_average', 'USD', 'metric_ton', 'USD/metric ton', 'world-bank-pink-sheet', 'Lead',      'month', true),
    ('tin',       'tin',       'Estanho',  'world_bank_pink_sheet', 'monthly_average', 'USD', 'metric_ton', 'USD/metric ton', 'world-bank-pink-sheet', 'Tin',       'month', true);
