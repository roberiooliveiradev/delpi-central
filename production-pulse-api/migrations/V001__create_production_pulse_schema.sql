BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS production_pulse;

COMMENT ON SCHEMA production_pulse IS 'Production Pulse — dispositivos IoT, amarrações e leituras.';

CREATE TABLE production_pulse.devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    name VARCHAR(120) NOT NULL,
    ip_address INET NOT NULL,
    driver_key VARCHAR(40) NOT NULL,
    role_key VARCHAR(40) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    poll_interval_seconds INT NOT NULL DEFAULT 30 CHECK (poll_interval_seconds BETWEEN 5 AND 300),
    last_seen_at TIMESTAMPTZ,
    last_poll_attempt_at TIMESTAMPTZ,
    next_poll_at TIMESTAMPTZ,
    last_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64),
    updated_by VARCHAR(64),
    UNIQUE (branch, ip_address)
);

CREATE INDEX production_pulse_devices_branch_role_idx
    ON production_pulse.devices (branch, role_key);

CREATE INDEX production_pulse_devices_branch_enabled_idx
    ON production_pulse.devices (branch, enabled);

CREATE INDEX production_pulse_devices_next_poll_at_idx
    ON production_pulse.devices (next_poll_at)
    WHERE enabled = TRUE;

CREATE TABLE production_pulse.device_bindings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    anchor_type VARCHAR(20) NOT NULL CHECK (
        anchor_type IN ('work_center', 'machine', 'equipment', 'area', 'standalone')
    ),
    placement_label VARCHAR(120) NOT NULL,
    placement_key VARCHAR(160) NOT NULL,
    work_center_code VARCHAR(20),
    work_center_name VARCHAR(120),
    machine_code VARCHAR(40),
    machine_label VARCHAR(120),
    equipment_label VARCHAR(120),
    area_label VARCHAR(120),
    resource_code VARCHAR(20),
    tool_code VARCHAR(20),
    notes TEXT,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(64),
    updated_by VARCHAR(64)
);

CREATE UNIQUE INDEX production_pulse_device_bindings_one_active_per_device_idx
    ON production_pulse.device_bindings (device_id)
    WHERE effective_to IS NULL;

CREATE INDEX production_pulse_device_bindings_anchor_type_idx
    ON production_pulse.device_bindings (anchor_type);

CREATE INDEX production_pulse_device_bindings_work_center_idx
    ON production_pulse.device_bindings (work_center_code)
    WHERE work_center_code IS NOT NULL;

CREATE INDEX production_pulse_device_bindings_placement_key_idx
    ON production_pulse.device_bindings (placement_key)
    WHERE effective_to IS NULL;

CREATE TABLE production_pulse.readings (
    id BIGSERIAL PRIMARY KEY,
    device_id UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    delta_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    source VARCHAR(20) NOT NULL CHECK (source IN ('poll', 'manual', 'command')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX production_pulse_readings_device_recorded_idx
    ON production_pulse.readings (device_id, recorded_at DESC);

CREATE TABLE production_pulse.device_commands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES production_pulse.devices (id) ON DELETE CASCADE,
    command_key VARCHAR(40) NOT NULL,
    issued_by VARCHAR(64) NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    response_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX production_pulse_device_commands_device_created_idx
    ON production_pulse.device_commands (device_id, created_at DESC);

COMMIT;
