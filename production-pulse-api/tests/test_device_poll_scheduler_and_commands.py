import asyncio
from uuid import uuid4

from production_pulse_app.application.services.device_poll_scheduler_service import (
    DevicePollSchedulerService,
)
from production_pulse_app.domain.models.device_reading import CommandResult


def test_tick_skips_device_already_in_flight():
    calls: list = []

    class _PollService:
        def poll_and_persist(self, device_id, *, source="poll"):
            calls.append(device_id)

    scheduler = DevicePollSchedulerService(poll_service=_PollService())
    device_id = uuid4()
    device = {"id": device_id, "poll_interval_ms": 30_000}
    scheduler._devices.list_due_for_scheduled_poll = lambda limit=50: [device]
    scheduler._in_flight.add(device_id)

    asyncio.run(scheduler._tick())
    assert calls == []


def test_gauge_increment_command_rejected(client, unique_ip):
    device = client.post(
        "/devices",
        json={
            "name": "ESP gauge",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_gauge_v1",
        },
    ).json()["data"]

    response = client.post(f"/devices/{device['id']}/commands/increment")
    assert response.status_code == 422
    assert "não suportado" in response.json()["error"]["message"].lower()


def test_counter_reset_command_is_audited(client, unique_ip, monkeypatch):
    from production_pulse_app.domain.models.device_reading import DeviceReading

    device = client.post(
        "/devices",
        json={
            "name": "ESP comando",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    ).json()["data"]

    client.put(
        f"/devices/{device['id']}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Prensa comando"},
    )

    class _Driver:
        driver_key = "esp8266_counter_v1"

        def execute(self, _device, command_key, *, payload=None):
            assert command_key == "reset"
            return CommandResult(success=True, metrics={"counter": 0}, response_payload={"contador": 0})

    class _Registry:
        def build_capabilities(self, _driver_key):
            return {"commands": ["increment", "decrement", "reset"]}

        def get_implementation(self, _driver_key):
            return _Driver()

    import production_pulse_app.interface.http.routes.device_routes as routes_module

    monkeypatch.setattr(routes_module._command_service, "_registry", _Registry())

    response = client.post(f"/devices/{device['id']}/commands/reset")
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["success"] is True
    assert body["metrics"]["counter"] == 0
    assert body["readingId"] is not None

    audit = client.get(f"/devices/{device['id']}/commands")
    assert audit.status_code == 200
    items = audit.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["commandKey"] == "reset"
    assert items[0]["success"] is True
