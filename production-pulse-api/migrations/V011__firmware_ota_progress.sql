-- P4 OTA: persist download progress reported by the device (bytes / percent).

ALTER TABLE production_pulse.firmware_update_targets
    ADD COLUMN IF NOT EXISTS bytes_received BIGINT,
    ADD COLUMN IF NOT EXISTS bytes_total BIGINT,
    ADD COLUMN IF NOT EXISTS progress_percent SMALLINT;

ALTER TABLE production_pulse.firmware_update_targets
    DROP CONSTRAINT IF EXISTS firmware_update_targets_progress_percent_check;

ALTER TABLE production_pulse.firmware_update_targets
    ADD CONSTRAINT firmware_update_targets_progress_percent_check
    CHECK (progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100));

ALTER TABLE production_pulse.firmware_update_targets
    DROP CONSTRAINT IF EXISTS firmware_update_targets_bytes_received_check;

ALTER TABLE production_pulse.firmware_update_targets
    ADD CONSTRAINT firmware_update_targets_bytes_received_check
    CHECK (bytes_received IS NULL OR bytes_received >= 0);

ALTER TABLE production_pulse.firmware_update_targets
    DROP CONSTRAINT IF EXISTS firmware_update_targets_bytes_total_check;

ALTER TABLE production_pulse.firmware_update_targets
    ADD CONSTRAINT firmware_update_targets_bytes_total_check
    CHECK (bytes_total IS NULL OR bytes_total >= 0);

COMMENT ON COLUMN production_pulse.firmware_update_targets.bytes_received IS
    'Bytes downloaded so far as reported by the device during OTA downloading.';
COMMENT ON COLUMN production_pulse.firmware_update_targets.bytes_total IS
    'Total artifact size in bytes as reported by the device (Content-Length).';
COMMENT ON COLUMN production_pulse.firmware_update_targets.progress_percent IS
    'Download progress 0-100 reported by the device; null when not downloading.';
