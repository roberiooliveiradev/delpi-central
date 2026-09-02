from production_pulse_app.domain.services.device_monotonic_counter_continuity_service import (
    COUNTER_OFFSET_KEY,
    COUNTER_RAW_KEY,
    apply_monotonic_continuity,
    public_metrics,
)


def test_continuity_first_reading_seeds_raw_and_offset():
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics={},
        raw_metrics={"counter": 42},
    )
    assert metrics["counter"] == 42
    assert metrics[COUNTER_RAW_KEY] == 42
    assert metrics[COUNTER_OFFSET_KEY] == 0
    assert meta == {}
    assert public_metrics(metrics) == {"counter": 42}


def test_continuity_increments_with_existing_offset():
    previous = {"counter": 105, COUNTER_RAW_KEY: 5, COUNTER_OFFSET_KEY: 100}
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics=previous,
        raw_metrics={"counter": 8},
    )
    assert metrics["counter"] == 108
    assert metrics[COUNTER_RAW_KEY] == 8
    assert metrics[COUNTER_OFFSET_KEY] == 100
    assert meta == {}


def test_continuity_restores_software_offset_after_power_loss():
    previous = {"counter": 100, COUNTER_RAW_KEY: 100, COUNTER_OFFSET_KEY: 0}
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics=previous,
        raw_metrics={"counter": 8},
    )
    assert metrics["counter"] == 108
    assert metrics[COUNTER_RAW_KEY] == 8
    assert metrics[COUNTER_OFFSET_KEY] == 100
    assert meta["counter_restored"] is True
    assert meta["counter_restore_mode"] == "software_offset"


def test_continuity_clear_offsets_for_absolute_set():
    previous = {"counter": 108, COUNTER_RAW_KEY: 8, COUNTER_OFFSET_KEY: 100}
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics=previous,
        raw_metrics={"counter": 50},
        clear_offsets=True,
    )
    assert metrics["counter"] == 50
    assert metrics[COUNTER_RAW_KEY] == 50
    assert metrics[COUNTER_OFFSET_KEY] == 0
    assert meta == {}
