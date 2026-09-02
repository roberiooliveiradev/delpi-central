-- Mínimo canônico de poll: 1 ms (alinha a device_validation_content.json).

ALTER TABLE production_pulse.devices
    DROP CONSTRAINT IF EXISTS devices_poll_interval_ms_check;

ALTER TABLE production_pulse.devices
    ADD CONSTRAINT devices_poll_interval_ms_check
    CHECK (poll_interval_ms >= 1 AND poll_interval_ms <= 300000);
