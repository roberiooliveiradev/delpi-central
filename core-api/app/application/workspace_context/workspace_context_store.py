# app/application/workspace_context/workspace_context_store.py
"""Ephemeral in-memory store for current workspace context.

Keyed by (user_id, client_instance_id) — one entry per publisher tab.
Entries expire after ``ttl_seconds`` and are kept for one extra TTL as a
grace window so readers can distinguish STALE (recently expired) from
ABSENT (nothing published). This is convenience contextualization state,
never durable business data. Follows the same posture as the app-usage
live store: memory ships by default; ``WORKSPACE_CONTEXT_STORE=redis``
+ ``REDIS_URL`` selects the shared backend for multi-replica deployments.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from app.application.workspace_context.workspace_context_contract import (
    WorkspaceContextPayload,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class WorkspaceContextEntry:
    user_id: str
    payload: WorkspaceContextPayload
    updated_at: datetime
    expires_at: datetime

    @property
    def fresh(self) -> bool:
        return self.expires_at > _utcnow()

    def as_dict(self) -> dict[str, Any]:
        out = self.payload.as_dict()
        out["updated_at"] = self.updated_at.isoformat()
        return out


class WorkspaceContextStore:
    def __init__(self, *, ttl_seconds: int = 300):
        self._ttl = timedelta(seconds=max(15, ttl_seconds))
        self._grace = self._ttl  # expired entries linger one extra TTL
        self._lock = threading.Lock()
        self._entries: dict[tuple[str, str], WorkspaceContextEntry] = {}

    def put(self, *, user_id: str, payload: WorkspaceContextPayload) -> WorkspaceContextEntry:
        now = _utcnow()
        entry = WorkspaceContextEntry(
            user_id=str(user_id),
            payload=payload,
            updated_at=now,
            expires_at=now + self._ttl,
        )
        with self._lock:
            self._prune_locked(now)
            key = (entry.user_id, payload.client_instance_id)
            self._entries[key] = entry
        return entry

    def delete(self, *, user_id: str, client_instance_id: str) -> bool:
        with self._lock:
            return (
                self._entries.pop((str(user_id), str(client_instance_id)), None)
                is not None
            )

    def list_for_user(self, *, user_id: str, fresh_only: bool = True) -> list[WorkspaceContextEntry]:
        now = _utcnow()
        with self._lock:
            self._prune_locked(now)
            entries = [
                entry
                for (uid, _), entry in self._entries.items()
                if uid == str(user_id)
            ]
        if fresh_only:
            return [e for e in entries if e.expires_at > now]
        return entries

    def _prune_locked(self, now: datetime) -> None:
        cutoff = now - self._grace
        stale = [
            k for k, e in self._entries.items() if e.expires_at <= cutoff
        ]
        for key in stale:
            self._entries.pop(key, None)


_store: WorkspaceContextStore | None = None


def get_workspace_context_store(*, ttl_seconds: int | None = None):
    """Store provider — memory default, Redis opt-in for multi-replica.

    Mirrors the app-usage live-store posture: ``WORKSPACE_CONTEXT_STORE``
    selects the backend (``memory``|``redis``); ``REDIS_URL`` must be set
    for the shared backend. Unavailable Redis falls back to memory.
    """
    global _store
    if _store is not None:
        return _store
    ttl = ttl_seconds
    backend = "memory"
    redis_url = ""
    try:
        from flask import current_app

        if ttl is None:
            ttl = int(current_app.config.get("WORKSPACE_CONTEXT_TTL_SECONDS", 300))
        backend = str(current_app.config.get("WORKSPACE_CONTEXT_STORE", "memory")).lower()
        redis_url = str(current_app.config.get("REDIS_URL", "") or "").strip()
    except RuntimeError:
        ttl = ttl or 300

    if backend == "redis" and redis_url:
        try:
            from app.infrastructure.workspace_context.redis_workspace_context_store import (
                RedisWorkspaceContextStore,
            )

            _store = RedisWorkspaceContextStore(redis_url=redis_url, ttl_seconds=ttl)
            return _store
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                "Workspace context redis unavailable, using memory: %s", exc
            )
    _store = WorkspaceContextStore(ttl_seconds=ttl or 300)
    return _store


def reset_workspace_context_store() -> None:
    global _store
    _store = None
