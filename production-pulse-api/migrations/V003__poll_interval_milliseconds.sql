-- Intervalo de poll canônico em milissegundos (fonte única).
-- Converte poll_interval_seconds → poll_interval_ms (0.5 s → 500 ms).

ALTER TABLE production_pulse.devices
    DROP CONSTRAINT IF EXISTS devices_poll_interval_seconds_check;

ALTER TABLE production_pulse.devices
    ADD COLUMN poll_interval_ms INTEGER;

UPDATE production_pulse.devices
SET poll_interval_ms = GREATEST(
    500,
    LEAST(300000, ROUND(poll_interval_seconds * 1000)::integer)
)
WHERE poll_interval_ms IS NULL;

ALTER TABLE production_pulse.devices
    ALTER COLUMN poll_interval_ms SET DEFAULT 30000;

ALTER TABLE production_pulse.devices
    ALTER COLUMN poll_interval_ms SET NOT NULL;

ALTER TABLE production_pulse.devices
    ADD CONSTRAINT devices_poll_interval_ms_check
    CHECK (poll_interval_ms >= 500 AND poll_interval_ms <= 300000);

ALTER TABLE production_pulse.devices
    DROP COLUMN poll_interval_seconds;
