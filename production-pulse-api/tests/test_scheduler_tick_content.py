from production_pulse_app.application.services.device_poll_scheduler_service import (
    resolve_scheduler_tick_seconds,
)
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    live_ui_refresh_min_ms,
    scheduler_tick_ms,
)


def test_scheduler_tick_ms_matches_content():
    assert scheduler_tick_ms() == 100
    assert resolve_scheduler_tick_seconds() == 0.1


def test_live_ui_refresh_min_ms_matches_content():
    assert live_ui_refresh_min_ms() == 50
