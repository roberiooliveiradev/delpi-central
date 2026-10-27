-- PROC-0076 R4 — daily/intraday-ready metal instruments.
--
-- Additive only: no row rewritten, no right widened, no feed activated.
--
-- 1) ``metal_instruments.granularity`` previously allowed only
--    ('month','year'), which blocks registering a future homologated
--    daily metal source. The CHECK now accepts 'day' and 'week' as
--    native granularities; existing rows are untouched (all 'month').
-- 2) ``metal_quote_observations.observation_timestamp`` records the
--    provider's effective quotation instant when the source publishes
--    one — distinct from ``observation_date`` (period start) and
--    ``retrieved_at`` (collection time). NULL for the monthly Pink
--    Sheet rows; the partial unique index gives intraday series a
--    collision-free identity alongside the existing daily-period
--    uniqueness.

ALTER TABLE external_data.metal_instruments
    DROP CONSTRAINT IF EXISTS metal_instruments_granularity_check;

ALTER TABLE external_data.metal_instruments
    ADD CONSTRAINT metal_instruments_granularity_check
    CHECK (granularity IN ('day', 'week', 'month', 'year'));

ALTER TABLE external_data.metal_quote_observations
    ADD COLUMN IF NOT EXISTS observation_timestamp TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS
    metal_quote_observations_intraday_uq
    ON external_data.metal_quote_observations
        (instrument_id, observation_timestamp, source_id)
    WHERE observation_timestamp IS NOT NULL;
