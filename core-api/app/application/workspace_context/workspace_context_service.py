# app/application/workspace_context/workspace_context_service.py
"""Resolve the authenticated user's *current* workspace context.

Statuses:
- ``active``    — exactly one fresh, active entry wins (a single open tab,
                  or one focused tab among several).
- ``ambiguous`` — multiple fresh+active entries with no foreground winner;
                  candidates are returned so the consumer can ask one
                  discriminating question instead of guessing.
- ``stale``     — entries exist but all expired (TTL exceeded).
- ``absent``    — nothing published, or publishers explicitly deactivated.

``active`` on an entry means "workspace open" — NOT "tab focused". A user
chatting with an assistant in another window keeps their context ACTIVE.
``focused`` is only recency evidence for ambiguity resolution.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.application.workspace_context.workspace_context_contract import (
    WorkspaceContextPayload,
)
from app.application.workspace_context.workspace_context_store import (
    WorkspaceContextEntry,
    get_workspace_context_store,
)

STATUS_ACTIVE = "active"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_STALE = "stale"
STATUS_ABSENT = "absent"


def _serialize(entry: WorkspaceContextEntry) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    out = entry.as_dict()
    out["age_seconds"] = max(0, int((now - entry.updated_at).total_seconds()))
    return out


class WorkspaceContextService:
    def __init__(self, store=None):
        self._store = store or get_workspace_context_store()

    def publish(self, *, user_id: str, payload: WorkspaceContextPayload) -> dict[str, Any]:
        entry = self._store.put(user_id=str(user_id), payload=payload)
        return {"status": "published", "updated_at": entry.updated_at.isoformat()}

    def unpublish(self, *, user_id: str, client_instance_id: str) -> dict[str, Any]:
        removed = self._store.delete(
            user_id=str(user_id), client_instance_id=str(client_instance_id)
        )
        return {"status": "removed" if removed else "absent"}

    def resolve(self, *, user_id: str, app_id: str | None = None) -> dict[str, Any]:
        entries = self._store.list_for_user(user_id=str(user_id), fresh_only=True)
        if app_id:
            entries = [e for e in entries if e.payload.app_id == app_id]

        active = [e for e in entries if e.payload.active]
        if len(active) == 1:
            return {"status": STATUS_ACTIVE, "context": _serialize(active[0])}
        if len(active) > 1:
            focused = [e for e in active if e.payload.focused]
            if len(focused) == 1:
                return {"status": STATUS_ACTIVE, "context": _serialize(focused[0])}
            # Most recent focus evidence wins only when it is unambiguous:
            # exactly one entry focused most recently than the rest.
            latest = max(active, key=lambda e: e.updated_at)
            focused_latest = [e for e in active if e.updated_at == latest.updated_at]
            if len(focused_latest) == 1 and latest.payload.focused:
                return {"status": STATUS_ACTIVE, "context": _serialize(latest)}
            return {
                "status": STATUS_AMBIGUOUS,
                "candidates": [_serialize(e) for e in sorted(active, key=lambda e: e.updated_at, reverse=True)],
            }

        if entries:
            # Fresh but all explicitly inactive (e.g. publisher navigated away).
            return {"status": STATUS_ABSENT, "context": None}

        expired = self._store.list_for_user(user_id=str(user_id), fresh_only=False)
        if app_id:
            expired = [e for e in expired if e.payload.app_id == app_id]
        if expired:
            newest = max(expired, key=lambda e: e.updated_at)
            return {
                "status": STATUS_STALE,
                "context": _serialize(newest),
            }
        return {"status": STATUS_ABSENT, "context": None}
