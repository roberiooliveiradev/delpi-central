-- OTA hybrid wake telemetry (push wake + pull authorize).
-- wake_* lives on targets; last_ota_check_at on devices (updated only by /device-ota/check).

ALTER TABLE production_pulse.firmware_update_targets
    ADD COLUMN IF NOT EXISTS wake_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS wake_attempted_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS wake_acknowledged_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS wake_error_code VARCHAR(64);

ALTER TABLE production_pulse.firmware_update_targets
    DROP CONSTRAINT IF EXISTS firmware_update_targets_wake_status_check;

ALTER TABLE production_pulse.firmware_update_targets
    ADD CONSTRAINT firmware_update_targets_wake_status_check
    CHECK (
        wake_status IS NULL
        OR wake_status IN ('pending', 'accepted', 'failed')
    );

COMMENT ON COLUMN production_pulse.firmware_update_targets.wake_status IS
    'Best-effort push wake outcome: pending|accepted|failed; independent of OTA target.status.';
COMMENT ON COLUMN production_pulse.firmware_update_targets.wake_attempted_at IS
    'When the API attempted POST /api/ota/check-now on the device.';
COMMENT ON COLUMN production_pulse.firmware_update_targets.wake_acknowledged_at IS
    'When the device accepted the wake (HTTP 2xx/202).';
COMMENT ON COLUMN production_pulse.firmware_update_targets.wake_error_code IS
    'Wake failure code (timeout, refused, network_error, …); never written to error_code.';

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS last_ota_check_at TIMESTAMPTZ;

COMMENT ON COLUMN production_pulse.devices.last_ota_check_at IS
    'Last successful device OTA check request (/device-ota/check); pull telemetry only.';
