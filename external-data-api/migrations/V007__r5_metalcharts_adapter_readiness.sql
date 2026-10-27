-- PROC-0076 R5 — MetalCharts adapter readiness (Free plan).
--
-- Additive only: nothing activated, no right widened, no key shipped.
--
-- Verified MetalCharts contract facts (public docs, 2026-10-27):
--   * Bearer token (mc_live_*); Free = 200 weight/month/account,
--     10 weight/minute/key, 1 key, history limited to 30 days daily;
--     commercial use allowed on every plan; public display requires a
--     visible credit link; operational cache allowed within reasonable
--     bounds; permanent retention is NOT expressly authorized.
--   * GET /v1/prices returns every tracked metal in one call (1 weight);
--     GET /v1/history/{symbol} costs 2 weight.
--   * Copper symbol HG (COMEX futures) quoted USD per pound — verified
--     on the official copper docs page. The other five symbols are NOT
--     verified (needs /v1/instruments with a key), so bindings are
--     seeded INACTIVE with NULL source_series_key — never guessed.
--
-- 1) market_data_sources row 'metalcharts' — INACTIVE. The scope
--    grants only what the documented terms prove: collect, derive and
--    internal_display (internal commercial use; the UI already carries
--    source attribution). ``store_cache_only`` deliberately replaces
--    ``store``: operational TTL caching is permitted while permanent
--    retention is not, so the permanent-observation ingestion gate
--    (collect+store) stays fail-closed for this source.
-- 2) market_data_sources.observation_retention — 'permanent' default
--    for existing sources; 'ttl_cache' for metalcharts so the query
--    layer knows which table family serves its observations.
-- 3) metal_instrument_sources — per-instrument source bindings; a
--    second provider never overwrites the canonical instrument→source
--    link (no source mixing inside a series). All rows INACTIVE until
--    S1 homologation verifies symbols/units with a real key.
-- 4) metal_quote_cache — operational TTL cache; ``expires_at`` is NOT
--    NULL so the no-permanent-retention policy is structural, not a
--    convention.
-- 5) source_api_call_ledger — per-call weight accounting enforcing the
--    monthly + per-minute allowance server-side.

ALTER TABLE external_data.market_data_sources
    ADD COLUMN IF NOT EXISTS observation_retention TEXT NOT NULL
        DEFAULT 'permanent';

ALTER TABLE external_data.market_data_sources
    DROP CONSTRAINT IF EXISTS market_data_sources_retention_check;
ALTER TABLE external_data.market_data_sources
    ADD CONSTRAINT market_data_sources_retention_check
    CHECK (observation_retention IN ('permanent', 'ttl_cache'));

INSERT INTO external_data.market_data_sources
    (source_id, provider_id, source_kind, attribution, license_reference,
     license_reviewed_at, allowed_use_scope, active,
     observation_retention)
VALUES
    ('metalcharts', 'metalcharts', 'api',
     'MetalCharts — https://metalcharts.org',
     'MetalCharts API Terms — https://metalcharts.org/api-terms',
     NULL,
     'collect;derive;internal_display;store_cache_only;no_redistribute',
     false,
     'ttl_cache')
ON CONFLICT (source_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS external_data.metal_instrument_sources (
    binding_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_id       INTEGER NOT NULL REFERENCES external_data.metal_instruments (instrument_id) ON DELETE RESTRICT,
    source_id           TEXT NOT NULL REFERENCES external_data.market_data_sources (source_id) ON DELETE RESTRICT,
    -- Upstream symbol verified via /v1/instruments; NULL until S1
    -- homologation with a real key — never guessed.
    source_series_key   TEXT,
    granularity         TEXT NOT NULL CHECK (granularity IN ('day', 'week', 'month', 'year')),
    quotation_basis     TEXT NOT NULL,
    native_currency     TEXT NOT NULL CHECK (char_length(native_currency) = 3),
    unit_code           TEXT,
    -- Lower priority wins when several active bindings are displayable.
    priority            INTEGER NOT NULL DEFAULT 100,
    active              BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (instrument_id, source_id)
);

INSERT INTO external_data.metal_instrument_sources
    (instrument_id, source_id, source_series_key, granularity,
     quotation_basis, native_currency, unit_code, priority, active)
SELECT i.instrument_id,
       'metalcharts',
       CASE i.instrument_code WHEN 'copper' THEN 'HG' ELSE NULL END,
       'day',
       'daily_close',
       'USD',
       CASE i.instrument_code WHEN 'copper' THEN 'usd_per_pound' ELSE NULL END,
       10,
       false
FROM external_data.metal_instruments i
WHERE i.active
ON CONFLICT (instrument_id, source_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS external_data.metal_quote_cache (
    cache_id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_id         INTEGER NOT NULL REFERENCES external_data.metal_instruments (instrument_id) ON DELETE RESTRICT,
    source_id             TEXT NOT NULL REFERENCES external_data.market_data_sources (source_id) ON DELETE RESTRICT,
    observation_date      DATE NOT NULL,
    observation_timestamp TIMESTAMPTZ,
    native_price          NUMERIC(20, 6) NOT NULL CHECK (native_price > 0),
    native_currency       TEXT NOT NULL,
    unit_code             TEXT NOT NULL,
    quote_basis           TEXT NOT NULL,
    quality_status        TEXT NOT NULL DEFAULT 'validated',
    source_record_key     TEXT,
    retrieved_at          TIMESTAMPTZ NOT NULL,
    -- Retention guard: every cached row must expire — no permanent
    -- retention for sources without a 'store' grant.
    expires_at            TIMESTAMPTZ NOT NULL,
    UNIQUE (instrument_id, observation_date, source_id)
);

CREATE INDEX IF NOT EXISTS metal_quote_cache_expiry_idx
    ON external_data.metal_quote_cache (expires_at);

CREATE INDEX IF NOT EXISTS metal_quote_cache_instrument_date_idx
    ON external_data.metal_quote_cache (instrument_id, observation_date DESC);

CREATE TABLE IF NOT EXISTS external_data.source_api_call_ledger (
    call_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_id      TEXT NOT NULL REFERENCES external_data.market_data_sources (source_id) ON DELETE RESTRICT,
    endpoint       TEXT NOT NULL,
    params_hash    TEXT NOT NULL,
    weight         INTEGER NOT NULL CHECK (weight > 0),
    http_status    INTEGER,
    called_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Minute bucket materialised by the writer — date_trunc() on
    -- timestamptz is STABLE, not IMMUTABLE, so it cannot live in an
    -- index expression.
    called_minute  TIMESTAMPTZ NOT NULL,
    correlation_id TEXT
);

-- Same upstream request inside one minute counts once — a retry or a
-- racing consumer can never double-spend the allowance.
CREATE UNIQUE INDEX IF NOT EXISTS source_api_call_ledger_minute_uq
    ON external_data.source_api_call_ledger
        (source_id, endpoint, params_hash, called_minute);

CREATE INDEX IF NOT EXISTS source_api_call_ledger_window_idx
    ON external_data.source_api_call_ledger (source_id, called_at);
