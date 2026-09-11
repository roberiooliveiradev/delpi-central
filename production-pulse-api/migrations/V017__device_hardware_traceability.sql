-- Device logical point vs physical hardware traceability.
-- devices remain the stable monitoring point; hardware_units track silicon identity.

BEGIN;

CREATE TABLE IF NOT EXISTS production_pulse.hardware_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hardware_uid VARCHAR(64),
    current_mac_address VARCHAR(17),
    controller_code VARCHAR(64),
    hardware_family VARCHAR(40),
    identity_confidence VARCHAR(32) NOT NULL DEFAULT 'legacy_unknown'
        CHECK (identity_confidence IN (
            'strong', 'controller_code', 'mac_fallback', 'legacy_unknown'
        )),
    identity_source VARCHAR(40) NOT NULL DEFAULT 'legacy'
        CHECK (identity_source IN (
            'firmware_hardware_uid', 'controller_code', 'mac', 'legacy', 'manual'
        )),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS production_pulse_hardware_units_uid_uq
    ON production_pulse.hardware_units (hardware_uid)
    WHERE hardware_uid IS NOT NULL;

CREATE INDEX IF NOT EXISTS production_pulse_hardware_units_mac_idx
    ON production_pulse.hardware_units (current_mac_address)
    WHERE current_mac_address IS NOT NULL;

CREATE INDEX IF NOT EXISTS production_pulse_hardware_units_controller_idx
    ON production_pulse.hardware_units (controller_code)
    WHERE controller_code IS NOT NULL;

COMMENT ON TABLE production_pulse.hardware_units IS
    'Physical IoT board identity (silicon). Independent of logical devices.';

CREATE TABLE IF NOT EXISTS production_pulse.device_hardware_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    hardware_unit_id UUID NOT NULL REFERENCES production_pulse.hardware_units (id) ON DELETE RESTRICT,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    ip_address_snapshot INET,
    mac_address_snapshot VARCHAR(17),
    controller_code_snapshot VARCHAR(64),
    hardware_uid_snapshot VARCHAR(64),
    identity_confidence VARCHAR(32) NOT NULL DEFAULT 'legacy_unknown',
    replacement_reason VARCHAR(40),
    replacement_notes TEXT,
    first_firmware_version VARCHAR(32),
    last_firmware_version VARCHAR(32),
    first_counter_raw BIGINT,
    last_counter_raw BIGINT,
    logical_counter_at_start BIGINT,
    logical_counter_at_end BIGINT,
    counter_delta_total BIGINT NOT NULL DEFAULT 0,
    online_seconds_total BIGINT NOT NULL DEFAULT 0,
    reboot_count INT NOT NULL DEFAULT 0,
    last_seen_at TIMESTAMPTZ,
    last_uptime_ms BIGINT,
    last_success_poll_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64),
    updated_by VARCHAR(64),
    CONSTRAINT device_hardware_assignments_period_chk CHECK (
        effective_to IS NULL OR effective_to >= effective_from
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS production_pulse_dha_one_active_per_device_idx
    ON production_pulse.device_hardware_assignments (device_id)
    WHERE effective_to IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS production_pulse_dha_one_active_per_unit_idx
    ON production_pulse.device_hardware_assignments (hardware_unit_id)
    WHERE effective_to IS NULL;

CREATE INDEX IF NOT EXISTS production_pulse_dha_device_from_idx
    ON production_pulse.device_hardware_assignments (device_id, effective_from DESC);

CREATE INDEX IF NOT EXISTS production_pulse_dha_ip_snapshot_idx
    ON production_pulse.device_hardware_assignments (ip_address_snapshot)
    WHERE ip_address_snapshot IS NOT NULL;

CREATE INDEX IF NOT EXISTS production_pulse_dha_mac_snapshot_idx
    ON production_pulse.device_hardware_assignments (mac_address_snapshot)
    WHERE mac_address_snapshot IS NOT NULL;

COMMENT ON TABLE production_pulse.device_hardware_assignments IS
    'Period during which a physical hardware unit occupied a logical device point.';

CREATE TABLE IF NOT EXISTS production_pulse.device_hardware_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES production_pulse.device_hardware_assignments (id) ON DELETE SET NULL,
    hardware_unit_id UUID REFERENCES production_pulse.hardware_units (id) ON DELETE SET NULL,
    event_type VARCHAR(40) NOT NULL CHECK (event_type IN (
        'hardware_detected',
        'hardware_replaced',
        'hardware_removed',
        'hardware_reconnected',
        'network_identity_changed',
        'replacement_confirmed'
    )),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS production_pulse_dhe_device_created_idx
    ON production_pulse.device_hardware_events (device_id, created_at DESC);

CREATE INDEX IF NOT EXISTS production_pulse_dhe_type_idx
    ON production_pulse.device_hardware_events (event_type);

ALTER TABLE production_pulse.readings
    ADD COLUMN IF NOT EXISTS hardware_assignment_id UUID
        REFERENCES production_pulse.device_hardware_assignments (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS production_pulse_readings_assignment_idx
    ON production_pulse.readings (hardware_assignment_id)
    WHERE hardware_assignment_id IS NOT NULL;

ALTER TABLE production_pulse.device_commands
    ADD COLUMN IF NOT EXISTS hardware_assignment_id UUID
        REFERENCES production_pulse.device_hardware_assignments (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS production_pulse_commands_assignment_idx
    ON production_pulse.device_commands (hardware_assignment_id)
    WHERE hardware_assignment_id IS NOT NULL;

ALTER TABLE production_pulse.firmware_update_targets
    ADD COLUMN IF NOT EXISTS hardware_assignment_id UUID
        REFERENCES production_pulse.device_hardware_assignments (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS production_pulse_ota_targets_assignment_idx
    ON production_pulse.firmware_update_targets (hardware_assignment_id)
    WHERE hardware_assignment_id IS NOT NULL;

COMMIT;
