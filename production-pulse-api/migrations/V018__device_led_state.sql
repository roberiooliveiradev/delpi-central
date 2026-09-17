-- Last known RGB LED operational state from chip GET /api/status (ledState).
-- Additive; NULL = firmware/API still without field or never polled successfully.

BEGIN;

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS led_state VARCHAR(40);

COMMENT ON COLUMN production_pulse.devices.led_state IS
    'Last ledState from chip /api/status (offline|connecting|wifi_ok_never_contacted|backend_ok|wifi_ok_stale|ota_in_progress|auth_error).';

COMMIT;
