from datetime import datetime, timedelta, timezone
from uuid import UUID

from production_pulse_app.application.services.device_reading_retention_service import (
    DeviceReadingRetentionService,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_reading_repository import (
    PostgresDeviceReadingRepository,
)


def _create_device(client, unique_ip: str):
    response = client.post(
        "/devices",
        json={
            "name": "ESP retention",
            "branch": "01",
            "ipAddress": unique_ip,
            "driverKey": "esp8266_counter_v1",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_purge_expired_raw_removes_only_old_rows(client, unique_ip):
    device = _create_device(client, unique_ip)
    device_id = UUID(device["id"])
    repo = PostgresDeviceReadingRepository()
    now = datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc)

    repo.insert(
        device_id,
        metrics={"counter": 1},
        delta_metrics={"counter": 0},
        meta={},
        source="poll",
        recorded_at=now - timedelta(days=120),
    )
    repo.insert(
        device_id,
        metrics={"counter": 2},
        delta_metrics={"counter": 1},
        meta={},
        source="poll",
        recorded_at=now - timedelta(days=1),
    )

    service = DeviceReadingRetentionService(reading_repository=repo)
    result = service.purge_expired_raw(now=now, retention_days=90, batch_size=100)

    assert result["deleted"] == 1
    assert result["retentionDays"] == 90
    remaining = client.get(f"/devices/{device['id']}/readings")
    assert remaining.status_code == 200
    assert remaining.json()["data"]["pagination"]["total"] == 1
    assert remaining.json()["data"]["items"][0]["metrics"]["counter"] == 2
