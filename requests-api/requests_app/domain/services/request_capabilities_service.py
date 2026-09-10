"""Resolve non-transition capabilities for a request detail projection.

Mirrors enforcement in file_use_cases / timeline create_comment — presentation only.
"""

from __future__ import annotations

from typing import Any

from requests_app.domain.entities import Actor, Request


def resolve_request_capabilities(
    request: Request,
    *,
    actor: Actor,
    workflow: dict[str, Any] | None,
) -> dict[str, bool]:
    is_owner = request.created_by_user_id == actor.user_id
    can_view = bool(
        is_owner or actor.has_view_all or actor.has_process or actor.has_manage
    )
    terminal = _is_terminal(request, workflow)
    can_staff = bool(actor.has_process or actor.has_manage)

    return {
        # create_comment: any viewer of the request
        "can_comment": can_view,
        # upload attachment: owner|process|manage and not terminal
        "can_upload_attachment": bool(
            (is_owner or can_staff) and not terminal
        ),
        # upload artifact: process|manage (no terminal check in use case today)
        "can_upload_artifact": can_staff,
    }


def _is_terminal(request: Request, workflow: dict[str, Any] | None) -> bool:
    terminals = set((workflow or {}).get("terminalStatuses") or [])
    return request.status in terminals
