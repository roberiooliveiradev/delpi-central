from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

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
    """Ensure route-level services pick up the temp upload dir."""
    from production_pulse_app.application.services.firmware_catalog_service import (
        FirmwareCatalogService,
    )
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )
    from production_pulse_app.application.services.device_ota_service import DeviceOtaService
    from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
        FirmwareArtifactStorage,
    )
    import production_pulse_app.interface.http.routes.firmware_routes as firmware_routes
    import production_pulse_app.interface.http.routes.device_ota_routes as device_ota_routes

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


def test_publish_list_and_duplicate_firmware(client, unique_ip, firmware_storage_dir):
    device = _create_device(client, ip=unique_ip)
    assert device["firmwareKey"] == "esp8266_counter_v1"

    files = {"file": ("counter.bin", b"firmware-v120-bytes", "application/octet-stream")}
    data = {
        "firmwareKey": "esp8266_counter_v1",
        "driverKey": "esp8266_counter_v1",
        "version": "1.2.0",
        "displayName": "Leitor de maquina",
        "publish": "true",
    }
    published = client.post("/firmwares", data=data, files=files)
    assert published.status_code == 201, published.text
    item = published.json()["data"]
    assert item["firmwareKey"] == "esp8266_counter_v1"
    assert item["version"] == "1.2.0"
    assert len(item["artifactSha256"]) == 64
    assert "artifactPath" not in item

    listed = client.get("/firmwares", params={"firmwareKey": "esp8266_counter_v1"})
    assert listed.status_code == 200
    assert len(listed.json()["data"]["items"]) == 1

    dup = client.post("/firmwares", data=data, files=files)
    assert dup.status_code == 422
    assert dup.json()["error"]["code"] == "firmwareDuplicateVersion"


def test_manual_job_check_download_report_and_summary(client, unique_ip, firmware_storage_dir):
    token = "ota-token-1"
    code = f"ESP-{uuid4().hex[:8].upper()}"
    device = _create_device(client, ip=unique_ip, token=token, code=code)
    device_id = device["id"]

    # Seed installed version so onlyOutdated still selects when different
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="1.1.0"
    )

    files = {"file": ("counter.bin", b"firmware-v130-bytes", "application/octet-stream")}
    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "1.3.0",
            "displayName": "Counter",
            "publish": "true",
        },
        files=files,
    )
    assert published.status_code == 201
    firmware_id = published.json()["data"]["id"]

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"firmwareKey": "esp8266_counter_v1", "onlyOutdated": True},
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["data"]["id"]
    assert job.json()["data"]["status"] == "running"

    targets = client.get(f"/firmware-update-jobs/{job_id}/targets")
    assert targets.status_code == 200
    items = targets.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["status"] == "authorized"

    check = client.get(
        "/device-ota/check",
        params={"deviceId": device_id},
        headers={"X-Device-Token": token},
    )
    assert check.status_code == 200, check.text
    check_data = check.json()["data"]
    assert check_data["updateAvailable"] is True
    artifact_token = check_data["artifactToken"]

    unauthorized = client.get(
        "/device-ota/check",
        params={"deviceId": device_id},
        headers={"X-Device-Token": "wrong"},
    )
    assert unauthorized.status_code == 401

    download = client.get(
        f"/device-ota/artifacts/{artifact_token}",
        params={"deviceId": device_id},
        headers={"X-Device-Token": token},
    )
    assert download.status_code == 200
    assert download.content == b"firmware-v130-bytes"

    report = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": check_data["targetId"],
            "status": "updated",
            "installedFirmwareVersion": "1.3.0",
        },
    )
    assert report.status_code == 200, report.text
    assert report.json()["data"]["status"] == "updated"

    fetched = client.get(f"/devices/{device_id}")
    assert fetched.json()["data"]["installedFirmwareVersion"] == "1.3.0"

    summary = client.get(
        "/firmware-update-summary",
        params={"branch": "01", "firmwareKey": "esp8266_counter_v1"},
    )
    assert summary.status_code == 200
    body = summary.json()["data"]
    assert body["total"] >= 1
    assert body["updated"] >= 1

    # Negative: no second open target while first completed is ok; create another job conflict when open
    files2 = {"file": ("counter.bin", b"firmware-v140-bytes", "application/octet-stream")}
    published2 = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "1.4.0",
            "displayName": "Counter",
            "publish": "true",
        },
        files=files2,
    )
    assert published2.status_code == 201


def test_scheduled_job_authorizes_only_after_due(client, unique_ip, firmware_storage_dir):
    token = "ota-token-2"
    device = _create_device(client, ip=unique_ip, token=token)
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device["id"]), version="1.0.0"
    )

    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "2.0.0",
            "displayName": "Counter",
            "publish": "true",
        },
        files={"file": ("c.bin", b"fw20", "application/octet-stream")},
    )
    firmware_id = published.json()["data"]["id"]

    future = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "scheduled",
            "scheduledAt": future,
        },
    )
    assert job.status_code == 201, job.text
    assert job.json()["data"]["status"] == "scheduled"
    job_id = job.json()["data"]["id"]

    check_before = client.get(
        "/device-ota/check",
        params={"deviceId": device["id"]},
        headers={"X-Device-Token": token},
    )
    assert check_before.json()["data"]["updateAvailable"] is False

    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )
    from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
        PostgresFirmwareUpdateJobRepository,
    )

    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    # Force due by rewriting scheduled_at
    with __import__(
        "production_pulse_app.infrastructure.persistence.plugins_postgres_connection",
        fromlist=["plugins_connection"],
    ).plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE production_pulse.firmware_update_jobs
                SET scheduled_at = %s
                WHERE id = %s
                """,
                (past, job_id),
            )
        conn.commit()

    authorized = FirmwareUpdateJobService().authorize_due_scheduled()
    assert authorized >= 1

    check_after = client.get(
        "/device-ota/check",
        params={"deviceId": device["id"]},
        headers={"X-Device-Token": token},
    )
    assert check_after.json()["data"]["updateAvailable"] is True

    # sibling: cancel
    cancelled = client.post(f"/firmware-update-jobs/{job_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"


def test_ota_progress_report_and_device_status(client, unique_ip, firmware_storage_dir):
    token = "ota-progress-token"
    device = _create_device(client, ip=unique_ip, token=token)
    device_id = device["id"]
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="1.0.0"
    )

    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "1.5.0",
            "displayName": "Counter progress",
            "publish": "true",
        },
        files={"file": ("counter.bin", b"x" * 200, "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    firmware_id = published.json()["data"]["id"]

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {
                "firmwareKey": "esp8266_counter_v1",
                "onlyOutdated": True,
                "deviceIds": [device_id],
            },
        },
    )
    assert job.status_code == 201, job.text
    target_id = client.get(
        f"/firmware-update-jobs/{job.json()['data']['id']}/targets"
    ).json()["data"]["items"][0]["id"]

    empty_status = client.get(f"/devices/{uuid4()}/firmware-update-status")
    # wrong id may 404 — sibling below uses real device

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
    pdata = progress.json()["data"]
    assert pdata["status"] == "downloading"
    assert pdata["progressPercent"] == 25
    assert pdata["bytesReceived"] == 50
    assert pdata["bytesTotal"] == 200

    status = client.get(f"/devices/{device_id}/firmware-update-status")
    assert status.status_code == 200, status.text
    sdata = status.json()["data"]
    assert sdata["active"] is True
    assert sdata["status"] == "downloading"
    assert sdata["progressPercent"] == 25
    assert sdata["bytesReceived"] == 50
    assert sdata["toVersion"] == "1.5.0"

    # sibling: percent derived from bytes when percent omitted
    progress2 = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_id,
            "status": "downloading",
            "bytesReceived": 100,
            "bytesTotal": 200,
        },
    )
    assert progress2.status_code == 200
    assert progress2.json()["data"]["progressPercent"] == 50

    applying = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={"deviceId": device_id, "targetId": target_id, "status": "applying"},
    )
    assert applying.status_code == 200
    assert applying.json()["data"]["progressPercent"] == 100

    # negative: no token
    denied = client.post(
        "/device-ota/report",
        json={"deviceId": device_id, "targetId": target_id, "status": "downloading"},
    )
    assert denied.status_code == 401


def test_cancel_rejects_late_report_and_idempotent_cancel(client, unique_ip, firmware_storage_dir):
    token = "ota-cancel-race"
    device = _create_device(client, ip=unique_ip, token=token)
    device_id = device["id"]

    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "2.0.0",
            "displayName": "Cancel race",
            "publish": "true",
        },
        files={"file": ("counter.bin", b"y" * 120, "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    firmware_id = published.json()["data"]["id"]

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device_id]},
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["data"]["id"]
    target_id = client.get(f"/firmware-update-jobs/{job_id}/targets").json()["data"]["items"][0]["id"]

    cancelled = client.post(f"/firmware-update-jobs/{job_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"

    again = client.post(f"/firmware-update-jobs/{job_id}/cancel")
    assert again.status_code == 200
    assert again.json()["data"]["status"] == "cancelled"

    late = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_id,
            "status": "updated",
            "installedFirmwareVersion": "2.0.0",
        },
    )
    assert late.status_code == 422
    assert late.json()["error"]["code"] == "deviceOtaInvalidTransition"


def test_archive_and_patch_firmware_metadata(client, unique_ip, firmware_storage_dir):
    _create_device(client, ip=unique_ip)
    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "3.0.0",
            "displayName": "Before archive",
            "publish": "true",
        },
        files={"file": ("counter.bin", b"z" * 80, "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    firmware_id = published.json()["data"]["id"]

    patched = client.patch(
        f"/firmwares/{firmware_id}",
        json={"displayName": "Renamed version", "releaseNotes": "notes"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"]["displayName"] == "Renamed version"
    assert patched.json()["data"]["releaseNotes"] == "notes"

    archived = client.post(f"/firmwares/{firmware_id}/archive")
    assert archived.status_code == 200
    assert archived.json()["data"]["archivedAt"] is not None

    blocked = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False},
        },
    )
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "firmwareArchived"

    drivers = client.get("/firmware-drivers")
    assert drivers.status_code == 200
    assert any(item.get("key") == "esp8266_counter_v1" for item in drivers.json()["data"]["items"])


def test_job_completes_when_all_targets_updated(client, unique_ip, firmware_storage_dir):
    token = "ota-complete-job"
    device = _create_device(client, ip=unique_ip, token=token)
    device_id = device["id"]
    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "4.0.0",
            "displayName": "Complete job",
            "publish": "true",
        },
        files={"file": ("counter.bin", b"w" * 64, "application/octet-stream")},
    )
    firmware_id = published.json()["data"]["id"]
    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device_id]},
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["data"]["id"]
    target_id = client.get(f"/firmware-update-jobs/{job_id}/targets").json()["data"]["items"][0]["id"]

    updated = client.post(
        "/device-ota/report",
        headers={"X-Device-Token": token},
        json={
            "deviceId": device_id,
            "targetId": target_id,
            "status": "updated",
            "installedFirmwareVersion": "4.0.0",
        },
    )
    assert updated.status_code == 200, updated.text
    jobs = client.get("/firmware-update-jobs", params={"branch": "01"})
    assert jobs.status_code == 200
    row = next(item for item in jobs.json()["data"]["items"] if item["id"] == job_id)
    assert row["status"] == "completed"


def test_ota_job_isolates_c3_and_esp8266_families(client, unique_ip, firmware_storage_dir):
    """Job for C3 firmware must not target ESP8266 devices (and vice-versa)."""
    parts = unique_ip.split(".")
    esp_ip = unique_ip
    c3_ip = f"{parts[0]}.{parts[1]}.{(int(parts[2]) + 1) % 250}.{parts[3]}"

    esp = _create_device(client, ip=esp_ip, token="esp-tok", code=f"ESP-{uuid4().hex[:8].upper()}")
    c3_body = {
        "name": f"C3 {c3_ip}",
        "branch": "01",
        "ipAddress": c3_ip,
        "driverKey": "esp32c3_counter_v1",
        "apiToken": "c3-tok",
        "controllerCode": f"ESP32C3-{uuid4().hex[:12].upper()}",
        "enabled": True,
    }
    c3_created = client.post("/devices", json=c3_body)
    assert c3_created.status_code == 201, c3_created.text
    c3 = c3_created.json()["data"]

    published_c3 = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp32c3_counter_v1",
            "driverKey": "esp32c3_counter_v1",
            "version": "1.0.0",
            "displayName": "C3 Counter",
            "publish": "true",
        },
        files={"file": ("c3.bin", b"c3-firmware-bytes", "application/octet-stream")},
    )
    assert published_c3.status_code == 201, published_c3.text
    c3_fw_id = published_c3.json()["data"]["id"]

    # Explicit ESP8266 id against C3 firmware → no eligible devices
    cross = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": c3_fw_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [esp["id"]]},
        },
    )
    assert cross.status_code == 422, cross.text
    assert cross.json()["error"]["code"] == "noEligibleDevices"

    ok = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": c3_fw_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [c3["id"], esp["id"]]},
        },
    )
    assert ok.status_code == 201, ok.text
    targets = client.get(f"/firmware-update-jobs/{ok.json()['data']['id']}/targets")
    assert targets.status_code == 200
    items = targets.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["deviceId"] == c3["id"]


def test_manual_job_allows_downgrade_to_older_published_version(
    client, unique_ip, firmware_storage_dir
):
    """Upgrade and rollback share the same job motor; onlyOutdated is string inequality."""
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    device = _create_device(client, ip=unique_ip, token="downgrade-tok")
    device_id = device["id"]
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="1.0.0"
    )

    older = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "0.1.3",
            "displayName": "Older",
            "publish": "true",
        },
        files={"file": ("old.bin", b"old-firmware", "application/octet-stream")},
    )
    assert older.status_code == 201, older.text
    older_id = older.json()["data"]["id"]

    newer = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "1.0.0",
            "displayName": "Current",
            "publish": "true",
        },
        files={"file": ("new.bin", b"new-firmware", "application/octet-stream")},
    )
    assert newer.status_code == 201, newer.text

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": older_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {
                "firmwareKey": "esp8266_counter_v1",
                "onlyOutdated": True,
                "deviceIds": [device_id],
            },
        },
    )
    assert job.status_code == 201, job.text
    targets = client.get(f"/firmware-update-jobs/{job.json()['data']['id']}/targets")
    item = targets.json()["data"]["items"][0]
    assert item["fromVersion"] == "1.0.0"
    assert item["toVersion"] == "0.1.3"
    assert item["deviceId"] == device_id


def test_same_version_with_only_outdated_skips_device(
    client, unique_ip, firmware_storage_dir
):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    device = _create_device(client, ip=unique_ip, token="same-tok")
    device_id = device["id"]
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="2.0.0"
    )

    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "2.0.0",
            "displayName": "Same",
            "publish": "true",
        },
        files={"file": ("same.bin", b"same-firmware", "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    firmware_id = published.json()["data"]["id"]

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {
                "onlyOutdated": True,
                "deviceIds": [device_id],
            },
        },
    )
    assert job.status_code == 422, job.text
    assert job.json()["error"]["code"] == "noEligibleDevices"


def test_archived_firmware_rejected_for_new_job(client, unique_ip, firmware_storage_dir):
    device = _create_device(client, ip=unique_ip, token="arch-tok")
    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "3.0.0",
            "displayName": "Arch",
            "publish": "true",
        },
        files={"file": ("arch.bin", b"arch-firmware", "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    firmware_id = published.json()["data"]["id"]

    archived = client.post(f"/firmwares/{firmware_id}/archive")
    assert archived.status_code == 200, archived.text

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device["id"]]},
        },
    )
    assert job.status_code == 422, job.text
    assert job.json()["error"]["code"] == "firmwareArchived"


def test_draft_firmware_not_found_for_job(client, unique_ip, firmware_storage_dir):
    device = _create_device(client, ip=unique_ip, token="draft-tok")
    draft = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "3.1.0",
            "displayName": "Draft",
            "publish": "false",
        },
        files={"file": ("draft.bin", b"draft-firmware", "application/octet-stream")},
    )
    assert draft.status_code == 201, draft.text
    firmware_id = draft.json()["data"]["id"]
    assert draft.json()["data"]["publishedAt"] is None

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": firmware_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device["id"]]},
        },
    )
    assert job.status_code in {404, 422}, job.text


def test_scheduled_job_keeps_to_version_of_selected_firmware_id(
    client, unique_ip, firmware_storage_dir
):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    device = _create_device(client, ip=unique_ip, token="sched-ver-tok")
    device_id = device["id"]
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="1.0.0"
    )

    older = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "0.9.0",
            "displayName": "Sched older",
            "publish": "true",
        },
        files={"file": ("s0.bin", b"sched-old", "application/octet-stream")},
    )
    assert older.status_code == 201, older.text
    older_id = older.json()["data"]["id"]

    client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "1.2.0",
            "displayName": "Sched newer",
            "publish": "true",
        },
        files={"file": ("s1.bin", b"sched-new", "application/octet-stream")},
    )

    future = (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat()
    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": older_id,
            "branch": "01",
            "trigger": "scheduled",
            "scheduledAt": future,
            "filter": {
                "onlyOutdated": True,
                "deviceIds": [device_id],
            },
        },
    )
    assert job.status_code == 201, job.text
    assert job.json()["data"]["firmwareId"] == older_id
    targets = client.get(f"/firmware-update-jobs/{job.json()['data']['id']}/targets")
    item = targets.json()["data"]["items"][0]
    assert item["toVersion"] == "0.9.0"
    assert item["fromVersion"] == "1.0.0"


def test_reconcile_after_downgrade_installed_matches_older_to_version(
    client, unique_ip, firmware_storage_dir
):
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    from uuid import UUID

    device = _create_device(client, ip=unique_ip, token="reconcile-down-tok")
    device_id = device["id"]
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="1.0.0"
    )

    older = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": "0.1.3",
            "displayName": "Reconcile older",
            "publish": "true",
        },
        files={"file": ("r.bin", b"reconcile-old", "application/octet-stream")},
    )
    assert older.status_code == 201, older.text
    older_id = older.json()["data"]["id"]

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": older_id,
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": True, "deviceIds": [device_id]},
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["data"]["id"]

    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="0.1.3"
    )
    closed = FirmwareUpdateJobService().reconcile_device_installed_version(
        UUID(device_id), "0.1.3"
    )
    assert closed is True

    targets = client.get(f"/firmware-update-jobs/{job_id}/targets")
    item = targets.json()["data"]["items"][0]
    assert item["status"] == "updated"
    assert item["toVersion"] == "0.1.3"
