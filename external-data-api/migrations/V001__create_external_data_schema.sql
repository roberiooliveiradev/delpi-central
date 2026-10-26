-- PROC-0076 P0 — market data owned by external-data-api.
-- Dedicated schema in postgres-plugins; never touches the supplies schema
-- or any other bounded context. Monetary values are NUMERIC, never float.

CREATE SCHEMA IF NOT EXISTS external_data;

-- Licensed/approved external sources. ``active = false`` disables the feed
-- even when env flags allow it; a catalog row is NOT proof of licensing —
-- the license fields record the documented reference and review date.
CREATE TABLE external_data.market_data_sources (
    source_id            TEXT PRIMARY KEY,
    provider_id          TEXT NOT NULL,
    source_kind          TEXT NOT NULL CHECK (source_kind IN ('api', 'file')),
    attribution          TEXT NOT NULL,
    license_reference    TEXT NOT NULL,
    license_reviewed_at  DATE,
    allowed_use_scope    TEXT NOT NULL,
    active               BOOLEAN NOT NULL DEFAULT false,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Metal instruments: same metal on a different basis/unit/market is a
-- different series — identity is the instrument, not the metal name.
CREATE TABLE external_data.metal_instruments (
    instrument_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_code     TEXT NOT NULL UNIQUE,
    metal_code          TEXT NOT NULL,
    label               TEXT NOT NULL,
    market              TEXT NOT NULL,
    quotation_basis     TEXT NOT NULL,
    native_currency     TEXT NOT NULL CHECK (char_length(native_currency) = 3),
    unit_code           TEXT NOT NULL,
    unit_label          TEXT NOT NULL,
    source_id           TEXT NOT NULL REFERENCES external_data.market_data_sources (source_id) ON DELETE RESTRICT,
    source_series_key   TEXT NOT NULL,
    granularity         TEXT NOT NULL CHECK (granularity IN ('month', 'year')),
    active              BOOLEAN NOT NULL DEFAULT true,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Normalized observations at native granularity. Idempotent identity:
-- (instrument, observation_date, source). ``observation_date`` is the
-- period start (first day of the month for monthly series). A stored row
-- is a real published value; gaps are absence, never zero.
CREATE TABLE external_data.metal_quote_observations (
    observation_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_id       INTEGER NOT NULL REFERENCES external_data.metal_instruments (instrument_id) ON DELETE RESTRICT,
    observation_date    DATE NOT NULL,
    native_price        NUMERIC(20, 6) NOT NULL CHECK (native_price > 0),
    native_currency     TEXT NOT NULL,
    unit_code           TEXT NOT NULL,
    quote_basis         TEXT NOT NULL,
    source_id           TEXT NOT NULL REFERENCES external_data.market_data_sources (source_id) ON DELETE RESTRICT,
    source_record_key   TEXT,
    retrieved_at        TIMESTAMPTZ NOT NULL,
    revised_at          TIMESTAMPTZ,
    quality_status      TEXT NOT NULL DEFAULT 'validated' CHECK (quality_status IN ('validated', 'estimated')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (instrument_id, observation_date, source_id)
);

CREATE INDEX metal_quote_observations_instrument_date_idx
    ON external_data.metal_quote_observations (instrument_id, observation_date DESC);

-- FX observations keyed by pair + rate_kind: PTAX, spot and other
-- references never share a key. Positive rate invariant.
CREATE TABLE external_data.fx_rate_observations (
    fx_id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pair_code           TEXT NOT NULL,
    rate_kind           TEXT NOT NULL,
    reference_date      DATE NOT NULL,
    value               NUMERIC(20, 6) NOT NULL CHECK (value > 0),
    source_id           TEXT NOT NULL REFERENCES external_data.market_data_sources (source_id) ON DELETE RESTRICT,
    source_record_key   TEXT,
    retrieved_at        TIMESTAMPTZ NOT NULL,
    revised_at          TIMESTAMPTZ,
    quality_status      TEXT NOT NULL DEFAULT 'validated' CHECK (quality_status IN ('validated', 'estimated')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (pair_code, rate_kind, reference_date, source_id)
);

CREATE INDEX fx_rate_observations_pair_kind_date_idx
    ON external_data.fx_rate_observations (pair_code, rate_kind, reference_date DESC);

-- Operational trail: no raw payloads, tokens or personal data. Outcome is
-- honest — a partial batch is not reported as full success.
CREATE TABLE external_data.market_data_ingestion_runs (
    run_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id         TEXT NOT NULL,
    feed                TEXT NOT NULL,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    outcome             TEXT NOT NULL DEFAULT 'running' CHECK (outcome IN ('running', 'success', 'partial', 'failed')),
    fetched_count       INTEGER NOT NULL DEFAULT 0,
    inserted_count      INTEGER NOT NULL DEFAULT 0,
    updated_count       INTEGER NOT NULL DEFAULT 0,
    skipped_count       INTEGER NOT NULL DEFAULT 0,
    safe_error_code     TEXT,
    correlation_id      TEXT,
    version             TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX market_data_ingestion_runs_feed_started_idx
    ON external_data.market_data_ingestion_runs (feed, started_at DESC);
