# app/infrastructure/presence/redis_user_presence_store.py

from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.domain.dto.user_presence_dto import UserPresenceSummaryDTO


class RedisUserPresenceStore:

    def __init__(self, *, redis_url: str, ttl_seconds: int = 90):
        import redis

        self._ttl_seconds = max(15, ttl_seconds)
        self._client = redis.from_url(redis_url, decode_responses=True)
        self._session_prefix = "presence:session:"
        self._user_prefix = "presence:user:"

    def register(self, *, user_id: str, session_id: str) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        payload = json.dumps(
            {
                "userId": str(user_id),
                "connectedAt": now,
                "lastSeenAt": now,
            }
        )
        pipe = self._client.pipeline()
        pipe.setex(
            f"{self._session_prefix}{session_id}",
            self._ttl_seconds,
            payload,
        )
        pipe.sadd(f"{self._user_prefix}{user_id}", session_id)
        pipe.expire(f"{self._user_prefix}{user_id}", self._ttl_seconds * 2)
        pipe.execute()

    def unregister(self, session_id: str) -> None:
        raw = self._client.get(f"{self._session_prefix}{session_id}")
        pipe = self._client.pipeline()
        pipe.delete(f"{self._session_prefix}{session_id}")
        if raw:
            try:
                payload = json.loads(raw)
                user_id = payload.get("userId")
                if user_id:
                    pipe.srem(f"{self._user_prefix}{user_id}", session_id)
            except json.JSONDecodeError:
                pass
        pipe.execute()

    def touch(self, session_id: str) -> None:
        key = f"{self._session_prefix}{session_id}"
        raw = self._client.get(key)
        if not raw:
            return

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._client.delete(key)
            return

        payload["lastSeenAt"] = datetime.utcnow().isoformat() + "Z"
        user_id = payload.get("userId")
        self._client.setex(key, self._ttl_seconds, json.dumps(payload))
        if user_id:
            self._client.expire(f"{self._user_prefix}{user_id}", self._ttl_seconds * 2)

    def get_user_id(self, session_id: str) -> str | None:
        raw = self._client.get(f"{self._session_prefix}{session_id}")
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        user_id = payload.get("userId")
        return str(user_id).strip() if user_id else None

    def clear_user(self, *, user_id: str) -> None:
        normalized = str(user_id).strip()
        if not normalized:
            return
        user_key = f"{self._user_prefix}{normalized}"
        session_ids = list(self._client.smembers(user_key))
        pipe = self._client.pipeline()
        for session_id in session_ids:
            pipe.delete(f"{self._session_prefix}{session_id}")
        pipe.delete(user_key)
        pipe.execute()

    def list_online(self) -> list[UserPresenceSummaryDTO]:
        summaries: list[UserPresenceSummaryDTO] = []
        cutoff = datetime.utcnow() - timedelta(seconds=self._ttl_seconds)

        for key in self._client.scan_iter(match=f"{self._user_prefix}*"):
            user_id = key.removeprefix(self._user_prefix)
            session_ids = list(self._client.smembers(key))
            if not session_ids:
                self._client.delete(key)
                continue

            states: list[dict] = []
            for session_id in session_ids:
                raw = self._client.get(f"{self._session_prefix}{session_id}")
                if not raw:
                    self._client.srem(key, session_id)
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    self._client.delete(f"{self._session_prefix}{session_id}")
                    self._client.srem(key, session_id)
                    continue

                last_seen = _parse_iso(payload.get("lastSeenAt"))
                if last_seen is None or last_seen < cutoff:
                    self.unregister(session_id)
                    continue

                connected = _parse_iso(payload.get("connectedAt")) or last_seen
                states.append(
                    {
                        "connected_at": connected,
                        "last_seen_at": last_seen,
                    }
                )

            if not states:
                continue

            summaries.append(
                UserPresenceSummaryDTO(
                    user_id=user_id,
                    connection_count=len(states),
                    connected_at=min(item["connected_at"] for item in states),
                    last_seen_at=max(item["last_seen_at"] for item in states),
                )
            )

        summaries.sort(key=lambda item: item.last_seen_at, reverse=True)
        return summaries


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError:
        return None
