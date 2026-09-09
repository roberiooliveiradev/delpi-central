-- Firmware version archive (soft). Does not mutate V010/V011.
-- published artifact rows remain immutable; archive only gates new OTA jobs.

ALTER TABLE production_pulse.firmwares
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS firmwares_archived_at_idx
    ON production_pulse.firmwares (archived_at)
    WHERE archived_at IS NULL;

COMMENT ON COLUMN production_pulse.firmwares.archived_at IS
    'When set, version is archived: visible in history, not eligible for new OTA jobs.';
