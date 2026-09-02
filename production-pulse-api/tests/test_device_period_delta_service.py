from datetime import datetime, timezone
from uuid import uuid4

from production_pulse_app.application.services.device_period_delta_service import (
    DevicePeriodDeltaService,
)


class _FakeReadingRepository:
    def __init__(self, day_totals: dict, shift_totals: dict) -> None:
        self._day_totals = day_totals
        self._shift_totals = shift_totals
        self._call_index = 0

    def sum_delta_metric_for_devices(
        self,
        device_ids,
        *,
        metric_key,
        recorded_from,
        recorded_to,
    ):
        self._call_index += 1
        if self._call_index == 1:
            return dict(self._day_totals)
        return dict(self._shift_totals)


def test_build_period_deltas_for_counter_devices_only():
    counter_id = uuid4()
    gauge_id = uuid4()
    rows = [
        {"id": counter_id, "role_key": "pulse_counter"},
        {"id": gauge_id, "role_key": "process_gauge"},
    ]
    service = DevicePeriodDeltaService(
        reading_repository=_FakeReadingRepository(
            day_totals={counter_id: 42},
            shift_totals={counter_id: 7},
        )
    )

    result = service.build_period_deltas_for_devices(
        rows,
        now=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert counter_id in result
    assert result[counter_id]["day"]["counter"] == 42
    assert result[counter_id]["shift"]["counter"] == 7
    assert gauge_id not in result


def test_aggregate_branch_counter_deltas_sums_bound_counters():
    counter_a = uuid4()
    counter_b = uuid4()
    rows = [
        {"id": counter_a, "role_key": "pulse_counter"},
        {"id": counter_b, "role_key": "pulse_counter"},
    ]
    service = DevicePeriodDeltaService(
        reading_repository=_FakeReadingRepository(
            day_totals={counter_a: 10, counter_b: 5},
            shift_totals={counter_a: 3, counter_b: 2},
        )
    )

    payload = service.aggregate_branch_counter_deltas(
        rows,
        bound_device_ids={counter_a, counter_b},
        now=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
    )

    assert payload == {"day": {"counter": 15}, "shift": {"counter": 5}}
