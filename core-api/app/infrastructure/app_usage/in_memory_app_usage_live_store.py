# app/infrastructure/app_usage/in_memory_app_usage_live_store.py

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.dto.app_usage_dto import AppUsageLiveAppDTO, AppUsageLiveSessionDTO


@dataclass
class _SessionState:
    user_id: str
    app_id: str | None
    route_path: str | None
    app_connected_at: datetime | None
    last_seen_at: datetime


class InMemoryAppUsageLiveStore:
    def __init__(self, *, ttl_seconds: int = 90):
        self._ttl_seconds = max(15, ttl_seconds)
        self._lock = threading.Lock()
        self._by_session: dict[str, _SessionState] = {}

    def bind_session(self, *, user_id: str, session_id: str) -> None:
        now = datetime.utcnow()
        with self._lock:
            self._prune_locked(now)
            self._by_session[session_id] = _SessionState(
                user_id=str(user_id),
                app_id=None,
                route_path=None,
                app_connected_at=None,
                last_seen_at=now,
            )

    def unbind_session(self, session_id: str) -> None:
        with self._lock:
            self._by_session.pop(session_id, None)

    def set_active_app(
        self,
        session_id: str,
        *,
        app_id: str,
        route_path: str | None = None,
    ) -> None:
        now = datetime.utcnow()
        normalized_app_id = str(app_id).strip()
        if not normalized_app_id:
            return

        with self._lock:
            state = self._by_session.get(session_id)
            if state is None:
                return

            state.app_id = normalized_app_id
            state.route_path = route_path
            state.app_connected_at = now
            state.last_seen_at = now

    def touch(self, session_id: str, *, app_id: str | None = None) -> None:
        now = datetime.utcnow()
        with self._lock:
            state = self._by_session.get(session_id)
            if state is None:
                return

            if app_id:
                normalized = str(app_id).strip()
                if normalized:
                    if state.app_id != normalized:
                        state.app_id = normalized
                        state.app_connected_at = now
                    state.route_path = state.route_path

            state.last_seen_at = now

    def get_user_id(self, session_id: str) -> str | None:
        with self._lock:
            state = self._by_session.get(session_id)
            return state.user_id if state else None

    def list_live_sessions(self) -> list[AppUsageLiveSessionDTO]:
        now = datetime.utcnow()
        with self._lock:
            self._prune_locked(now)
            sessions: list[AppUsageLiveSessionDTO] = []

            for state in self._by_session.values():
                if not state.app_id or not state.app_connected_at:
                    continue

                sessions.append(
                    AppUsageLiveSessionDTO(
                        user_id=state.user_id,
                        app_id=state.app_id,
                        route_path=state.route_path,
                        connected_at=state.app_connected_at,
                        last_seen_at=state.last_seen_at,
                    )
                )

        sessions.sort(key=lambda item: item.last_seen_at, reverse=True)
        return sessions

    def list_live_apps(self) -> list[AppUsageLiveAppDTO]:
        sessions = self.list_live_sessions()
        grouped: dict[str, list[AppUsageLiveSessionDTO]] = {}

        for session in sessions:
            grouped.setdefault(session.app_id, []).append(session)

        apps: list[AppUsageLiveAppDTO] = []
        for app_id, items in grouped.items():
            users = {item.user_id for item in items}
            apps.append(
                AppUsageLiveAppDTO(
                    app_id=app_id,
                    user_count=len(users),
                    session_count=len(items),
                    last_seen_at=max(item.last_seen_at for item in items),
                )
            )

        apps.sort(key=lambda item: item.last_seen_at, reverse=True)
        return apps

    def _prune_locked(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self._ttl_seconds)
        stale = [
            session_id
            for session_id, state in self._by_session.items()
            if state.last_seen_at < cutoff
        ]
        for session_id in stale:
            self._by_session.pop(session_id, None)
