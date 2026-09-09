-- Firmware version source snapshot + draft without artifact.
-- Does not mutate V006/V010/V011/V012.

ALTER TABLE production_pulse.firmwares
    ADD COLUMN IF NOT EXISTS source_text TEXT;

ALTER TABLE production_pulse.firmwares
    ALTER COLUMN artifact_path DROP NOT NULL,
    ALTER COLUMN artifact_sha256 DROP NOT NULL,
    ALTER COLUMN artifact_size_bytes DROP NOT NULL;

ALTER TABLE production_pulse.firmwares
    DROP CONSTRAINT IF EXISTS firmwares_published_requires_artifact;

ALTER TABLE production_pulse.firmwares
    ADD CONSTRAINT firmwares_published_requires_artifact
    CHECK (
        published_at IS NULL
        OR (
            artifact_path IS NOT NULL
            AND artifact_sha256 IS NOT NULL
            AND artifact_size_bytes IS NOT NULL
        )
    );

COMMENT ON COLUMN production_pulse.firmwares.source_text IS
    'Sketch (.ino) snapshot for this firmware version. OTA uses artifact only (R59).';
