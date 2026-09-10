-- Device driver profiles (catalog) — runtime source of truth for driver metadata.
-- Protocol implementations remain in code (protocol_kind → factory).

CREATE TABLE IF NOT EXISTS production_pulse.device_drivers (
    driver_key VARCHAR(40) PRIMARY KEY,
    protocol_kind VARCHAR(40) NOT NULL,
    role_key VARCHAR(40) NOT NULL,
    label_pt TEXT NOT NULL,
    description_pt TEXT,
    metrics JSONB NOT NULL DEFAULT '[]'::jsonb,
    commands JSONB NOT NULL DEFAULT '[]'::jsonb,
    operator_surface VARCHAR(40) NOT NULL,
    operator_eligible BOOLEAN NOT NULL DEFAULT TRUE,
    poll JSONB NOT NULL DEFAULT '{"timeoutMs": 3000}'::jsonb,
    thresholds JSONB NOT NULL DEFAULT '{}'::jsonb,
    counter_restore JSONB,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT device_drivers_protocol_kind_chk
        CHECK (protocol_kind IN ('http_counter', 'http_gauge'))
);

CREATE INDEX IF NOT EXISTS idx_pp_device_drivers_active
    ON production_pulse.device_drivers (driver_key)
    WHERE archived_at IS NULL;

COMMENT ON TABLE production_pulse.device_drivers IS
    'Driver profiles (metadata). protocol_kind selects code implementation.';
COMMENT ON COLUMN production_pulse.device_drivers.driver_key IS
    'Stable EN key referenced by devices.driver_key and firmwares.driver_key.';
COMMENT ON COLUMN production_pulse.device_drivers.protocol_kind IS
    'Code factory key: http_counter | http_gauge.';

-- Seed MVP drivers (idempotent).
INSERT INTO production_pulse.device_drivers (
    driver_key, protocol_kind, role_key, label_pt, description_pt,
    metrics, commands, operator_surface, operator_eligible, poll, thresholds, counter_restore
) VALUES
(
    'esp8266_counter_v1',
    'http_counter',
    'pulse_counter',
    'ESP8266 — contador de golpes',
    'Firmware: contador público, config/token, reboot e factory-reset autenticados',
    '[{"key":"counter","type":"integer","monotonic":true,"labelPt":"Golpes","primary":true,"icon":"Hash"}]'::jsonb,
    '["increment","decrement","reset","set","configure","reboot","factory_reset"]'::jsonb,
    'counter_pad',
    TRUE,
    '{"timeoutMs":3000}'::jsonb,
    '{}'::jsonb,
    '{"enabled":true,"preferHardwareSet":true,"intentionalDecreaseCommands":["decrement","reset","set"],"intentionalDecreaseCommandGraceMs":15000}'::jsonb
),
(
    'esp32c3_counter_v1',
    'http_counter',
    'pulse_counter',
    'ESP32-C3 Super Mini — contador de golpes',
    'Firmware C3: contador público, config/token, reboot e factory-reset autenticados; OTA isolado por driverKey',
    '[{"key":"counter","type":"integer","monotonic":true,"labelPt":"Golpes","primary":true,"icon":"Hash"}]'::jsonb,
    '["increment","decrement","reset","set","configure","reboot","factory_reset"]'::jsonb,
    'counter_pad',
    TRUE,
    '{"timeoutMs":3000}'::jsonb,
    '{}'::jsonb,
    '{"enabled":true,"preferHardwareSet":true,"intentionalDecreaseCommands":["decrement","reset","set"],"intentionalDecreaseCommandGraceMs":15000}'::jsonb
),
(
    'esp8266_gauge_v1',
    'http_gauge',
    'process_gauge',
    'ESP8266 — sensores de processo',
    'Leitura rpm e temperatura; sem comandos de escrita',
    '[{"key":"rpm","type":"number","monotonic":false,"labelPt":"Rotação","unit":"rpm","primary":true,"icon":"Gauge"},{"key":"temperature_c","type":"number","monotonic":false,"labelPt":"Temperatura","unit":"°C","primary":false,"icon":"Thermometer"}]'::jsonb,
    '[]'::jsonb,
    'gauge_readout',
    TRUE,
    '{"timeoutMs":3000}'::jsonb,
    '{"temperature_c":{"warnAbove":75,"dangerAbove":90}}'::jsonb,
    NULL
)
ON CONFLICT (driver_key) DO NOTHING;
