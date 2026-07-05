from __future__ import annotations

from typing import Any

from tv_app.application.services.presentation_realtime_hub import presentation_realtime_hub


def notify_presentation_changed(
    *,
    playlist_id: str,
    reason: str,
    revision: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "type": "presentation_updated",
        "reason": reason,
    }
    if revision:
        payload["revision"] = revision
    presentation_realtime_hub.schedule_broadcast(str(playlist_id), payload)
