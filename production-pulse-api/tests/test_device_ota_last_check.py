from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from production_pulse_app.application.services.device_ota_service import DeviceOtaService


def test_check_records_last_ota_check_at_even_without_update():
    devices = MagicMock()
    jobs = MagicMock()
    jobs.find_authorized_target_for_device.return_value = None
    device_id = uuid4()
    device = {"id": device_id, "installed_firmware_version": "1.0.0"}

    service = DeviceOtaService(device_repository=devices, job_repository=jobs)
    result = service.check(device)

    devices.record_last_ota_check_at.assert_called_once_with(device_id)
    assert result["updateAvailable"] is False


def test_check_records_last_ota_check_at_when_update_available():
    devices = MagicMock()
    jobs = MagicMock()
    target_id = uuid4()
    job_id = uuid4()
    device_id = uuid4()
    jobs.find_authorized_target_for_device.return_value = {
        "id": target_id,
        "job_id": job_id,
        "firmware_key": "esp8266_counter_v1",
        "firmware_version": "1.3.1",
        "to_version": "1.3.1",
        "artifact_sha256": "abc",
        "artifact_size_bytes": 10,
    }
    jobs.update_target.return_value = {}
    device = {"id": device_id, "installed_firmware_version": "1.3.0"}

    service = DeviceOtaService(device_repository=devices, job_repository=jobs)
    result = service.check(device)

    devices.record_last_ota_check_at.assert_called_once_with(device_id)
    assert result["updateAvailable"] is True
    assert result["artifactToken"]
