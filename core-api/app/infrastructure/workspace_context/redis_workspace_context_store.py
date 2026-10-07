# app/infrastructure/workspace_context/redis_workspace_context_store.py
"""Redis-backed store for current workspace context.

Same semantics as ``WorkspaceContextStore`` (memory): entries keyed by
(user_id, client_instance_id), TTL expiry plus one-TTL grace window so
readers distinguish STALE from ABSENT. Redis key TTL covers both —
expired entries disappear automatically once the grace window passes.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.application.workspace_context.workspace_context_contract import (
    WorkspaceContextPayload,
)
from app.application.workspace_context.workspace_context_store import (
    WorkspaceContextEntry,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


class RedisWorkspaceContextStore:
    def __init__(self, *, redis_url: str, ttl_seconds: int = 300):
        import redis

        self._ttl = timedelta(seconds=max(15, ttl_seconds))
        self._grace = self._ttl
        self._key_ttl_seconds = int((self._ttl + self._grace).total_seconds())
        self._client = redis.from_url(redis_url, decode_responses=True)

    def _entry_key(self, user_id: str, client_instance_id: str) -> str:
        return f"wctx:entry:{user_id}:{client_instance_id}"

    def _user_key(self, user_id: str) -> str:
        return f"wctx:user:{user_id}"

    def put(self, *, user_id: str, payload: WorkspaceContextPayload) -> WorkspaceContextEntry:
        now = _utcnow()
        entry = WorkspaceContextEntry(
            user_id=str(user_id),
            payload=payload,
            updated_at=now,
            expires_at=now + self._ttl,
        )
        doc = entry.as_dict()
        doc["expires_at"] = entry.expires_at.isoformat()
        pipe = self._client.pipeline()
        pipe.setex(
            self._entry_key(entry.user_id, payload.client_instance_id),
            self._key_ttl_seconds,
            json.dumps(doc),
        )
        user_key = self._user_key(entry.user_id)
        pipe.sadd(user_key, payload.client_instance_id)
        pipe.expire(user_key, self._key_ttl_seconds)
        pipe.execute()
        return entry

    def delete(self, *, user_id: str, client_instance_id: str) -> bool:
        pipe = self._client.pipeline()
        pipe.delete(self._entry_key(str(user_id), str(client_instance_id)))
        pipe.srem(self._user_key(str(user_id)), str(client_instance_id))
        deleted, _ = pipe.execute()
        return bool(deleted)

    def list_for_user(self, *, user_id: str, fresh_only: bool = True) -> list[WorkspaceContextEntry]:
        now = _utcnow()
        user_key = self._user_key(str(user_id))
        client_ids = self._client.smembers(user_key)
        if not client_ids:
            return []
        keys = [self._entry_key(str(user_id), cid) for cid in client_ids]
        raws = self._client.mget(keys)
        entries: list[WorkspaceContextEntry] = []
        stale_members: list[str] = []
        for cid, raw in zip(client_ids, raws):
            if raw is None:
                stale_members.append(cid)
                continue
            try:
                doc = json.loads(raw)
                entries.append(
                    WorkspaceContextEntry(
                        user_id=str(user_id),
                        payload=WorkspaceContextPayload.from_dict(doc),
                        updated_at=_parse_dt(doc["updated_at"]),
                        expires_at=_parse_dt(doc["expires_at"]),
                    )
                )
            except (KeyError, ValueError, TypeError):
                stale_members.append(cid)
        if stale_members:
            self._client.srem(user_key, *stale_members)
        if fresh_only:
            return [e for e in entries if e.expires_at > now]
        return entries
