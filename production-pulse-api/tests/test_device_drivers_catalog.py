from __future__ import annotations

from uuid import uuid4

import pytest

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.infrastructure.drivers.http_counter_driver import HttpCounterDriver
from production_pulse_app.infrastructure.drivers.http_gauge_driver import HttpGaugeDriver
from production_pulse_app.startup.register_device_drivers import (
    reset_device_driver_registration_for_tests,
)


def _unique_key(prefix: str = "custom") -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def test_seed_drivers_present_in_list(client):
    response = client.get("/drivers")
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()["data"]["items"]}
    assert {"esp8266_counter_v1", "esp32c3_counter_v1", "esp8266_gauge_v1"} <= keys


def test_create_patch_archive_unarchive_driver(client):
    key = _unique_key("http_counter")
    created = client.post(
        "/drivers",
        json={
            "driverKey": key,
            "protocolKind": "http_counter",
            "labelPt": "Contador custom",
            "descriptionPt": "Novo tipo sem deploy",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()["data"]
    assert body["key"] == key
    assert body["protocolKind"] == "http_counter"
    assert body["roleKey"] == "pulse_counter"
    assert body["archivedAt"] is None

    patched = client.patch(
        f"/drivers/{key}",
        json={"labelPt": "Contador custom v2", "poll": {"timeoutMs": 4500}},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"]["labelPt"] == "Contador custom v2"
    assert patched.json()["data"]["poll"]["timeoutMs"] == 4500

    archived = client.post(f"/drivers/{key}/archive")
    assert archived.status_code == 200
    assert archived.json()["data"]["archivedAt"] is not None

    active = client.get("/drivers")
    assert key not in {item["key"] for item in active.json()["data"]["items"]}

    all_rows = client.get("/drivers", params={"includeArchived": True})
    assert key in {item["key"] for item in all_rows.json()["data"]["items"]}

    restored = client.post(f"/drivers/{key}/unarchive")
    assert restored.status_code == 200
    assert restored.json()["data"]["archivedAt"] is None


def test_create_rejects_invalid_protocol_kind(client):
    response = client.post(
        "/drivers",
        json={
            "driverKey": _unique_key("badproto"),
            "protocolKind": "mqtt_counter",
            "labelPt": "Inválido",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalidProtocolKind"


def test_create_rejects_duplicate_key(client):
    response = client.post(
        "/drivers",
        json={
            "driverKey": "esp8266_counter_v1",
            "protocolKind": "http_counter",
            "labelPt": "Duplicado",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "driverKeyExists"


def test_firmware_create_rejects_archived_driver(client, tmp_path, monkeypatch):
    monkeypatch.setenv("PP_FIRMWARE_UPLOAD_DIR", str(tmp_path / "firmwares"))
    from production_pulse_app import config as config_module

    config_module.settings.PP_FIRMWARE_UPLOAD_DIR = str(tmp_path / "firmwares")

    key = _unique_key("arch_fw")
    created = client.post(
        "/drivers",
        json={"driverKey": key, "protocolKind": "http_counter", "labelPt": "Para arquivar"},
    )
    assert created.status_code == 201, created.text
    assert client.post(f"/drivers/{key}/archive").status_code == 200

    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": key,
            "driverKey": key,
            "version": "1.0.0",
            "displayName": "Archived driver fw",
            "publish": "true",
        },
        files={"file": ("x.bin", b"z" * 64, "application/octet-stream")},
    )
    assert published.status_code == 422
    assert published.json()["error"]["code"] == "driverArchived"


def test_firmware_create_rejects_unknown_driver(client, tmp_path, monkeypatch):
    monkeypatch.setenv("PP_FIRMWARE_UPLOAD_DIR", str(tmp_path / "firmwares"))
    from production_pulse_app import config as config_module

    config_module.settings.PP_FIRMWARE_UPLOAD_DIR = str(tmp_path / "firmwares")

    published = client.post(
        "/firmwares",
        data={
            "firmwareKey": "missing_family_v1",
            "driverKey": "does_not_exist_v1",
            "version": "1.0.0",
            "displayName": "Missing driver",
            "publish": "true",
        },
        files={"file": ("x.bin", b"z" * 64, "application/octet-stream")},
    )
    assert published.status_code == 422
    assert published.json()["error"]["code"] == "driverKeyUnknown"


def test_catalog_and_firmware_drivers_omit_archived(client):
    key = _unique_key("hidden")
    assert (
        client.post(
            "/drivers",
            json={"driverKey": key, "protocolKind": "http_gauge", "labelPt": "Gauge temp"},
        ).status_code
        == 201
    )
    assert client.post(f"/drivers/{key}/archive").status_code == 200

    catalog = client.get("/catalog/drivers")
    assert catalog.status_code == 200
    assert key not in {item["key"] for item in catalog.json()["data"]["drivers"]}

    fw_drivers = client.get("/firmware-drivers")
    assert fw_drivers.status_code == 200
    keys = {item["key"] for item in fw_drivers.json()["data"]["items"]}
    assert key not in keys


def test_get_implementation_factory_db_only_counter(plugins_db_env):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_driver_repository import (
        PostgresDeviceDriverRepository,
    )

    key = _unique_key("factory")
    PostgresDeviceDriverRepository().create(
        {
            "driver_key": key,
            "protocol_kind": "http_counter",
            "role_key": "pulse_counter",
            "label_pt": "Factory counter",
            "description_pt": None,
            "metrics": [{"key": "counter", "type": "integer", "labelPt": "Golpes", "primary": True}],
            "commands": ["increment", "reset"],
            "operator_surface": "counter_pad",
            "operator_eligible": True,
            "poll": {"timeoutMs": 3000},
            "thresholds": {},
            "counter_restore": None,
        }
    )
    reset_device_driver_registration_for_tests()
    driver = get_device_driver_registry().get_implementation(key)
    assert isinstance(driver, HttpCounterDriver)
    assert driver.driver_key == key
    reset_device_driver_registration_for_tests()


def test_get_implementation_factory_db_only_gauge(plugins_db_env):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_driver_repository import (
        PostgresDeviceDriverRepository,
    )

    key = _unique_key("gauge")
    PostgresDeviceDriverRepository().create(
        {
            "driver_key": key,
            "protocol_kind": "http_gauge",
            "role_key": "process_gauge",
            "label_pt": "Factory gauge",
            "description_pt": None,
            "metrics": [
                {"key": "rpm", "type": "number", "labelPt": "Rotação", "primary": True},
            ],
            "commands": [],
            "operator_surface": "gauge_readout",
            "operator_eligible": True,
            "poll": {"timeoutMs": 3000},
            "thresholds": {},
            "counter_restore": None,
        }
    )
    reset_device_driver_registration_for_tests()
    driver = get_device_driver_registry().get_implementation(key)
    assert isinstance(driver, HttpGaugeDriver)
    assert driver.driver_key == key
    reset_device_driver_registration_for_tests()


def test_get_implementation_rejects_unknown_protocol_kind(plugins_db_env, monkeypatch):
    reset_device_driver_registration_for_tests()
    registry = get_device_driver_registry()

    class _FakeRepo:
        def get_by_key(self, driver_key: str):
            return {
                "driver_key": driver_key,
                "protocol_kind": "mqtt_counter",
                "role_key": "pulse_counter",
                "label_pt": "x",
                "description_pt": None,
                "metrics": [],
                "commands": [],
                "operator_surface": "counter_pad",
                "operator_eligible": True,
                "poll": {},
                "thresholds": {},
                "counter_restore": None,
                "archived_at": None,
            }

    monkeypatch.setattr(registry, "_repo", _FakeRepo())
    with pytest.raises(DeviceDriverNotImplementedError):
        registry.get_implementation("broken_proto_v1")
    reset_device_driver_registration_for_tests()


def test_archive_allowed_while_device_still_polls(client, unique_ip, plugins_db_env):
    """Archive is soft; existing devices keep the key and factory still resolves."""
    key = _unique_key("inuse")
    assert (
        client.post(
            "/drivers",
            json={"driverKey": key, "protocolKind": "http_counter", "labelPt": "Em uso"},
        ).status_code
        == 201
    )
    created = client.post(
        "/devices",
        json={
            "name": "Device with custom driver",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": key,
            "enabled": True,
        },
    )
    assert created.status_code == 201, created.text
    assert client.post(f"/drivers/{key}/archive").status_code == 200

    reset_device_driver_registration_for_tests()
    impl = get_device_driver_registry().get_implementation(key)
    assert isinstance(impl, HttpCounterDriver)
    reset_device_driver_registration_for_tests()
