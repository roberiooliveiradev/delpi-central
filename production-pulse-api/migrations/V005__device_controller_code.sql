-- Código estável do controlador IoT (chipId / identidade do firmware).
-- Preenchido no cadastro e preferencialmente via probe em /api/status.

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS controller_code VARCHAR(64);

COMMENT ON COLUMN production_pulse.devices.controller_code IS
    'Identidade do hardware no firmware (ex.: ESP-00A1B2C3). Opcional; único por filial quando informado.';

CREATE UNIQUE INDEX IF NOT EXISTS production_pulse_devices_branch_controller_code_uidx
    ON production_pulse.devices (branch, controller_code)
    WHERE controller_code IS NOT NULL AND btrim(controller_code) <> '';
