from production_pulse_app.domain.models.device_reading import DeviceReading


def _create_device(client, unique_ip: str):
    response = client.post(
        "/devices",
        json={
            "name": "ESP poll",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def _bind_equipment(client, device_id: str):
    client.put(
        f"/devices/{device_id}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Motor teste poll"},
    )


def test_test_probe_does_not_persist_device_or_reading(client, unique_ip, monkeypatch):
    from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
        PostgresDeviceRepository,
    )
    import production_pulse_app.application.services.device_probe_service as probe_module

    class _FakeRegistry:
        def get_implementation(self, _driver_key):
            class _Driver:
                def test(self, device):
                    return DeviceReading(metrics={"counter": 99})

            return _Driver()

    monkeypatch.setattr(probe_module, "get_device_driver_registry", lambda: _FakeRegistry())

    repo = PostgresDeviceRepository()
    before_devices = len(repo.list_devices(branch="01"))

    response = client.post(
        "/devices/test-probe",
        json={
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["online"] is True
    assert body["metrics"]["counter"] == 99

    after_devices = len(repo.list_devices(branch="01"))
    assert after_devices == before_devices


def test_manual_poll_persists_reading_and_delta(client, unique_ip, monkeypatch):
    sequence = iter(
        [
            DeviceReading(metrics={"counter": 10}),
            DeviceReading(metrics={"counter": 15}),
        ]
    )

    def fake_read(_self, _device):
        return next(sequence)

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )

    device = _create_device(client, unique_ip)
    _bind_equipment(client, device["id"])

    first = client.post(f"/devices/{device['id']}/poll")
    assert first.status_code == 200
    first_body = first.json()["data"]
    assert first_body["metrics"]["counter"] == 10
    assert first_body["deltaMetrics"]["counter"] == 0
    assert first_body["online"] is True
    assert first_body["status"] == "online"

    second = client.post(f"/devices/{device['id']}/poll")
    assert second.status_code == 200
    second_body = second.json()["data"]
    assert second_body["deltaMetrics"]["counter"] == 5

    readings = client.get(f"/devices/{device['id']}/readings")
    assert readings.status_code == 200
    assert readings.json()["data"]["pagination"]["total"] == 2


def test_live_does_not_persist_reading(client, unique_ip, monkeypatch):
    calls = {"count": 0}

    def fake_read(_self, _device):
        calls["count"] += 1
        return DeviceReading(metrics={"counter": 77})

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )

    device = _create_device(client, unique_ip)
    _bind_equipment(client, device["id"])

    live = client.get(f"/devices/{device['id']}/live")
    assert live.status_code == 200
    assert live.json()["data"]["metrics"]["counter"] == 77

    readings = client.get(f"/devices/{device['id']}/readings")
    assert readings.json()["data"]["pagination"]["total"] == 0
    assert calls["count"] == 1


def test_device_without_binding_reports_no_binding_status(client, unique_ip, monkeypatch):
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        lambda _self, _device: DeviceReading(metrics={"counter": 1}),
    )

    device = _create_device(client, unique_ip)
    detail = client.get(f"/devices/{device['id']}")
    assert detail.json()["data"]["status"] == "no_binding"
    assert detail.json()["data"]["online"] is False


def test_gauge_poll_persists_heartbeat_without_delta(client, unique_ip, monkeypatch):
    sequence = iter(
        [
            DeviceReading(metrics={"rpm": 1180.0, "temperature_c": 42.0}),
            DeviceReading(metrics={"rpm": 1180.0, "temperature_c": 42.0}),
        ]
    )

    def fake_read(_self, _device):
        return next(sequence)

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )

    device = client.post(
        "/devices",
        json={
            "name": "ESP gauge poll",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_gauge_v1",
        },
    ).json()["data"]
    _bind_equipment(client, device["id"])

    first = client.post(f"/devices/{device['id']}/poll")
    assert first.status_code == 200
    first_body = first.json()["data"]
    assert first_body["metrics"]["rpm"] == 1180.0
    assert first_body.get("deltaMetrics") in ({}, None)

    second = client.post(f"/devices/{device['id']}/poll")
    assert second.status_code == 200

    readings = client.get(f"/devices/{device['id']}/readings")
    assert readings.json()["data"]["pagination"]["total"] == 2


def test_manual_poll_restores_counter_after_hardware_power_loss(client, unique_ip, monkeypatch):
    sequence = iter(
        [
            DeviceReading(metrics={"counter": 100}),
            DeviceReading(metrics={"counter": 8}),
        ]
    )

    def fake_read(_self, _device):
        return next(sequence)

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )
    # Firmware atual sem /api/definir → restore por offset de software.
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._maybe_hardware_restore_counter",
        lambda self, device, *, previous_metrics, raw_metrics, accept_decrease=False: None,
    )

    device = _create_device(client, unique_ip)
    _bind_equipment(client, device["id"])

    client.post(f"/devices/{device['id']}/poll")
    second = client.post(f"/devices/{device['id']}/poll")
    assert second.status_code == 200
    body = second.json()["data"]
    assert body["metrics"]["counter"] == 108
    assert body["deltaMetrics"]["counter"] == 8
    assert body["meta"]["counter_restored"] is True
    assert body["meta"]["counter_restore_mode"] == "software_offset"
    assert "counter_reset" not in body["meta"]

    detail = client.get(f"/devices/{device['id']}")
    assert detail.json()["data"]["lastMetrics"] == {"counter": 108}


def test_manual_poll_hardware_set_restore(client, unique_ip, monkeypatch):
    sequence = iter(
        [
            DeviceReading(metrics={"counter": 100}),
            DeviceReading(metrics={"counter": 8}),
        ]
    )

    def fake_read(_self, _device):
        return next(sequence)

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )
    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._maybe_hardware_restore_counter",
        lambda self, device, *, previous_metrics, raw_metrics, accept_decrease=False: (
            (
                {"counter": 108, "counterRaw": 108, "counterOffset": 0},
                {
                    "counter_restored": True,
                    "counter_restore_mode": "hardware_set",
                    "counter_restore_from": 100,
                    "counter_restore_raw": 8,
                    "counter_restore_target": 108,
                },
            )
            if (not accept_decrease)
            and previous_metrics.get("counter") is not None
            and isinstance(raw_metrics.get("counter"), (int, float))
            and int(raw_metrics["counter"])
            < int(previous_metrics.get("counterRaw", previous_metrics.get("counter")))
            else None
        ),
    )

    device = _create_device(client, unique_ip)
    _bind_equipment(client, device["id"])
    client.post(f"/devices/{device['id']}/poll")
    second = client.post(f"/devices/{device['id']}/poll")
    body = second.json()["data"]
    assert body["metrics"]["counter"] == 108
    assert body["deltaMetrics"]["counter"] == 8
    assert body["meta"]["counter_restore_mode"] == "hardware_set"


def test_manual_poll_device_unreachable_returns_422(client, unique_ip, monkeypatch):
    from production_pulse_app.domain.errors import DeviceDriverError

    def fake_read(_self, _device):
        raise DeviceDriverError(
            "timeout",
            technical_detail="HTTP timeout for http://192.168.20.2/api/contador.",
        )

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )

    device = _create_device(client, unique_ip)
    _bind_equipment(client, device["id"])

    response = client.post(f"/devices/{device['id']}/poll")
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "timeout"
    assert "dispositivo" in body["error"]["message"].lower()
    assert "timeout" not in body["error"]["message"].lower()

    detail = client.get(f"/devices/{device['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["status"] == "offline"


def test_live_device_unreachable_returns_422(client, unique_ip, monkeypatch):
    from production_pulse_app.domain.errors import DeviceDriverError

    def fake_read(_self, _device):
        raise DeviceDriverError("network_error", technical_detail="HTTP request failed.")

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )

    device = _create_device(client, unique_ip)
    _bind_equipment(client, device["id"])

    response = client.get(f"/devices/{device['id']}/live")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "network_error"
