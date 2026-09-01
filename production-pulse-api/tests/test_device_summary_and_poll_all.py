from production_pulse_app.domain.models.device_reading import CommandResult


def _create_bound_device(client, unique_ip: str, *, label: str = "Motor summary"):
    device = client.post(
        "/devices",
        json={
            "name": "ESP summary",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    ).json()["data"]
    client.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": label},
    )
    return device


def test_summary_counts_bound_and_unbound(client, unique_ip):
    bound = _create_bound_device(client, unique_ip)
    client.post(
        "/devices",
        json={
            "name": "ESP rascunho",
            "branch": "01",
            "ipAddress": f"192.168.20.{180 + int(unique_ip.split('.')[-1]) % 50}",
            "driverKey": "esp8266_counter_v1",
        },
    )

    response = client.get("/summary", params={"branch": "01"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    assert data["withoutBinding"] == 1
    assert data["branch"] == "01"
    assert bound["id"]


def test_viewer_can_read_summary(client_factory, unique_ip):
    admin = client_factory(["production-pulse.admin"])
    _create_bound_device(admin, unique_ip)

    viewer = client_factory(
        [
            "production-pulse.devices.view",
            "production-pulse.view.filial-01",
        ],
    )
    response = viewer.get("/summary", params={"branch": "01"})
    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1


def test_poll_all_requires_manage(client_factory, unique_ip, monkeypatch):
    admin = client_factory(["production-pulse.admin"])
    device = _create_bound_device(admin, unique_ip)

    class _FakeDriver:
        driver_key = "esp8266_counter_v1"

        def read(self, device):
            from production_pulse_app.domain.models.device_reading import DeviceReading
            from datetime import datetime, timezone

            return DeviceReading(metrics={"counter": 3}, recorded_at=datetime.now(timezone.utc))

    from production_pulse_app.interface.http.routes import device_routes as routes_module

    monkeypatch.setattr(
        routes_module._poll_service._registry,
        "get_implementation",
        lambda key: _FakeDriver(),
    )

    viewer = client_factory(
        [
            "production-pulse.devices.view",
            "production-pulse.view.filial-01",
        ],
    )
    assert viewer.post("/devices/poll-all", params={"branch": "01"}).status_code == 403

    manager = client_factory(
        [
            "production-pulse.devices.manage",
            "production-pulse.view.filial-01",
        ],
    )
    response = manager.post("/devices/poll-all", params={"branch": "01"})
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["polled"] == 1
    assert payload["succeeded"] == 1
    assert payload["results"][0]["deviceId"] == device["id"]


def test_devices_command_permission_allows_admin_route(client_factory, unique_ip, monkeypatch):
    admin = client_factory(["production-pulse.admin"])
    device = _create_bound_device(admin, unique_ip)

    commander = client_factory(
        [
            "production-pulse.devices.command",
            "production-pulse.view.filial-01",
        ],
    )

    class _FakeDriver:
        driver_key = "esp8266_counter_v1"

        def execute(self, device, command_key, payload=None):
            return CommandResult(success=True, metrics={"counter": 0})

    from production_pulse_app.interface.http.routes import device_routes as routes_module

    monkeypatch.setattr(
        routes_module._command_service._registry,
        "get_implementation",
        lambda key: _FakeDriver(),
    )

    response = commander.post(f"/devices/{device['id']}/commands/reset")
    assert response.status_code == 200
