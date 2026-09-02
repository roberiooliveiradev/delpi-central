from production_pulse_app.domain.services.device_monotonic_counter_continuity_service import (
    COUNTER_OFFSET_KEY,
    COUNTER_RAW_KEY,
    apply_monotonic_continuity,
    intentional_decrease_command_grace_ms,
    intentional_decrease_command_keys,
    is_unexplained_counter_drop,
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
    assert meta["counter_restore_reason"] == "unexplained_drop"


def test_continuity_small_unexplained_drop_also_restores():
    """Sem provenance de comando, queda de 1 também é power-loss (não usa teto 50)."""
    previous = {"counter": 30, COUNTER_RAW_KEY: 30, COUNTER_OFFSET_KEY: 0}
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics=previous,
        raw_metrics={"counter": 0},
    )
    assert metrics["counter"] == 30
    assert metrics[COUNTER_RAW_KEY] == 0
    assert metrics[COUNTER_OFFSET_KEY] == 30
    assert meta["counter_restored"] is True


def test_continuity_accept_decrease_flag_skips_power_loss():
    previous = {"counter": 100, COUNTER_RAW_KEY: 100, COUNTER_OFFSET_KEY: 0}
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics=previous,
        raw_metrics={"counter": 8},
        accept_decrease=True,
    )
    assert metrics["counter"] == 8
    assert meta.get("counter_decrease_accepted") is True
    assert meta.get("counter_decrease_provenance") == "recent_command"
    assert "counter_restored" not in meta


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


def test_unexplained_drop_helper():
    assert is_unexplained_counter_drop(100, 99) is True
    assert is_unexplained_counter_drop(100, 8) is True
    assert is_unexplained_counter_drop(100, 100) is False
    assert is_unexplained_counter_drop(100, 101) is False


def test_intentional_decrease_config_from_driver():
    assert "decrement" in intentional_decrease_command_keys("esp8266_counter_v1")
    assert intentional_decrease_command_grace_ms("esp8266_counter_v1") == 15_000


def test_continuity_floors_negative_counter():
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics={"counter": 0, COUNTER_RAW_KEY: 0, COUNTER_OFFSET_KEY: 0},
        raw_metrics={"counter": -3},
        accept_decrease=True,
    )
    assert metrics["counter"] == 0
    assert metrics[COUNTER_RAW_KEY] == 0
    assert metrics[COUNTER_OFFSET_KEY] == 0
    assert meta["counter_floored"] is True
    assert public_metrics(metrics) == {"counter": 0}


def test_continuity_floors_negative_on_first_reading():
    metrics, meta = apply_monotonic_continuity(
        driver_key="esp8266_counter_v1",
        previous_metrics={},
        raw_metrics={"counter": -1},
    )
    assert metrics["counter"] == 0
    assert meta["counter_floored"] is True
