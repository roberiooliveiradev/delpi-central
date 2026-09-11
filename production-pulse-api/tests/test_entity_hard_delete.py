from __future__ import annotations

from pathlib import Path
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
    from production_pulse_app.application.services.firmware_catalog_service import (
        FirmwareCatalogService,
    )
    from production_pulse_app.application.services.firmware_deletion_service import (
        FirmwareDeletionService,
    )
    from production_pulse_app.application.services.firmware_update_job_service import (
        FirmwareUpdateJobService,
    )
    from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
        FirmwareArtifactStorage,
    )
    import production_pulse_app.interface.http.routes.firmware_routes as firmware_routes

    storage = FirmwareArtifactStorage(base_dir=str(firmware_storage_dir))
    firmware_routes._catalog = FirmwareCatalogService(storage=storage)
    firmware_routes._deletion = FirmwareDeletionService(storage=storage)
    firmware_routes._jobs = FirmwareUpdateJobService()
    yield


def _create_device(client, *, ip: str, token: str = "del-tok", code: str | None = None):
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


def _publish_firmware(client, *, version: str, payload: bytes = b"fw-bytes"):
    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "esp8266_counter_v1",
            "driverKey": "esp8266_counter_v1",
            "version": version,
            "displayName": f"FW {version}",
            "publish": "true",
        },
        files={"file": (f"{version}.bin", payload, "application/octet-stream")},
    )
    assert published.status_code == 201, published.text
    return published.json()["data"]


def test_disable_enable_canonical_and_legacy_delete_soft(client, unique_ip):
    device = _create_device(client, ip=unique_ip)
    device_id = device["id"]

    disabled = client.post(f"/devices/{device_id}/disable")
    assert disabled.status_code == 200
    assert disabled.json()["data"]["enabled"] is False

    enabled = client.post(f"/devices/{device_id}/enable")
    assert enabled.status_code == 200
    assert enabled.json()["data"]["enabled"] is True

    legacy = client.delete(f"/devices/{device_id}")
    assert legacy.status_code == 200
    assert legacy.json()["data"]["enabled"] is False

    still = client.get(f"/devices/{device_id}")
    assert still.status_code == 200
    assert still.json()["data"]["enabled"] is False


def test_device_hard_delete_removes_row(client, unique_ip):
    device = _create_device(client, ip=unique_ip, token="hard-tok")
    device_id = device["id"]

    impact = client.get(f"/devices/{device_id}/deletion-impact")
    assert impact.status_code == 200
    body = impact.json()["data"]
    assert body["canDelete"] is True
    assert "bindings" in body["dependencies"]

    deleted = client.delete(f"/devices/{device_id}/permanent")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    missing = client.get(f"/devices/{device_id}")
    assert missing.status_code == 404


def test_device_hard_delete_blocked_when_active_ota(client, unique_ip):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )

    device = _create_device(client, ip=unique_ip, token="ota-block")
    device_id = device["id"]
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device_id), version="1.0.0"
    )

    fw = _publish_firmware(
        client,
        version=f"9.{int(uuid4().hex[:4], 16) % 90 + 10}.0",
        payload=b"block-ota",
    )
    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": fw["id"],
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": True, "deviceIds": [device_id]},
        },
    )
    assert job.status_code == 201, job.text

    impact = client.get(f"/devices/{device_id}/deletion-impact")
    assert impact.status_code == 200
    assert impact.json()["data"]["canDelete"] is False
    assert impact.json()["data"]["blockers"][0]["code"] == "deviceHasActiveOta"

    blocked = client.delete(f"/devices/{device_id}/permanent")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "deviceHasActiveOta"


def test_device_hard_delete_404(client):
    missing = client.delete(f"/devices/{uuid4()}/permanent")
    assert missing.status_code == 404


def test_firmware_hard_delete_removes_artifact(client, unique_ip, firmware_storage_dir):
    _create_device(client, ip=unique_ip)
    fw = _publish_firmware(client, version="0.0.7", payload=b"artifact-delete-me")
    firmware_id = fw["id"]
    relative = None
    # Find artifact under storage
    matches = list(Path(firmware_storage_dir).rglob("*.bin"))
    assert matches, "expected artifact file on disk"
    relative = matches[0]

    impact = client.get(f"/firmwares/{firmware_id}/deletion-impact")
    assert impact.status_code == 200
    assert impact.json()["data"]["canDelete"] is True

    deleted = client.delete(f"/firmwares/{firmware_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    listed = client.get("/firmwares", params={"firmwareKey": "esp8266_counter_v1"})
    ids = [item["id"] for item in listed.json()["data"]["items"]]
    assert firmware_id not in ids
    assert not relative.exists()


def test_firmware_hard_delete_blocked_with_job_history(client, unique_ip):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )

    device = _create_device(client, ip=unique_ip, token="fw-hist")
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device["id"]), version="1.0.0"
    )
    fw = _publish_firmware(client, version="8.8.8", payload=b"hist")
    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": fw["id"],
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device["id"]]},
        },
    )
    assert job.status_code == 201, job.text

    impact = client.get(f"/firmwares/{fw['id']}/deletion-impact")
    assert impact.json()["data"]["canDelete"] is False
    codes = {b["code"] for b in impact.json()["data"]["blockers"]}
    assert "firmwareHasUpdateHistory" in codes or "firmwareHasActiveTargets" in codes

    blocked = client.delete(f"/firmwares/{fw['id']}")
    assert blocked.status_code == 409


def test_firmware_hard_delete_blocked_when_installed(client, unique_ip):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )

    device = _create_device(client, ip=unique_ip, token="fw-inst")
    fw = _publish_firmware(client, version="7.7.7", payload=b"installed")
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device["id"]), version="7.7.7"
    )

    impact = client.get(f"/firmwares/{fw['id']}/deletion-impact")
    assert impact.json()["data"]["canDelete"] is False
    assert any(
        b["code"] == "firmwareInstalledOnDevices"
        for b in impact.json()["data"]["blockers"]
    )

    blocked = client.delete(f"/firmwares/{fw['id']}")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "firmwareInstalledOnDevices"


def test_driver_hard_delete_free_and_blocked(client, unique_ip):
    key = f"temp_driver_{uuid4().hex[:8]}"
    created = client.post(
        "/drivers",
        json={
            "driverKey": key,
            "protocolKind": "http_counter",
            "labelPt": "Temp driver",
        },
    )
    assert created.status_code == 201, created.text

    impact = client.get(f"/drivers/{key}/deletion-impact")
    assert impact.status_code == 200
    assert impact.json()["data"]["canDelete"] is True

    deleted = client.delete(f"/drivers/{key}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True

    listed = client.get("/drivers", params={"includeArchived": True})
    keys = [
        item.get("driverKey") or item.get("key")
        for item in listed.json()["data"]["items"]
    ]
    assert key not in keys

    # Platform driver with device refs is blocked
    _create_device(client, ip=unique_ip, token="drv-block")
    blocked_impact = client.get("/drivers/esp8266_counter_v1/deletion-impact")
    assert blocked_impact.status_code == 200
    assert blocked_impact.json()["data"]["canDelete"] is False
    assert any(
        b["code"] == "driverHasDevices"
        for b in blocked_impact.json()["data"]["blockers"]
    )
    blocked = client.delete("/drivers/esp8266_counter_v1")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "driverHasDevices"


def test_firmware_family_hard_delete_without_deps(client, unique_ip, firmware_storage_dir):
    _create_device(client, ip=unique_ip)
    fw = _publish_firmware(client, version="0.1.0", payload=b"family-clean")
    key = fw["firmwareKey"]
    matches = list(Path(firmware_storage_dir).rglob("*.bin"))
    assert matches

    impact = client.get(f"/firmware-families/{key}/deletion-impact")
    assert impact.status_code == 200
    body = impact.json()["data"]
    assert body["canDelete"] is True
    assert body["versionCount"] == 1
    assert body["willPurgeFinishedJobs"] is False

    deleted = client.delete(f"/firmware-families/{key}")
    assert deleted.status_code == 200
    assert deleted.json()["data"]["deleted"] is True
    assert deleted.json()["data"]["versionCount"] == 1

    listed = client.get("/firmwares", params={"firmwareKey": key})
    assert listed.json()["data"]["items"] == []
    assert not matches[0].exists()


def test_firmware_family_hard_delete_purges_finished_jobs(client, unique_ip):
    from production_pulse_app.infrastructure.persistence.plugins_postgres_connection import (
        plugins_connection,
    )
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )

    device = _create_device(client, ip=unique_ip, token="fam-purge")
    PostgresDeviceRepository().record_installed_firmware_version(
        UUID(device["id"]), version="1.0.0"
    )
    fw_a = _publish_firmware(client, version="3.1.0", payload=b"a")
    fw_b = _publish_firmware(client, version="3.2.0", payload=b"b")
    key = fw_a["firmwareKey"]

    job = client.post(
        "/firmware-update-jobs",
        json={
            "firmwareId": fw_a["id"],
            "branch": "01",
            "trigger": "manual",
            "filter": {"onlyOutdated": False, "deviceIds": [device["id"]]},
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["data"]["id"]

    active_impact = client.get(f"/firmware-families/{key}/deletion-impact")
    assert active_impact.status_code == 200
    assert active_impact.json()["data"]["canDelete"] is False
    assert any(
        b["code"] == "firmwareHasActiveTargets"
        for b in active_impact.json()["data"]["blockers"]
    )
    blocked = client.delete(f"/firmware-families/{key}")
    assert blocked.status_code == 409

    with plugins_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE production_pulse.firmware_update_targets
                SET status = 'updated', finished_at = NOW(), updated_at = NOW()
                WHERE job_id = %s
                """,
                (job_id,),
            )
            cur.execute(
                """
                UPDATE production_pulse.firmware_update_jobs
                SET status = 'completed', updated_at = NOW()
                WHERE id = %s
                """,
                (job_id,),
            )
        conn.commit()

    impact = client.get(f"/firmware-families/{key}/deletion-impact")
    assert impact.status_code == 200
    body = impact.json()["data"]
    assert body["canDelete"] is True
    assert body["jobsFinished"] >= 1
    assert body["willPurgeFinishedJobs"] is True
    assert body["versionCount"] == 2

    # Version-level delete still blocked by finished history.
    version_impact = client.get(f"/firmwares/{fw_a['id']}/deletion-impact")
    assert version_impact.json()["data"]["canDelete"] is False
    assert any(
        b["code"] == "firmwareHasUpdateHistory"
        for b in version_impact.json()["data"]["blockers"]
    )

    deleted = client.delete(f"/firmware-families/{key}")
    assert deleted.status_code == 200, deleted.text
    data = deleted.json()["data"]
    assert data["purgedJobs"] >= 1
    assert data["versionCount"] == 2
    assert fw_a["id"] in data["deletedVersionIds"]
    assert fw_b["id"] in data["deletedVersionIds"]

    listed = client.get("/firmwares", params={"firmwareKey": key})
    assert listed.json()["data"]["items"] == []


def test_firmware_family_hard_delete_unlinks_devices(client, unique_ip):
    device = _create_device(client, ip=unique_ip, token="fam-unlink")
    fw = _publish_firmware(client, version="4.0.0", payload=b"unlink-me")
    key = fw["firmwareKey"]

    linked = client.put(
        f"/devices/{device['id']}/firmware-link",
        json={"firmwareKey": key},
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["data"]["assignedFirmwareKey"] == key

    deleted = client.delete(f"/firmware-families/{key}")
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["data"]["unlinkedDevices"] >= 1

    still = client.get(f"/devices/{device['id']}")
    assert still.status_code == 200
    assert still.json()["data"]["assignedFirmwareKey"] in (None, "")
    assert still.json()["data"]["id"] == device["id"]


def test_firmware_family_hard_delete_404_and_403(client, client_factory):
    missing = client.get("/firmware-families/does_not_exist_family/deletion-impact")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "firmwareFamilyNotFound"

    deleted = client.delete("/firmware-families/does_not_exist_family")
    assert deleted.status_code == 404

    viewer = client_factory(permissions=["production-pulse.devices.view"])
    assert viewer.delete("/firmware-families/esp8266_counter_v1").status_code == 403
    assert (
        viewer.get("/firmware-families/esp8266_counter_v1/deletion-impact").status_code
        == 403
    )
