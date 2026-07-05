from datetime import datetime, timezone

from tv_app.application.services.presentation_status_service import build_presentation_status


def test_status_never_presented():
    result = build_presentation_status({"viewCount": 0, "isActive": True})
    assert result["status"] == "never"
    assert result["online"] is False


def test_status_online_recent():
    now = datetime.now(timezone.utc).isoformat()
    result = build_presentation_status(
        {"lastPresentedAt": now, "viewCount": 3, "isActive": True},
    )
    assert result["status"] == "online"
    assert result["online"] is True


def test_status_offline_stale():
    old = datetime(2020, 1, 1, tzinfo=timezone.utc).isoformat()
    result = build_presentation_status(
        {"lastPresentedAt": old, "viewCount": 10, "isActive": True},
    )
    assert result["status"] == "offline"
    assert result["online"] is False
