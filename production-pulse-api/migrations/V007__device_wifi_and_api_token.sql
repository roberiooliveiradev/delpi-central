-- Espelho operacional da config do chip (Wi-Fi SSID + debounce + API token).
-- Senha Wi-Fi NÃO é persistida no Postgres.

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS wifi_ssid VARCHAR(64);

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS debounce_ms INTEGER;

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS device_api_token VARCHAR(128);

COMMENT ON COLUMN production_pulse.devices.wifi_ssid IS
    'Last known Wi-Fi SSID from device config (mirror; password not stored).';

COMMENT ON COLUMN production_pulse.devices.debounce_ms IS
    'GPIO debounce milliseconds mirrored from device /api/config.';

COMMENT ON COLUMN production_pulse.devices.device_api_token IS
    'Shared secret for X-Device-Token header when calling the device HTTP API.';
