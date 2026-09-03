-- Index for R49 raw retention purge (DELETE WHERE recorded_at < cutoff).
CREATE INDEX IF NOT EXISTS idx_pp_readings_recorded_at
    ON production_pulse.readings (recorded_at);
