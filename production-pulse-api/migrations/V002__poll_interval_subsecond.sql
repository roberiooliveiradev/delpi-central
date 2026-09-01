BEGIN;

ALTER TABLE production_pulse.devices
    DROP CONSTRAINT IF EXISTS devices_poll_interval_seconds_check;

ALTER TABLE production_pulse.devices
    ALTER COLUMN poll_interval_seconds TYPE NUMERIC(6, 2)
    USING poll_interval_seconds::numeric(6, 2);

ALTER TABLE production_pulse.devices
    ADD CONSTRAINT devices_poll_interval_seconds_check
    CHECK (poll_interval_seconds >= 0.5 AND poll_interval_seconds <= 300);

COMMIT;
