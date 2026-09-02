CREATE TABLE IF NOT EXISTS production_pulse.readings_rollups (
    id              BIGSERIAL PRIMARY KEY,
    device_id       UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    bucket_start    TIMESTAMPTZ NOT NULL,
    resolution      VARCHAR(8) NOT NULL CHECK (resolution IN ('hour', 'day')),
    metrics         JSONB NOT NULL DEFAULT '{}'::jsonb,
    delta_metrics   JSONB NOT NULL DEFAULT '{}'::jsonb,
    samples         INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT readings_rollups_device_res_bucket_uq UNIQUE (device_id, resolution, bucket_start)
);

CREATE INDEX IF NOT EXISTS idx_pp_readings_rollups_device_res_bucket
    ON production_pulse.readings_rollups (device_id, resolution, bucket_start DESC);
