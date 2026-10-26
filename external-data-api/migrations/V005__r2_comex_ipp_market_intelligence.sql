-- PROC-0076 R2 — Comex Stat (MDIC) + IBGE IPP sources and history.
--
-- Additive only: V001–V004 are untouched and the LME quarantine catalog
-- is preserved. New sources record open-government license evidence and
-- ship ``active = false`` — the feeds stay OFF until operational
-- authorization, and the Comex NCM allowlist is seeded EMPTY because
-- the NCM→product mapping is pending Compras homologation
-- (TO_INVENTORY; ingestion refuses to run without an explicit allowlist).
--
-- License evidence reviewed 2026-10-27:
--   * MDIC Comex Stat — Brazilian federal open data (Decreto
--     nº 8.777/2016, Política de Dados Abertos). Public CSV files at
--     balanca.economia.gov.br published for reuse with attribution.
--   * IBGE SIDRA table 6903 — official IPP publication, open data via
--     the SIDRA API; use permitted with source attribution. Contract
--     validated against servicodados.ibge.gov.br metadata: table 6903
--     (base dez/2018=100), classification 842 (CNAE 2.0), activity
--     46641 "24 METALURGIA", variables 10008 (número-índice) and 1396
--     (M/M-1 %).

INSERT INTO external_data.market_data_sources
    (source_id, provider_id, source_kind, attribution, license_reference,
     license_reviewed_at, allowed_use_scope, active)
VALUES
    ('mdic-comex-stat', 'mdic-comex-stat', 'file',
     'Ministério do Desenvolvimento, Indústria, Comércio e Serviços (MDIC) — Comex Stat, importações por NCM',
     'Política de Dados Abertos (Decreto nº 8.777/2016) — https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta',
     DATE '2026-10-27',
     'collect;store;derive;internal_display',
     false),
    ('ibge-ipp-sidra', 'ibge-ipp-sidra', 'api',
     'IBGE — Índice de Preços ao Produtor (IPP), SIDRA tabela 6903',
     'IBGE SIDRA dados abertos — https://sidra.ibge.gov.br/tabela/6903',
     DATE '2026-10-27',
     'collect;store;derive;internal_display',
     false);

-- Approved NCM allowlist — EMPTY on purpose. An NCM only enters through
-- a later additive migration after Compras homologates the
-- NCM→product mapping; until then the Comex feed refuses to run.
CREATE TABLE external_data.comex_ncm_allowlist (
    ncm_code      TEXT PRIMARY KEY CHECK (ncm_code ~ '^[0-9]{8}$'),
    ncm_version   TEXT NOT NULL,
    description   TEXT NOT NULL,
    family_code   TEXT,
    approved_by   TEXT,
    approved_at   TIMESTAMPTZ,
    active        BOOLEAN NOT NULL DEFAULT true,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Monthly import aggregates per (month, NCM, origin country, UF).
-- ``unit_value_usd_per_t`` is the derived FOB unit value
-- SUM(VL_FOB) / (SUM(KG_LIQUIDO)/1000) — an import-value indicator,
-- never a metal spot quote; NULL when the total weight is zero.
CREATE TABLE external_data.comex_import_monthly_observations (
    observation_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reference_month       DATE NOT NULL,
    ncm_code              TEXT NOT NULL
        REFERENCES external_data.comex_ncm_allowlist (ncm_code)
        ON DELETE RESTRICT,
    ncm_version           TEXT NOT NULL,
    country_code          TEXT NOT NULL,
    state_code            TEXT NOT NULL,
    fob_usd_total         NUMERIC(24, 6) NOT NULL
        CHECK (fob_usd_total >= 0),
    net_weight_kg_total   NUMERIC(24, 6) NOT NULL
        CHECK (net_weight_kg_total >= 0),
    unit_value_usd_per_t  NUMERIC(24, 6)
        CHECK (unit_value_usd_per_t IS NULL OR unit_value_usd_per_t > 0),
    contributing_rows     INTEGER NOT NULL CHECK (contributing_rows >= 0),
    quality_status        TEXT NOT NULL
        CHECK (quality_status IN ('validated', 'invalid_weight')),
    dataset_year          SMALLINT NOT NULL,
    dataset_revision      TEXT,
    source_checksum       TEXT,
    source_id             TEXT NOT NULL
        REFERENCES external_data.market_data_sources (source_id)
        ON DELETE RESTRICT,
    retrieved_at          TIMESTAMPTZ NOT NULL,
    revised_at            TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (reference_month, ncm_code, country_code, state_code,
            dataset_year, source_id)
);

CREATE INDEX comex_import_monthly_ncm_month_idx
    ON external_data.comex_import_monthly_observations
    (ncm_code, reference_month DESC);

-- Canonical, validated SIDRA series (frozen contract — see header).
CREATE TABLE external_data.producer_price_series (
    series_id          TEXT PRIMARY KEY,
    table_code         TEXT NOT NULL,
    classification_code TEXT NOT NULL,
    variable_code      TEXT NOT NULL,
    variable_label     TEXT NOT NULL,
    activity_code      TEXT NOT NULL,
    activity_label     TEXT NOT NULL,
    metric_kind        TEXT NOT NULL CHECK (metric_kind IN (
        'ipp_index', 'ipp_monthly_change_pct',
        'ipp_yoy_change_pct', 'ipp_year_accumulated_pct')),
    unit_code          TEXT NOT NULL,
    unit_label         TEXT NOT NULL,
    base_reference     TEXT,
    source_id          TEXT NOT NULL
        REFERENCES external_data.market_data_sources (source_id)
        ON DELETE RESTRICT,
    active             BOOLEAN NOT NULL DEFAULT true,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO external_data.producer_price_series
    (series_id, table_code, classification_code, variable_code,
     variable_label, activity_code, activity_label, metric_kind,
     unit_code, unit_label, base_reference, source_id, active)
VALUES
    ('ipp-metalurgia-index', '6903', '842', '10008',
     'IPP - Número-índice (dezembro de 2018 = 100)',
     '46641', '24 METALURGIA', 'ipp_index',
     'index', 'número-índice', 'dez/2018=100', 'ibge-ipp-sidra', true),
    ('ipp-metalurgia-mom', '6903', '842', '1396',
     'IPP - Variação mês/mês imediatamente anterior (M/M-1)',
     '46641', '24 METALURGIA', 'ipp_monthly_change_pct',
     'percent', '%', 'dez/2018=100', 'ibge-ipp-sidra', true);

CREATE TABLE external_data.producer_price_index_observations (
    observation_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    series_id       TEXT NOT NULL
        REFERENCES external_data.producer_price_series (series_id)
        ON DELETE RESTRICT,
    reference_month DATE NOT NULL,
    value           NUMERIC(20, 6) NOT NULL,
    source_id       TEXT NOT NULL
        REFERENCES external_data.market_data_sources (source_id)
        ON DELETE RESTRICT,
    source_record_key TEXT,
    published_at    TIMESTAMPTZ,
    retrieved_at    TIMESTAMPTZ NOT NULL,
    revised_at      TIMESTAMPTZ,
    quality_status  TEXT NOT NULL DEFAULT 'validated'
        CHECK (quality_status IN ('validated', 'estimated')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (series_id, reference_month, source_id)
);

CREATE INDEX producer_price_index_series_month_idx
    ON external_data.producer_price_index_observations
    (series_id, reference_month DESC);
