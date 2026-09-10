"""User-facing copy for WebSocket floating notices (never raw status codes)."""

from __future__ import annotations

from typing import Any

from requests_app.domain.services.creator_portal_notification_policy import (
    resolve_creator_gate_copy,
)


def build_realtime_transition_notification(
    *,
    workflow: dict[str, Any] | None,
    to_status: str,
    request_number: str,
    actor_name: str,
) -> dict[str, str]:
    title, message, notif_type = resolve_creator_gate_copy(
        workflow=workflow,
        to_status=to_status,
        request_number=request_number,
        actor_name=actor_name,
    )
    variant = (
        notif_type
        if notif_type in {"info", "success", "warning", "error"}
        else "info"
    )
    return {"title": title, "message": message, "variant": variant}
