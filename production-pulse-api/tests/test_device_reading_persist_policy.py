from datetime import datetime, timedelta, timezone

from production_pulse_app.domain.services.device_reading_persist_policy_service import (
    decide_persist_reading,
    metrics_changed_beyond_deadband,
)
from production_pulse_app.infrastructure.content.telemetry_persistence_content_service import (
    heartbeat_ms,
    reset_telemetry_persistence_catalog_cache,
)


def setup_function() -> None:
    reset_telemetry_persistence_catalog_cache()


def test_counter_deadband_requires_at_least_one_unit():
    assert not metrics_changed_beyond_deadband(
        role_key="pulse_counter",
        previous_metrics={"counter": 10},
        new_metrics={"counter": 10},
    )
    assert metrics_changed_beyond_deadband(
        role_key="pulse_counter",
        previous_metrics={"counter": 10},
        new_metrics={"counter": 11},
    )


def test_gauge_deadband_rpm():
    assert not metrics_changed_beyond_deadband(
        role_key="process_gauge",
        previous_metrics={"rpm": 1000, "temperature_c": 40},
        new_metrics={"rpm": 1003, "temperature_c": 40},
    )
    assert metrics_changed_beyond_deadband(
        role_key="process_gauge",
        previous_metrics={"rpm": 1000, "temperature_c": 40},
        new_metrics={"rpm": 1006, "temperature_c": 40},
    )


def test_decide_command_always_persists():
    decision = decide_persist_reading(
        source="command",
        role_key="pulse_counter",
        previous_metrics={"counter": 10},
        new_metrics={"counter": 10},
        last_persisted_at=datetime.now(timezone.utc),
    )
    assert decision.should_persist is True
    assert decision.reason == "command"


def test_decide_skip_unchanged_within_heartbeat():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    decision = decide_persist_reading(
        source="poll",
        role_key="pulse_counter",
        previous_metrics={"counter": 130},
        new_metrics={"counter": 130},
        last_persisted_at=now - timedelta(seconds=5),
        now=now,
    )
    assert decision.should_persist is False
    assert decision.reason == "skipped_unchanged"


def test_decide_heartbeat_after_idle():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    idle = timedelta(milliseconds=heartbeat_ms("pulse_counter") + 100)
    decision = decide_persist_reading(
        source="poll",
        role_key="pulse_counter",
        previous_metrics={"counter": 130},
        new_metrics={"counter": 130},
        last_persisted_at=now - idle,
        now=now,
    )
    assert decision.should_persist is True
    assert decision.reason == "heartbeat"


def test_decide_first_reading_and_restore_meta():
    assert (
        decide_persist_reading(
            source="poll",
            role_key="pulse_counter",
            previous_metrics={},
            new_metrics={"counter": 1},
            last_persisted_at=None,
        ).reason
        == "first"
    )
    decision = decide_persist_reading(
        source="poll",
        role_key="pulse_counter",
        previous_metrics={"counter": 100},
        new_metrics={"counter": 100},
        last_persisted_at=datetime.now(timezone.utc),
        meta={"counter_restored": True},
    )
    assert decision.should_persist is True
    assert decision.reason == "restore_or_reset"
