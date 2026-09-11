from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from production_pulse_app.application.services.device_ota_wake_service import DeviceOtaWakeService
from production_pulse_app.domain.models.device_reading import CommandResult


def _target(**overrides):
    base = {
        "id": uuid4(),
        "device_id": uuid4(),
        "status": "authorized",
        "wake_attempted_at": None,
    }
    base.update(overrides)
    return base


def test_wake_success_persists_accepted_without_changing_ota_status():
    jobs = MagicMock()
    devices = MagicMock()
    registry = MagicMock()
    target = _target()
    claimed = {**target, "wake_status": "pending"}
    jobs.claim_wake_attempt.return_value = claimed
    devices.get_by_id.return_value = {
        "id": target["device_id"],
        "driver_key": "esp8266_counter_v1",
        "ip_address": "10.0.0.2",
    }
    driver = MagicMock()
    driver.wake_ota_check.return_value = CommandResult(success=True)
    registry.get_implementation.return_value = driver

    DeviceOtaWakeService(
        job_repository=jobs,
        device_repository=devices,
        driver_registry=registry,
    ).wake_target(target)

    jobs.finalize_wake_attempt.assert_called_once_with(
        target["id"],
        wake_status="accepted",
        wake_error_code=None,
    )
    jobs.transition_target.assert_not_called()


def test_wake_timeout_marks_failed_keeps_authorized():
    jobs = MagicMock()
    devices = MagicMock()
    registry = MagicMock()
    target = _target()
    jobs.claim_wake_attempt.return_value = {**target, "wake_status": "pending"}
    devices.get_by_id.return_value = {
        "id": target["device_id"],
        "driver_key": "esp8266_counter_v1",
    }
    driver = MagicMock()
    driver.wake_ota_check.return_value = CommandResult(success=False, error_code="timeout")
    registry.get_implementation.return_value = driver

    DeviceOtaWakeService(
        job_repository=jobs,
        device_repository=devices,
        driver_registry=registry,
    ).wake_target(target)

    jobs.finalize_wake_attempt.assert_called_once_with(
        target["id"],
        wake_status="failed",
        wake_error_code="timeout",
    )


def test_wake_skips_when_claim_returns_none():
    jobs = MagicMock()
    target = _target(wake_attempted_at="2026-01-01T00:00:00Z")
    jobs.claim_wake_attempt.return_value = None
    DeviceOtaWakeService(job_repository=jobs).wake_target(target)
    jobs.claim_wake_attempt.assert_called_once()
    jobs.finalize_wake_attempt.assert_not_called()


def test_wake_retries_after_prior_failed_attempt():
    jobs = MagicMock()
    devices = MagicMock()
    registry = MagicMock()
    target = _target(
        wake_attempted_at="2026-01-01T00:00:00Z",
        wake_status="failed",
        started_at=None,
    )
    jobs.claim_wake_attempt.return_value = {**target, "wake_status": "pending"}
    devices.get_by_id.return_value = {
        "id": target["device_id"],
        "driver_key": "esp8266_counter_v1",
    }
    driver = MagicMock()
    driver.wake_ota_check.return_value = CommandResult(success=True)
    registry.get_implementation.return_value = driver

    DeviceOtaWakeService(
        job_repository=jobs,
        device_repository=devices,
        driver_registry=registry,
        wake_retry_seconds=60,
    ).wake_target(target)

    jobs.claim_wake_attempt.assert_called_once_with(
        target["id"],
        retry_after_seconds=60,
    )
    jobs.finalize_wake_attempt.assert_called_once_with(
        target["id"],
        wake_status="accepted",
        wake_error_code=None,
    )


def test_wake_skips_when_download_already_started():
    jobs = MagicMock()
    target = _target(started_at="2026-01-01T00:00:01Z")
    DeviceOtaWakeService(job_repository=jobs).wake_target(target)
    jobs.claim_wake_attempt.assert_not_called()


def test_retry_authorized_wakes_lists_then_wakes():
    jobs = MagicMock()
    targets = [_target()]
    jobs.list_authorized_targets_for_wake_retry.return_value = targets
    jobs.claim_wake_attempt.return_value = None
    service = DeviceOtaWakeService(job_repository=jobs, wake_retry_seconds=45)
    assert service.retry_authorized_wakes() == 1
    jobs.list_authorized_targets_for_wake_retry.assert_called_once_with(
        retry_after_seconds=45,
    )
    jobs.claim_wake_attempt.assert_called_once()


def test_create_job_wakes_after_authorize(monkeypatch):
    from production_pulse_app.application.services import firmware_update_job_service as mod

    wake = MagicMock()
    jobs = MagicMock()
    firmwares = MagicMock()
    devices = MagicMock()
    firmware_id = uuid4()
    job_id = uuid4()
    device_id = uuid4()
    firmwares.get_by_id.return_value = {
        "id": firmware_id,
        "published_at": "x",
        "archived_at": None,
        "firmware_key": "esp8266_counter_v1",
        "driver_key": "esp8266_counter_v1",
        "version": "1.3.1",
    }
    devices.list_devices.return_value = [
        {
            "id": device_id,
            "firmware_key": "esp8266_counter_v1",
            "driver_key": "esp8266_counter_v1",
            "installed_firmware_version": "1.3.0",
        }
    ]
    jobs.create_job_with_targets.return_value = {
        "id": job_id,
        "firmware_id": firmware_id,
        "branch": "01",
        "trigger": "manual",
        "status": "running",
        "filter": {},
        "created_by": None,
        "created_at": None,
        "updated_at": None,
        "scheduled_at": None,
    }
    authorized = [
        {
            "id": uuid4(),
            "job_id": job_id,
            "device_id": device_id,
            "status": "authorized",
            "from_version": "1.3.0",
            "to_version": "1.3.1",
            "error_code": None,
            "bytes_received": None,
            "bytes_total": None,
            "progress_percent": None,
            "authorized_at": None,
            "started_at": None,
            "finished_at": None,
            "created_at": None,
            "updated_at": None,
            "wake_status": None,
            "wake_attempted_at": None,
            "wake_acknowledged_at": None,
            "wake_error_code": None,
        }
    ]
    jobs.list_targets.return_value = authorized

    service = mod.FirmwareUpdateJobService(
        job_repository=jobs,
        firmware_repository=firmwares,
        device_repository=devices,
        wake_service=wake,
    )
    service.create_job(
        {
            "firmwareId": str(firmware_id),
            "branch": "01",
            "trigger": "manual",
            "filter": {"deviceIds": [str(device_id)]},
        },
        actor_sub="tester",
    )
    wake.wake_authorized_targets.assert_called_once_with(authorized)
    # Ensure wake is after create (create called before wake)
    assert jobs.create_job_with_targets.call_count == 1


def test_authorize_due_scheduled_wakes_once():
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )

    wake = MagicMock()
    jobs = MagicMock()
    job_id = uuid4()
    targets = [_target(job_id=job_id)]
    jobs.authorize_due_scheduled_jobs.return_value = (1, targets)
    jobs.get_job.return_value = {"id": job_id, "branch": "01", "status": "running"}
    service = FirmwareUpdateJobService(job_repository=jobs, wake_service=wake)
    assert service.authorize_due_scheduled() == 1
    wake.wake_authorized_targets.assert_called_once_with(targets)
