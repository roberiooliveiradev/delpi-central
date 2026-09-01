from production_pulse_app.domain.services.device_reading_delta_service import compute_delta_metrics


def test_delta_increments_monotonic_counter():
    delta, meta = compute_delta_metrics(
        driver_key="esp8266_counter_v1",
        previous_metrics={"counter": 10},
        new_metrics={"counter": 15},
    )
    assert delta == {"counter": 5}
    assert meta == {}


def test_delta_first_reading_is_zero():
    delta, meta = compute_delta_metrics(
        driver_key="esp8266_counter_v1",
        previous_metrics={},
        new_metrics={"counter": 42},
    )
    assert delta == {"counter": 0}
    assert meta == {}


def test_delta_detects_counter_reset():
    delta, meta = compute_delta_metrics(
        driver_key="esp8266_counter_v1",
        previous_metrics={"counter": 100},
        new_metrics={"counter": 8},
    )
    assert delta == {"counter": 8}
    assert meta == {"counter_reset": True}
