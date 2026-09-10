"""Resolve non-transition capabilities for a request detail projection.

Mirrors enforcement in file_use_cases / timeline create_comment — presentation only.

Attachment manage on the detail page is only when the request is returned
(`needs_information`) and the actor is the owner. Create-flow bootstrap upload
(status `submitted`) is allowed by the use case but is not exposed here so the
detail UI stays read-only until a return.
"""

from __future__ import annotations

from typing import Any

from requests_app.domain.entities import Actor, Request

# Detail presentation: owner may add/remove attachments only when returned.
ATTACHMENT_MANAGE_STATUS = "needs_information"


def _file_immutable_statuses(workflow: dict[str, Any] | None) -> set[str]:
    """Statuses where artifacts/attachments must not be mutated (workflow-driven)."""
    terminals = {
        str(item).strip()
        for item in ((workflow or {}).get("terminalStatuses") or [])
        if str(item).strip()
    }
    locked = {
        str(item).strip()
        for item in ((workflow or {}).get("fileImmutableStatuses") or [])
        if str(item).strip()
    }
    return terminals | locked


def _terminal_statuses(workflow: dict[str, Any] | None) -> set[str]:
    return {
        str(item).strip()
        for item in ((workflow or {}).get("terminalStatuses") or [])
        if str(item).strip()
    }


def resolve_request_capabilities(
    request: Request,
    *,
    actor: Actor,
    workflow: dict[str, Any] | None,
) -> dict[str, bool]:
    immutable = _file_immutable_statuses(workflow)
    files_locked = request.status in immutable
    is_terminal = request.status in _terminal_statuses(workflow)
    is_owner = request.created_by_user_id == actor.user_id
    can_view = bool(
        is_owner or actor.has_view_all or actor.has_process or actor.has_manage
    )
    can_staff = bool(actor.has_process or actor.has_manage)
    can_manage_attachments = bool(
        (not files_locked)
        and is_owner
        and request.status == ATTACHMENT_MANAGE_STATUS
    )

    return {
        # create/update comment: viewers while request is not terminal
        "can_comment": bool(can_view and not is_terminal),
        # terminal request — conversation read-only for everyone (banner copy)
        "conversation_frozen": bool(is_terminal),
        # detail manage (upload + delete): owner + needs_information only
        "can_upload_attachment": can_manage_attachments,
        # upload artifact: process|manage and not terminal / fileImmutableStatuses
        "can_upload_artifact": bool(can_staff and not files_locked),
    }
