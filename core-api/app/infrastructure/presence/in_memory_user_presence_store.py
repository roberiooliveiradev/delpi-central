# app/infrastructure/presence/in_memory_user_presence_store.py

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.dto.user_presence_dto import UserPresenceSummaryDTO


@dataclass
class _ConnectionState:
    user_id: str
    connected_at: datetime
    last_seen_at: datetime


class InMemoryUserPresenceStore:
    def __init__(self, *, ttl_seconds: int = 90):
        self._ttl_seconds = max(15, ttl_seconds)
        self._lock = threading.Lock()
        self._by_session: dict[str, _ConnectionState] = {}

    def register(self, *, user_id: str, session_id: str) -> None:
        now = datetime.utcnow()
        with self._lock:
            self._prune_locked(now)
            self._by_session[session_id] = _ConnectionState(
                user_id=str(user_id),
                connected_at=now,
                last_seen_at=now,
            )

    def unregister(self, session_id: str) -> None:
        with self._lock:
            self._by_session.pop(session_id, None)

    def touch(self, session_id: str) -> None:
        now = datetime.utcnow()
        with self._lock:
            state = self._by_session.get(session_id)
            if state is None:
                return
            state.last_seen_at = now

    def list_online(self) -> list[UserPresenceSummaryDTO]:
        now = datetime.utcnow()
        with self._lock:
            self._prune_locked(now)
            grouped: dict[str, list[_ConnectionState]] = {}
            for state in self._by_session.values():
                grouped.setdefault(state.user_id, []).append(state)

        summaries: list[UserPresenceSummaryDTO] = []
        for user_id, states in grouped.items():
            connected_at = min(state.connected_at for state in states)
            last_seen_at = max(state.last_seen_at for state in states)
            summaries.append(
                UserPresenceSummaryDTO(
                    user_id=user_id,
                    connection_count=len(states),
                    connected_at=connected_at,
                    last_seen_at=last_seen_at,
                )
            )

        summaries.sort(key=lambda item: item.last_seen_at, reverse=True)
        return summaries

    def _prune_locked(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self._ttl_seconds)
        stale = [
            session_id
            for session_id, state in self._by_session.items()
            if state.last_seen_at < cutoff
        ]
        for session_id in stale:
            self._by_session.pop(session_id, None)
