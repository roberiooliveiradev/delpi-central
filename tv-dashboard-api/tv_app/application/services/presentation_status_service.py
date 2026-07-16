from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tv_app.application.services.tv_dashboard_content_service import heartbeat_interval_sec


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def build_presentation_status(
    playlist: dict[str, Any],
    *,
    content_revision: str | None = None,
) -> dict[str, Any]:
    interval = heartbeat_interval_sec()
    stale_after_sec = interval * 2
    last_at = _parse_iso(playlist.get("lastPresentedAt"))
    now = datetime.now(timezone.utc)

    if last_at is None:
        status = "never"
        online = False
        seconds_since = None
    else:
        seconds_since = max(0, int((now - last_at).total_seconds()))
        online = seconds_since <= stale_after_sec
        status = "online" if online else "offline"

    payload: dict[str, Any] = {
        "status": status,
        "online": online,
        "lastPresentedAt": playlist.get("lastPresentedAt"),
        "viewCount": playlist.get("viewCount") or 0,
        "heartbeatIntervalSec": interval,
        "staleAfterSec": stale_after_sec,
        "secondsSinceLastPresentation": seconds_since,
        "isActive": bool(playlist.get("isActive")),
    }
    if content_revision:
        payload["contentRevision"] = content_revision
    return payload
