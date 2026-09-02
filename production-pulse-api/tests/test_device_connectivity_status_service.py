from datetime import datetime, timedelta, timezone

from production_pulse_app.domain.services.device_connectivity_status_service import (
    grace_ms_for_device,
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


def test_grace_follows_poll_interval_with_content_floor():
    # 500 ms × 2 = 1000 → piso content 2000 ms → 2 s
    assert grace_ms_for_device(_device(poll_interval_ms=500)) == 2_000
    assert grace_seconds_for_device(_device(poll_interval_ms=500)) == 2
    # 5 s × 2 = 10 s
    assert grace_seconds_for_device(_device(poll_interval_ms=5_000)) == 10
    # 30 s × 2 = 60 s
    assert grace_seconds_for_device(_device(poll_interval_ms=30_000)) == 60
    # acima do max content
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
    device = _device(poll_interval_ms=500, last_seen_at=now - timedelta(milliseconds=800))
    result = resolve_connectivity_status(device, has_binding=True, now=now)
    assert result["status"] == "online"
    assert result["online"] is True
    assert result["graceMs"] == 2_000


def test_status_offline_outside_grace_for_fast_poll():
    """Com poll 500 ms, grace ~2 s — desconexão detectada sem esperar 60 s."""
    now = datetime.now(timezone.utc)
    device = _device(poll_interval_ms=500, last_seen_at=now - timedelta(seconds=3))
    result = resolve_connectivity_status(device, has_binding=True, now=now)
    assert result["status"] == "offline"
    assert result["online"] is False


def test_status_offline_outside_grace_window():
    now = datetime.now(timezone.utc)
    device = _device(poll_interval_ms=30_000, last_seen_at=now - timedelta(seconds=120))
    result = resolve_connectivity_status(device, has_binding=True, now=now)
    assert result["status"] == "offline"
    assert result["online"] is False
