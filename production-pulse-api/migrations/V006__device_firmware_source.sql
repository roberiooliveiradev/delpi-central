-- Sketch Arduino (.ino) cadastrado por dispositivo — texto completo para cópia no detalhe.

ALTER TABLE production_pulse.devices
    ADD COLUMN IF NOT EXISTS firmware_source TEXT;

COMMENT ON COLUMN production_pulse.devices.firmware_source IS
    'Código-fonte do firmware (.ino) associado ao dispositivo. Opcional; exibido na aba Firmware do detalhe.';
