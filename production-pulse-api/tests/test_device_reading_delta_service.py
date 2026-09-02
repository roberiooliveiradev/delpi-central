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


def test_delta_detects_decrease_with_signed_delta():
    delta, meta = compute_delta_metrics(
        driver_key="esp8266_counter_v1",
        previous_metrics={"counter": 100},
        new_metrics={"counter": 99},
    )
    assert delta == {"counter": -1}
    assert meta == {"counter_decreased": True}


def test_delta_large_drop_is_signed_not_reset_rewrite():
    # Power-loss já normalizado na continuidade; aqui só o delta lógico.
    delta, meta = compute_delta_metrics(
        driver_key="esp8266_counter_v1",
        previous_metrics={"counter": 100},
        new_metrics={"counter": 108},
    )
    assert delta == {"counter": 8}
    assert meta == {}
