from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest


@pytest.fixture
def firmware_storage_dir(tmp_path, monkeypatch):
    target = tmp_path / "firmwares"
    target.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("PP_FIRMWARE_UPLOAD_DIR", str(target))
    from production_pulse_app import config as config_module

    config_module.settings.PP_FIRMWARE_UPLOAD_DIR = str(target)
    return target


@pytest.fixture(autouse=True)
def _reset_firmware_route_singletons(firmware_storage_dir, monkeypatch):
    from production_pulse_app.application.services.device_ota_service import DeviceOtaService
    from production_pulse_app.application.services.firmware_catalog_service import (
        FirmwareCatalogService,
    )
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )
    from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
        FirmwareArtifactStorage,
    )
    import production_pulse_app.interface.http.routes.device_ota_routes as device_ota_routes
    import production_pulse_app.interface.http.routes.firmware_routes as firmware_routes

    storage = FirmwareArtifactStorage(base_dir=str(firmware_storage_dir))
    firmware_routes._catalog = FirmwareCatalogService(storage=storage)
    firmware_routes._jobs = FirmwareUpdateJobService()
    device_ota_routes._service = DeviceOtaService(storage=storage)
    yield


def _create_device(client, *, ip: str, token: str = "device-secret", code: str | None = None):
    body = {
        "name": f"ESP {ip}",
        "branch": "01",
        "ipAddress": ip,
        "driverKey": "esp8266_counter_v1",
        "apiToken": token,
        "enabled": True,
    }
    if code:
        body["controllerCode"] = code
    created = client.post("/devices", json=body)
    assert created.status_code == 201, created.text
    return created.json()["data"]


def _publish_firmware(client, *, version: str, payload: bytes = b"fw-bytes") -> str:
    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": version,
            "displayName": f"Counter {version}",
            "publish": "true",
        },
        files={"file": ("counter.bin", payload, "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    return published.json()["data"]["id"]


def _create_manual_job(client, *, firmware_id: str, device_id: str) -> tuple[str, str]:
    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {
                "firmwareKey": "esp8266_counter_v1",
                "onlyOutdated": False,
                "deviceIds": [device_id],
            },
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["data"]["id"]
    targets = client.get(f"/firmware-update-jobs/{job_id}/targets")
    assert targets.status_code == 200
    target_id = targets.json()["data"]["items"][0]["id"]
    return job_id, target_id


def _set_target_updated_at(target_id: str, when: datetime) -> None:
    from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
        plugins_connection,
    )

    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE production_pulse.firmware_update_targets
                SET updated_at = %s
                WHERE id = %s
                """,
                (when, target_id),
            )
        conn.commit()


def test_second_job_same_device_conflicts_open_target(client, unique_ip, firmware_storage_dir):
    device = _create_device(client, ip=unique_ip, token="conflict-tok")
    device_id = device["id"]
    fw_a = _publish_firmware(client, version="5.0.0", payload=b"a" * 40)
    fw_b = _publish_firmware(client, version="5.1.0", payload=b"b" * 40)

    job_id, _ = _create_manual_job(client, firmware_id=fw_a, device_id=device_id)

    conflict = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": fw_b,
            "branch": "01",
            "trigger": "manual",
            "filter": {
                "onlyOutdated": False,
                "deviceIds": [device_id],
            },
        },
    )
    assert conflict.status_code == 422, conflict.text
    assert conflict.json()["error"]["code"] == "openTargetExists"
    assert "andamento" in conflict.json()["error"]["message"].lower()

    # Cancel frees the unique open-target index.
    cancelled = client.post(f"/firmware-update-jobs/{job_id}/cancel")
    assert cancelled.status_code == 200


def test_other_device_can_have_parallel_job(client, unique_ip, firmware_storage_dir):
    parts = unique_ip.split(".")
    ip_a = unique_ip
    ip_b = f"{parts[0]}.{parts[1]}.{(int(parts[2]) + 1) % 250}.{parts[3]}"

    device_a = _create_device(client, ip=ip_a, token="tok-a", code=f"A-{uuid4().hex[:8].upper()}")
    device_b = _create_device(client, ip=ip_b, token="tok-b", code=f"B-{uuid4().hex[:8].upper()}")
    firmware_id = _publish_firmware(client, version="5.2.0", payload=b"c" * 40)

    job_a = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device_a["id"]]},
        },
    )
    assert job_a.status_code == 201, job_a.text

    job_b = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device_b["id"]]},
        },
    )
    assert job_b.status_code == 201, job_b.text
    assert job_a.json()["data"]["id"] != job_b.json()["data"]["id"]


def test_report_updated_and_failed_are_idempotent(client, unique_ip, firmware_storage_dir):
    token = "idem-tok"
    device = _create_device(client, ip=unique_ip, token=token)
    device_id = device["id"]
    firmware_id = _publish_firmware(client, version="5.3.0", payload=b"d" * 40)
    _, target_id = _create_manual_job(client, firmware_id=firmware_id, device_id=device_id)

    first = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_id,
            "status": "updated",
            "installedFirmwareVersion": "5.3.0",
        },
    )
    assert first.status_code == 200, first.text
    assert first.json()["data"]["status"] == "updated"

    again = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_id,
            "status": "updated",
            "installedFirmwareVersion": "5.3.0",
        },
    )
    assert again.status_code == 200, again.text
    assert again.json()["data"]["status"] == "updated"

    # Sibling: failed idempotency on a fresh open target.
    firmware_id_2 = _publish_firmware(client, version="5.3.1", payload=b"e" * 40)
    _, target_fail = _create_manual_job(client, firmware_id=firmware_id_2, device_id=device_id)
    fail1 = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_fail,
            "status": "failed",
            "errorCode": "flash_error",
        },
    )
    assert fail1.status_code == 200
    assert fail1.json()["data"]["status"] == "failed"
    fail2 = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_fail,
            "status": "failed",
            "errorCode": "flash_error",
        },
    )
    assert fail2.status_code == 200
    assert fail2.json()["data"]["status"] == "failed"


def test_reconcile_open_target_when_installed_matches_to_version(
    client, unique_ip, firmware_storage_dir
):
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )

    device = _create_device(client, ip=unique_ip, token="reconcile-tok")
    device_id = device["id"]
    firmware_id = _publish_firmware(client, version="5.4.0", payload=b"f" * 40)
    job_id, target_id = _create_manual_job(client, firmware_id=firmware_id, device_id=device_id)

    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="5.4.0"
    )
    closed = FirmwareUpdateJobService().reconcile_device_installed_version(
        UUID(device_id), "5.4.0"
    )
    assert closed is True

    targets = client.get(f"/firmware-update-jobs/{job_id}/targets")
    item = next(t for t in targets.json()["data"]["items"] if t["id"] == target_id)
    assert item["status"] == "updated"

    status = client.get(f"/devices/{device_id}/firmware-update-status")
    assert status.status_code == 200
    assert status.json()["data"]["active"] is False


def test_stale_open_target_fails_and_allows_new_job(client, unique_ip, firmware_storage_dir):
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )

    device = _create_device(client, ip=unique_ip, token="stale-tok")
    device_id = device["id"]
    fw_old = _publish_firmware(client, version="5.5.0", payload=b"g" * 40)
    fw_new = _publish_firmware(client, version="5.5.1", payload=b"h" * 40)
    job_id, target_id = _create_manual_job(client, firmware_id=fw_old, device_id=device_id)

    old = datetime.now(timezone.utc) - timedelta(hours=2)
    _set_target_updated_at(target_id, old)

    failed = FirmwareUpdateJobService().fail_stale_open_targets(stale_seconds=3600)
    assert failed >= 1

    targets = client.get(f"/firmware-update-jobs/{job_id}/targets")
    item = next(t for t in targets.json()["data"]["items"] if t["id"] == target_id)
    assert item["status"] == "failed"
    assert item["errorCode"] == "ota_target_stale"

    # New job can be created after stale recovery.
    job2 = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": fw_new,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device_id]},
        },
    )
    assert job2.status_code == 201, job2.text


def test_recent_activity_is_not_stale(client, unique_ip, firmware_storage_dir):
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )

    device = _create_device(client, ip=unique_ip, token="fresh-tok")
    device_id = device["id"]
    firmware_id = _publish_firmware(client, version="5.6.0", payload=b"i" * 40)
    job_id, target_id = _create_manual_job(client, firmware_id=firmware_id, device_id=device_id)

    recent = datetime.now(timezone.utc) - timedelta(minutes=5)
    _set_target_updated_at(target_id, recent)

    failed = FirmwareUpdateJobService().fail_stale_open_targets(stale_seconds=3600)
    assert failed == 0

    targets = client.get(f"/firmware-update-jobs/{job_id}/targets")
    item = next(t for t in targets.json()["data"]["items"] if t["id"] == target_id)
    assert item["status"] == "authorized"


def test_progress_report_updates_updated_at(client, unique_ip, firmware_storage_dir):
    from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
        plugins_connection,
    )

    token = "progress-upd"
    device = _create_device(client, ip=unique_ip, token=token)
    device_id = device["id"]
    firmware_id = _publish_firmware(client, version="5.7.0", payload=b"j" * 200)
    _, target_id = _create_manual_job(client, firmware_id=firmware_id, device_id=device_id)

    old = datetime.now(timezone.utc) - timedelta(hours=1)
    _set_target_updated_at(target_id, old)

    progress = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_id,
            "status": "downloading",
            "bytesReceived": 50,
            "bytesTotal": 200,
            "progressPercent": 25,
        },
    )
    assert progress.status_code == 200, progress.text

    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT updated_at
                FROM production_pulse.firmware_update_targets
                WHERE id = %s
                """,
                (target_id,),
            )
            row = cur.fetchone()
    updated_at = row["updated_at"]
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=timezone.utc)
    assert updated_at > old
