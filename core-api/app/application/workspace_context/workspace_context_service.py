# app/application/workspace_context/workspace_context_service.py
"""Resolve the authenticated user's *current* workspace context.

Statuses:
- ``active``    — exactly one material candidate wins after dedupe and
                  specificity (a single open workspace, a focused tab, or
                  the most specific context of one entity chain).
- ``ambiguous`` — multiple *materially distinct* fresh+active candidates
                  with no foreground winner; candidates are returned so the
                  consumer can ask one discriminating question instead of
                  guessing.
- ``stale``     — entries exist but all expired (TTL exceeded).
- ``absent``    — nothing published, or publishers explicitly deactivated.

``active`` on an entry means "workspace open" — NOT "tab focused". A user
chatting with an assistant in another window keeps their context ACTIVE.
``focused`` is only recency evidence for ambiguity resolution.

Resolution pipeline: drop expired -> keep active -> dedupe by material key
(client/tab ids never count) -> drop strictly less specific contexts of the
same entity chain (home never competes) -> focus/recency as tiebreak only
between materially distinct candidates -> else AMBIGUOUS.
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


def _material_key(entry: WorkspaceContextEntry) -> tuple:
    """Semantic identity of a context, ignoring publisher/tab technical ids.

    ``client_instance_id`` never participates: two tabs publishing the same
    app/entity/presentation context are one material candidate, not two.
    """
    p = entry.payload
    refs = tuple((r.entity_type, r.entity_id) for r in p.entity_refs)
    presentation = tuple(sorted(p.presentation_state.items()))
    return (p.app_id, refs, presentation)


def _refs_chain(entry: WorkspaceContextEntry) -> tuple:
    return tuple((r.entity_type, r.entity_id) for r in entry.payload.entity_refs)


def _dedupe_material(
    entries: list[WorkspaceContextEntry],
) -> list[WorkspaceContextEntry]:
    """Collapse entries to one representative per material key."""
    best: dict[tuple, WorkspaceContextEntry] = {}
    for e in entries:
        key = _material_key(e)
        current = best.get(key)
        if current is None or (e.payload.focused, e.updated_at) > (
            current.payload.focused,
            current.updated_at,
        ):
            best[key] = e
    return list(best.values())


def _drop_subsumed(
    candidates: list[WorkspaceContextEntry],
) -> list[WorkspaceContextEntry]:
    """Drop candidates whose entity chain is a strict prefix of another's.

    ``home`` (empty refs) is a prefix of every material context, so it can
    never compete with an active/fresh process workspace. Specificity only
    eliminates within the *same* chain — incompatible entities (P vs Q,
    P/I vs P/J) are never silently resolved.
    """
    chains = [_refs_chain(e) for e in candidates]
    keep = []
    for i, entry in enumerate(candidates):
        chain = chains[i]
        subsumed = any(
            len(chain) < len(other) and other[: len(chain)] == chain
            for j, other in enumerate(chains)
            if j != i
        )
        if not subsumed:
            keep.append(entry)
    return keep


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
        # Technical multiplicity != material ambiguity: collapse same-material
        # entries first, then drop strictly less specific contexts of the same
        # entity chain (home never competes with an open process workspace).
        candidates = _drop_subsumed(_dedupe_material(active))
        if len(candidates) == 1:
            return {"status": STATUS_ACTIVE, "context": _serialize(candidates[0])}
        if len(candidates) > 1:
            focused = [e for e in candidates if e.payload.focused]
            if len(focused) == 1:
                return {"status": STATUS_ACTIVE, "context": _serialize(focused[0])}
            # Focus/recency is tiebreak evidence between materially distinct
            # candidates — never a silent last-write-wins on raw entries.
            if focused:
                latest = max(focused, key=lambda e: e.updated_at)
                return {"status": STATUS_ACTIVE, "context": _serialize(latest)}
            return {
                "status": STATUS_AMBIGUOUS,
                "candidates": [
                    _serialize(e)
                    for e in sorted(candidates, key=lambda e: e.updated_at, reverse=True)
                ],
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
