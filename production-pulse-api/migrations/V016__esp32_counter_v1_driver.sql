-- Official ESP32-WROOM counter driver (http_counter protocol).
-- Wake OTA is internal (HttpCounterDriver.wake_ota_check) — not in commands JSON.

INSERT INTO production_pulse.device_drivers (
    driver_key, protocol_kind, role_key, label_pt, description_pt,
    metrics, commands, operator_surface, operator_eligible, poll, thresholds, counter_restore
) VALUES
(
    'esp32_counter_v1',
    'http_counter',
    'pulse_counter',
    'ESP32-WROOM — contador de golpes',
    'Firmware WROOM: contador público, config/token, reboot e factory-reset autenticados; OTA híbrido isolado por driverKey',
    '[{"key":"counter","type":"integer","monotonic":true,"labelPt":"Golpes","primary":true,"icon":"Hash"}]'::jsonb,
    '["increment","decrement","reset","set","configure","reboot","factory_reset"]'::jsonb,
    'counter_pad',
    TRUE,
    '{"timeoutMs":3000}'::jsonb,
    '{}'::jsonb,
    '{"enabled":true,"preferHardwareSet":true,"intentionalDecreaseCommands":["decrement","reset","set"],"intentionalDecreaseCommandGraceMs":15000}'::jsonb
)
ON CONFLICT (driver_key) DO NOTHING;
