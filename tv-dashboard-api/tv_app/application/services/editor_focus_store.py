"""Ephemeral editor focus (playlist/slide/selection) for VISTA READ Actions."""

from __future__ import annotations

import threading
import time
from typing import Any

# Aligned with PresentationRealtimeHub presence stale TTL.
DEFAULT_FOCUS_TTL_SECONDS = 90.0


class EditorFocusStore:
    """In-process snapshot of the authenticated user's live editor focus.

    Fed by authorized ``selection_update`` WebSocket messages. Not persisted.
    Only the owning userId may read their own focus.
    """

    def __init__(self, *, ttl_seconds: float = DEFAULT_FOCUS_TTL_SECONDS) -> None:
        self._ttl = max(15.0, float(ttl_seconds))
        self._lock = threading.RLock()
        # key: userId → focus row
        self._by_user: dict[str, dict[str, Any]] = {}

    def record(
        self,
        *,
        user_id: str,
        playlist_id: str,
        slide_id: str,
        selected_ids: list[str] | None = None,
        client_id: str | None = None,
    ) -> dict[str, Any]:
        uid = str(user_id or "").strip()
        pid = str(playlist_id or "").strip()
        sid = str(slide_id or "").strip()
        if not uid or not pid or not sid:
            return {}
        ids: list[str] = []
        for raw in selected_ids or []:
            block_id = str(raw or "").strip()
            if block_id and block_id not in ids:
                ids.append(block_id)
            if len(ids) >= 100:
                break
        now_ms = int(time.time() * 1000)
        row = {
            "playlistId": pid,
            "slideId": sid,
            "selectedIds": ids,
            "clientId": str(client_id or "").strip() or None,
            "updatedAt": now_ms,
            "_mono": time.monotonic(),
        }
        with self._lock:
            self._by_user[uid] = row
        return self._public_view(row, stale=False)

    def clear_user(self, user_id: str) -> None:
        uid = str(user_id or "").strip()
        if not uid:
            return
        with self._lock:
            self._by_user.pop(uid, None)

    def clear_playlist_for_user(self, user_id: str, playlist_id: str) -> None:
        uid = str(user_id or "").strip()
        pid = str(playlist_id or "").strip()
        if not uid or not pid:
            return
        with self._lock:
            row = self._by_user.get(uid)
            if row and str(row.get("playlistId") or "") == pid:
                del self._by_user[uid]

    def get_for_user(self, user_id: str) -> dict[str, Any] | None:
        uid = str(user_id or "").strip()
        if not uid:
            return None
        with self._lock:
            row = self._by_user.get(uid)
            if not row:
                return None
            age = time.monotonic() - float(row.get("_mono") or 0)
            if age <= self._ttl:
                return self._public_view(row, stale=False)
            if age <= self._ttl * 2:
                return self._public_view(row, stale=True)
            del self._by_user[uid]
            return None

    def get_for_user_playlist(
        self, user_id: str, playlist_id: str
    ) -> dict[str, Any] | None:
        focus = self.get_for_user(user_id)
        if not focus:
            return None
        if str(focus.get("playlistId") or "") != str(playlist_id or "").strip():
            return None
        return focus

    def _is_stale_locked(self, row: dict[str, Any]) -> bool:
        mono = float(row.get("_mono") or 0)
        return (time.monotonic() - mono) > self._ttl

    @staticmethod
    def _public_view(row: dict[str, Any], *, stale: bool) -> dict[str, Any]:
        return {
            "playlistId": row.get("playlistId"),
            "slideId": row.get("slideId"),
            "selectedIds": list(row.get("selectedIds") or []),
            "clientId": row.get("clientId"),
            "updatedAt": row.get("updatedAt"),
            "stale": bool(stale),
        }


editor_focus_store = EditorFocusStore()
