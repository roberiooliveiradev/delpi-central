from __future__ import annotations

from uuid import uuid4


def _create_device(client, *, ip: str, driver_key: str = "esp8266_counter_v1", **extra):
    body = {
        "name": f"ESP {ip}",
        "branch": "01",
        "ipAddress": ip,
        "driverKey": driver_key,
        "enabled": True,
        **extra,
    }
    created = client.post("/devices", json=body)
    assert created.status_code == 201, created.text
    return created.json()["data"]


def test_firmware_link_set_replace_and_clear(client, unique_ip):
    device = _create_device(client, ip=unique_ip)
    device_id = device["id"]
    assert device["firmwareKey"] == "esp8266_counter_v1"
    assert device["assignedFirmwareKey"] == "esp8266_counter_v1"

    cleared = client.put(f"/devices/{device_id}/firmware-link", json={"firmwareKey": None})
    assert cleared.status_code == 200, cleared.text
    data = cleared.json()["data"]
    assert data["assignedFirmwareKey"] is None
    assert data["firmwareKey"] == "esp8266_counter_v1"  # effective via driver

    linked = client.put(
        f"/devices/{device_id}/firmware-link",
        json={"firmwareKey": "esp8266_counter_v1"},
    )
    assert linked.status_code == 200, linked.text
    assert linked.json()["data"]["assignedFirmwareKey"] == "esp8266_counter_v1"

    # Sibling replace stays 1:1 (same family still one key)
    again = client.put(
        f"/devices/{device_id}/firmware-link",
        json={"firmwareKey": "esp8266_counter_v1"},
    )
    assert again.status_code == 200
    assert again.json()["data"]["assignedFirmwareKey"] == "esp8266_counter_v1"


def test_firmware_link_incompatible_driver(client, unique_ip):
    device = _create_device(client, ip=unique_ip, driver_key="esp8266_gauge_v1")
    device_id = device["id"]

    bad = client.put(
        f"/devices/{device_id}/firmware-link",
        json={"firmwareKey": "esp8266_counter_v1"},
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "firmwareLinkIncompatible"


def test_firmware_link_not_found_and_invalid_key(client):
    missing = client.put(
        f"/devices/{uuid4()}/firmware-link",
        json={"firmwareKey": "esp8266_counter_v1"},
    )
    assert missing.status_code == 404

    device = _create_device(client, ip=f"10.99.{uuid4().int % 200}.{uuid4().int % 200}")
    invalid = client.put(
        f"/devices/{device['id']}/firmware-link",
        json={"firmwareKey": "INVALID KEY"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalidFirmwareKey"
