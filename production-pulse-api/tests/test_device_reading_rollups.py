from datetime import datetime, timezone

from production_pulse_app.domain.models.device_reading import DeviceReading



def _create_device(client, unique_ip: str):
    response = client.post(
        "/devices",
        json={
            "name": "ESP rollup",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def _bind(client, device_id: str):
    client.put(
        f"/devices/{device_id}/binding",
        json={"anchorType": "equipment", "equipmentLabel": "Motor rollup"},
    )


def test_poll_builds_hour_rollup_and_list_resolution(client, unique_ip, monkeypatch):
    sequence = iter(
        [
            DeviceReading(
                metrics={"counter": 10},
                recorded_at=datetime(2026, 9, 2, 14, 10, tzinfo=timezone.utc),
            ),
            DeviceReading(
                metrics={"counter": 15},
                recorded_at=datetime(2026, 9, 2, 14, 40, tzinfo=timezone.utc),
            ),
        ]
    )

    def fake_read(_self, _device):
        return next(sequence)

    monkeypatch.setattr(
        "production_pulse_app.application.services.device_poll_service.DevicePollService._read_from_driver",
        fake_read,
    )

    device = _create_device(client, unique_ip)
    _bind(client, device["id"])

    assert client.post(f"/devices/{device['id']}/poll").status_code == 200
    assert client.post(f"/devices/{device['id']}/poll").status_code == 200

    hour = client.get(
        f"/devices/{device['id']}/readings",
        params={"resolution": "hour", "pageSize": 50},
    )
    assert hour.status_code == 200
    body = hour.json()["data"]
    assert body["resolution"] == "hour"
    assert body["pagination"]["total"] == 1
    item = body["items"][0]
    assert item["source"] == "rollup"
    assert item["metrics"]["counter"] == 15
    assert item["deltaMetrics"]["counter"] == 5
    assert item["meta"]["samples"] == 2
    assert item["meta"]["resolution"] == "hour"

    day = client.get(
        f"/devices/{device['id']}/readings",
        params={"resolution": "day", "pageSize": 50},
    )
    assert day.status_code == 200
    assert day.json()["data"]["pagination"]["total"] == 1
    assert day.json()["data"]["items"][0]["metrics"]["counter"] == 15

