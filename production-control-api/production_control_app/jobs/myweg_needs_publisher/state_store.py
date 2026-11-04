"""Estado operacional mínimo das tentativas (sem payload nem secrets)."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover — Windows
    fcntl = None  # type: ignore[assignment]


class PublisherStateStore:
    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._path = state_dir / "publisher_state.json"
        self._lock_path = state_dir / "publisher_state.lock"

    def record_attempt(
        self,
        *,
        collection_id: str,
        payload_sha256: str,
        status: str,
        http_status: int | None = None,
        result: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "collection_id": collection_id,
            "payload_sha256": payload_sha256,
            "status": status,
            "http_status": http_status,
            "result": result,
            "dry_run": dry_run,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._locked():
            data = self._read_unlocked()
            attempts = list(data.get("attempts") or [])
            attempts = [
                item
                for item in attempts
                if not (
                    item.get("collection_id") == collection_id
                    and item.get("payload_sha256") == payload_sha256
                )
            ]
            attempts.append(entry)
            # Retém só as últimas 200 tentativas.
            data["attempts"] = attempts[-200:]
            self._write_atomic_unlocked(data)

    def get_attempt(self, collection_id: str, payload_sha256: str) -> dict[str, Any] | None:
        data = self._read_unlocked()
        for item in reversed(list(data.get("attempts") or [])):
            if (
                item.get("collection_id") == collection_id
                and item.get("payload_sha256") == payload_sha256
            ):
                return dict(item)
        return None

    def _read_unlocked(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"attempts": []}
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"attempts": []}
        if not isinstance(payload, dict):
            return {"attempts": []}
        return payload

    def _write_atomic_unlocked(self, data: dict[str, Any]) -> None:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix="publisher_state_",
            suffix=".json",
            dir=str(self._state_dir),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self._path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)

    def _locked(self):
        self._state_dir.mkdir(parents=True, exist_ok=True)
        lock_file = self._lock_path.open("a+", encoding="utf-8")

        class _Guard:
            def __enter__(self_inner):
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                if fcntl is not None:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                return False

        return _Guard()
