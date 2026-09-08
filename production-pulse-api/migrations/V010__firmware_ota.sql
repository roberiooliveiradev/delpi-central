-- P4 Firmware OTA: catalog, campaigns, per-device targets, device version columns.

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS firmware_key VARCHAR(64),
    ADD COLUMN IF NOT EXISTS installed_firmware_version VARCHAR(32),
    ADD COLUMN IF NOT EXISTS target_firmware_version VARCHAR(32),
    ADD COLUMN IF NOT EXISTS firmware_reported_at TIMESTAMPTZ;

COMMENT ON COLUMN production_pulse.devices.firmware_key IS
    'OTA firmware family (default aligned to driver_key). Independent of firmware_source sketch text.';
COMMENT ON COLUMN production_pulse.devices.installed_firmware_version IS
    'Last firmware version reported by the device (probe/poll/OTA report).';
COMMENT ON COLUMN production_pulse.devices.target_firmware_version IS
    'Desired firmware version for the device; nullable means follow campaign/latest published.';
COMMENT ON COLUMN production_pulse.devices.firmware_reported_at IS
    'When installed_firmware_version was last observed from the device.';

UPDATE production_pulse.devices
SET firmware_key = driver_key
WHERE firmware_key IS NULL;

CREATE INDEX IF NOT EXISTS idx_pp_devices_firmware_key
    ON production_pulse.devices (branch, firmware_key);

CREATE TABLE IF NOT EXISTS production_pulse.firmwares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firmware_key VARCHAR(64) NOT NULL,
    driver_key VARCHAR(40) NOT NULL,
    version VARCHAR(32) NOT NULL,
    display_name VARCHAR(120) NOT NULL,
    artifact_path TEXT NOT NULL,
    artifact_sha256 CHAR(64) NOT NULL,
    artifact_size_bytes BIGINT NOT NULL CHECK (artifact_size_bytes >= 0),
    release_notes TEXT,
    min_compatible_version VARCHAR(32),
    published_at TIMESTAMPTZ,
    created_by VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT firmwares_key_version_uq UNIQUE (firmware_key, version)
);

CREATE INDEX IF NOT EXISTS idx_pp_firmwares_driver_key
    ON production_pulse.firmwares (driver_key);

CREATE INDEX IF NOT EXISTS idx_pp_firmwares_published_at
    ON production_pulse.firmwares (firmware_key, published_at DESC NULLS LAST);

CREATE TABLE IF NOT EXISTS production_pulse.firmware_update_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firmware_id UUID NOT NULL REFERENCES production_pulse.firmwares (id) ON DELETE RESTRICT,
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    trigger VARCHAR(20) NOT NULL CHECK (trigger IN ('manual', 'scheduled')),
    scheduled_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'scheduled', 'running', 'completed', 'cancelled', 'failed')),
    filter JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT firmware_update_jobs_scheduled_requires_at CHECK (
        trigger <> 'scheduled' OR scheduled_at IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_pp_firmware_jobs_branch_status
    ON production_pulse.firmware_update_jobs (branch, status);

CREATE INDEX IF NOT EXISTS idx_pp_firmware_jobs_scheduled
    ON production_pulse.firmware_update_jobs (scheduled_at)
    WHERE status = 'scheduled';

CREATE TABLE IF NOT EXISTS production_pulse.firmware_update_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES production_pulse.firmware_update_jobs (id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending', 'authorized', 'downloading', 'applying',
            'updated', 'failed', 'skipped', 'cancelled'
        )),
    from_version VARCHAR(32),
    to_version VARCHAR(32) NOT NULL,
    error_code VARCHAR(64),
    artifact_token VARCHAR(64),
    artifact_token_expires_at TIMESTAMPTZ,
    authorized_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pp_firmware_targets_job_status
    ON production_pulse.firmware_update_targets (job_id, status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_pp_firmware_targets_one_open_per_device
    ON production_pulse.firmware_update_targets (device_id)
    WHERE status IN ('pending', 'authorized', 'downloading', 'applying');

CREATE INDEX IF NOT EXISTS idx_pp_firmware_targets_artifact_token
    ON production_pulse.firmware_update_targets (artifact_token)
    WHERE artifact_token IS NOT NULL;
