"""Store em memória de sessões do assistente de dados (TTL)."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

from tv_app.application.services.data.tv_data_builder_content_service import (
    TvDataBuilderContentService,
)
from tv_app.application.services.data.tv_data_builder_draft import empty_draft


class TvDataBuilderSessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, dict[str, Any]] = {}

    def create(self) -> dict[str, Any]:
        session_id = uuid.uuid4().hex
        now = time.time()
        ttl = TvDataBuilderContentService.setting_int("sessionTtlSeconds", 3600)
        payload = {
            "id": session_id,
            "createdAt": now,
            "updatedAt": now,
            "expiresAt": now + ttl,
            "messages": [
                {
                    "id": uuid.uuid4().hex[:12],
                    "role": "assistant",
                    "text": TvDataBuilderContentService.message("welcome"),
                    "suggestions": [],
                }
            ],
            "draft": empty_draft(),
            "preview": None,
        }
        with self._lock:
            self._purge_locked(now)
            self._sessions[session_id] = payload
        return self._public(payload)

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            self._purge_locked(time.time())
            payload = self._sessions.get(session_id)
            if not payload:
                return None
            return self._public(payload)

    def update(self, session_id: str, mutator) -> dict[str, Any] | None:
        with self._lock:
            self._purge_locked(time.time())
            payload = self._sessions.get(session_id)
            if not payload:
                return None
            next_payload = mutator(dict(payload))
            if not isinstance(next_payload, dict):
                return None
            now = time.time()
            ttl = TvDataBuilderContentService.setting_int("sessionTtlSeconds", 3600)
            next_payload["updatedAt"] = now
            next_payload["expiresAt"] = now + ttl
            next_payload["id"] = session_id
            self._sessions[session_id] = next_payload
            return self._public(next_payload)

    def _purge_locked(self, now: float) -> None:
        expired = [key for key, row in self._sessions.items() if float(row.get("expiresAt") or 0) < now]
        for key in expired:
            self._sessions.pop(key, None)

    @staticmethod
    def _public(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": payload.get("id"),
            "messages": list(payload.get("messages") or []),
            "draft": dict(payload.get("draft") or empty_draft()),
            "preview": payload.get("preview"),
            "updatedAt": payload.get("updatedAt"),
            "expiresAt": payload.get("expiresAt"),
        }


# Singleton de processo (API worker).
SESSION_STORE = TvDataBuilderSessionStore()
