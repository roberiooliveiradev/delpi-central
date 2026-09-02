from datetime import datetime, timezone

from production_pulse_app.application.services.device_reading_rollup_service import (
    _sum_delta_maps,
    rollup_row_to_api,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_reading_rollup_repository import (
    truncate_bucket_start,
)


def test_truncate_bucket_hour_and_day():
    when = datetime(2026, 9, 2, 14, 37, 12, tzinfo=timezone.utc)
    assert truncate_bucket_start(when, "hour") == datetime(
        2026, 9, 2, 14, 0, 0, tzinfo=timezone.utc
    )
    assert truncate_bucket_start(when, "day") == datetime(
        2026, 9, 2, 0, 0, 0, tzinfo=timezone.utc
    )


def test_sum_delta_maps_integers():
    assert _sum_delta_maps({"counter": 2}, {"counter": 3}) == {"counter": 5}
    assert _sum_delta_maps(None, {"rpm": 1.5}) == {"rpm": 1.5}


def test_rollup_row_to_api_shape():
    bucket = datetime(2026, 9, 2, 14, 0, tzinfo=timezone.utc)
    payload = rollup_row_to_api(
        {
            "id": 9,
            "device_id": "11111111-1111-1111-1111-111111111111",
            "bucket_start": bucket,
            "resolution": "hour",
            "metrics": {"counter": 15},
            "delta_metrics": {"counter": 5},
            "samples": 2,
            "updated_at": bucket,
        }
    )
    assert payload["id"] == "rollup:hour:9"
    assert payload["source"] == "rollup"
    assert payload["meta"]["samples"] == 2
    assert payload["recordedAt"] == bucket
