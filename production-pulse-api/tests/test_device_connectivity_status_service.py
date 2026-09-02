from datetime import datetime, timedelta, timezone

from production_pulse_app.domain.services.device_connectivity_status_service import (
    grace_seconds_for_device,
    resolve_connectivity_status,
)


def _device(**overrides):
    base = {
        "enabled": True,
        "poll_interval_ms": 30_000,
        "last_seen_at": None,
    }
    base.update(overrides)
    return base


def test_grace_seconds_clamps_to_min_and_max():
    assert grace_seconds_for_device(_device(poll_interval_ms=5_000)) == 60
    assert grace_seconds_for_device(_device(poll_interval_ms=30_000)) == 60
    assert grace_seconds_for_device(_device(poll_interval_ms=400_000)) == 600


def test_status_disabled():
    result = resolve_connectivity_status(_device(enabled=False), has_binding=True)
    assert result["status"] == "disabled"
    assert result["online"] is False


def test_status_no_binding():
    result = resolve_connectivity_status(_device(), has_binding=False)
    assert result["status"] == "no_binding"
    assert result["online"] is False


def test_status_offline_without_last_seen():
    result = resolve_connectivity_status(_device(), has_binding=True)
    assert result["status"] == "offline"
    assert result["online"] is False


def test_status_online_within_grace_window():
    now = datetime.now(timezone.utc)
    device = _device(last_seen_at=now - timedelta(seconds=30))
    result = resolve_connectivity_status(device, has_binding=True, now=now)
    assert result["status"] == "online"
    assert result["online"] is True


def test_status_offline_outside_grace_window():
    now = datetime.now(timezone.utc)
    device = _device(last_seen_at=now - timedelta(seconds=120))
    result = resolve_connectivity_status(device, has_binding=True, now=now)
    assert result["status"] == "offline"
    assert result["online"] is False
