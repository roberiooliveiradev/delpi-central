from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from production_pulse_app.application.services.integration_device_snapshot_service import (
    IntegrationDeviceSnapshotService,
    device_row_to_integration_snapshot,
)
from production_pulse_app.domain.services.device_monotonic_counter_continuity_service import (
    COUNTER_EPOCH_KEY,
    COUNTER_OFFSET_KEY,
    COUNTER_RAW_KEY,
)


def test_snapshot_exposes_counter_and_epoch_not_internal_raw():
    device_id = uuid4()
    row = {
        "id": device_id,
        "branch": "01",
        "name": "Prensa A",
        "role_key": "pulse_counter",
        "driver_key": "esp8266_counter_v1",
        "work_center_code": "CT01",
        "placement_key": "wc:01:CT01",
        "enabled": True,
        "poll_interval_ms": 1000,
        "last_seen_at": datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
        "last_poll_attempt_at": datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc),
        "last_error": None,
        "last_metrics": {
            "counter": 150,
            COUNTER_RAW_KEY: 50,
            COUNTER_OFFSET_KEY: 100,
            COUNTER_EPOCH_KEY: 2,
        },
    }
    snap = device_row_to_integration_snapshot(row)
    assert snap["deviceId"] == str(device_id)
    assert snap["counter"] == 150
    assert snap["counterEpoch"] == 2
    assert snap["workCenterCode"] == "CT01"
    assert "counterRaw" not in snap
    assert "counterOffset" not in snap


def test_list_by_work_center_filters_role(monkeypatch):
    class FakePlacement:
        def list_bound_devices(self, **kwargs):
            assert kwargs["placement_key"] == "wc:01:CT99"
            return [
                {
                    "id": uuid4(),
                    "branch": "01",
                    "name": "Counter",
                    "role_key": "pulse_counter",
                    "driver_key": "esp8266_counter_v1",
                    "work_center_code": "CT99",
                    "placement_key": "wc:01:CT99",
                    "enabled": True,
                    "poll_interval_ms": 500,
                    "last_seen_at": datetime.now(timezone.utc),
                    "last_poll_attempt_at": datetime.now(timezone.utc),
                    "last_error": None,
                    "last_metrics": {"counter": 10, COUNTER_EPOCH_KEY: 0},
                },
                {
                    "id": uuid4(),
                    "branch": "01",
                    "name": "Gauge",
                    "role_key": "process_gauge",
                    "driver_key": "esp8266_gauge_v1",
                    "work_center_code": "CT99",
                    "placement_key": "wc:01:CT99",
                    "enabled": True,
                    "poll_interval_ms": 500,
                    "last_seen_at": datetime.now(timezone.utc),
                    "last_poll_attempt_at": datetime.now(timezone.utc),
                    "last_error": None,
                    "last_metrics": {"rpm": 100},
                },
            ]

    service = IntegrationDeviceSnapshotService(placement_repository=FakePlacement())
    payload = service.list_by_work_center(branch="01", work_center="CT99")
    assert payload["workCenter"] == "CT99"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["roleKey"] == "pulse_counter"
    assert payload["items"][0]["counter"] == 10


def test_list_by_work_center_rejects_bad_branch():
    service = IntegrationDeviceSnapshotService(placement_repository=object())
    try:
        service.list_by_work_center(branch="99", work_center="CT01")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Filial" in str(exc)


def _bound_row(work_center: str, role_key: str = "pulse_counter") -> dict:
    return {
        "id": uuid4(),
        "branch": "01",
        "name": f"Counter {work_center}",
        "role_key": role_key,
        "driver_key": "esp8266_counter_v1",
        "work_center_code": work_center,
        "placement_key": f"wc:01:{work_center}",
        "enabled": True,
        "poll_interval_ms": 500,
        "last_seen_at": datetime.now(timezone.utc),
        "last_poll_attempt_at": datetime.now(timezone.utc),
        "last_error": None,
        "last_metrics": {"counter": 7, COUNTER_EPOCH_KEY: 1},
    }


def test_list_counters_by_branch_enumerates_all_bound_centers():
    class FakePlacement:
        def list_bound_devices(self, **kwargs):
            # Enumeracao por filial: sem placement_key — um GET cobre a filial.
            assert kwargs["branch"] == "01"
            assert kwargs["anchor_type"] == "work_center"
            assert "placement_key" not in kwargs
            return [
                _bound_row("CT01"),
                _bound_row("CT02"),
                _bound_row("CT03", role_key="process_gauge"),
            ]

    service = IntegrationDeviceSnapshotService(placement_repository=FakePlacement())
    payload = service.list_counters_by_branch(branch="01")
    assert payload["branch"] == "01"
    assert [item["workCenterCode"] for item in payload["items"]] == ["CT01", "CT02"]
    assert all(item["roleKey"] == "pulse_counter" for item in payload["items"])


def test_list_counters_by_branch_rejects_bad_branch():
    service = IntegrationDeviceSnapshotService(placement_repository=object())
    try:
        service.list_counters_by_branch(branch="99")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Filial" in str(exc)
