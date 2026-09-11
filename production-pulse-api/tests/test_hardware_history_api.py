from __future__ import annotations

from uuid import UUID, uuid4


def _create_device(client, *, ip: str):
    created = client.post(
        "/devices",
        json={
            "name": f"HW {ip}",
            "branch": "01",
            "ipAddress": ip,
            "driverKey": "esp8266_counter_v1",
            "apiToken": "del-tok",
            "enabled": True,
        },
    )
    assert created.status_code == 201, created.text
    return created.json()["data"]


def test_hardware_history_empty_then_patch_flow(client, unique_ip):
    device = _create_device(client, ip=unique_ip)
    device_id = device["id"]

    history = client.get(f"/devices/{device_id}/hardware-history")
    assert history.status_code == 200, history.text
    body = history.json()["data"]
    assert body["deviceId"] == device_id
    assert body["current"] is None
    assert body["history"] == []
    assert body["summary"]["hardwareCount"] == 0
    assert body["summary"]["legacyUnidentifiedCounterDelta"] == 0

    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_hardware_assignment_repository import (
        PostgresDeviceHardwareAssignmentRepository,
    )
    from production_pulse_app.infrastructure.persistence.repositories.postgres_hardware_unit_repository import (
        PostgresHardwareUnitRepository,
    )

    suffix = uuid4().hex[:8].upper()
    uid = f"ESP-TEST{suffix}"
    mac = f"12:34:56:{suffix[0:2]}:{suffix[2:4]}:{suffix[4:6]}"
    units = PostgresHardwareUnitRepository()
    assignments = PostgresDeviceHardwareAssignmentRepository()
    unit = units.create(
        hardware_uid=uid,
        mac_address=mac,
        controller_code=uid,
        hardware_family="esp8266_counter_v1",
        identity_confidence="strong",
        identity_source="firmware_hardware_uid",
    )
    opened = assignments.open_assignment(
        device_id=UUID(device_id),
        hardware_unit_id=unit["id"],
        ip_address=unique_ip,
        mac_address=mac,
        controller_code=uid,
        hardware_uid=uid,
        identity_confidence="strong",
        firmware_version="1.0.0",
        counter_raw=0,
        logical_counter=0,
    )

    history2 = client.get(f"/devices/{device_id}/hardware-history")
    assert history2.status_code == 200
    data2 = history2.json()["data"]
    assert data2["current"]["hardwareUid"] == uid
    assert data2["summary"]["hardwareCount"] == 1

    patched = client.patch(
        f"/devices/{device_id}/hardware-assignments/{opened['id']}",
        json={"replacementReason": "electronic_failure", "replacementNotes": "board burnt"},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"]["replacementReason"] == "electronic_failure"


def test_deletion_impact_includes_hardware_counts(client, unique_ip):
    device = _create_device(client, ip=unique_ip)
    impact = client.get(f"/devices/{device['id']}/deletion-impact")
    assert impact.status_code == 200
    deps = impact.json()["data"]["dependencies"]
    assert "hardwareAssignments" in deps
    assert "hardwareEvents" in deps
