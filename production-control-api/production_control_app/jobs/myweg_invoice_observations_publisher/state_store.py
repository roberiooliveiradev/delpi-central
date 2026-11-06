"""Estado operacional do publicador fiscal MyWEG (independente do publicador de necessidades)."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

try:
    import fcntl
except ImportError:  # pragma: no cover — Windows
    fcntl = None  # type: ignore[assignment]

_SAO_PAULO = ZoneInfo("America/Sao_Paulo")
_SUCCESS_STATUSES = frozenset({"published", "idempotent"})


class InvoicePublisherStateStore:
    """Autoridade local de tentativas — a observação no PostgreSQL permanece a fonte de negócio."""

    def __init__(self, state_dir: Path) -> None:
        self._state_dir = state_dir
        self._path = state_dir / "invoice_publisher_state.json"
        self._lock_path = state_dir / "invoice_publisher_state.lock"
        self._run_lock_path = state_dir / "invoice_publisher_run.lock"

    def record_attempt(
        self,
        *,
        collection_id: str,
        payload_sha256: str,
        status: str,
        document_date: str | None = None,
        semantic_sha256: str | None = None,
        observation_id: str | None = None,
        http_status: int | None = None,
        result: str | None = None,
        dry_run: bool = False,
    ) -> None:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        with self._locked():
            data = self._read_unlocked()
            attempts = list(data.get("attempts") or [])
            kept: list[dict[str, Any]] = []
            for item in attempts:
                if (
                    item.get("collection_id") == collection_id
                    and item.get("payload_sha256") == payload_sha256
                ):
                    continue
                kept.append(item)
            kept.append(
                {
                    "collection_id": collection_id,
                    "document_date": document_date,
                    "payload_sha256": payload_sha256,
                    "semantic_sha256": semantic_sha256,
                    "observation_id": observation_id,
                    "status": status,
                    "http_status": http_status,
                    "result": result,
                    "dry_run": dry_run,
                    "updated_at": now,
                }
            )
            data["attempts"] = kept[-500:]
            self._write_atomic_unlocked(data)

    def get_success_for_collection(self, collection_id: str) -> dict[str, Any] | None:
        data = self._read_unlocked()
        for item in reversed(list(data.get("attempts") or [])):
            if item.get("collection_id") != collection_id:
                continue
            if item.get("dry_run"):
                continue
            if str(item.get("status") or "") in _SUCCESS_STATUSES:
                return dict(item)
        return None

    def get_success_for_document_date(self, document_date: str) -> dict[str, Any] | None:
        data = self._read_unlocked()
        for item in reversed(list(data.get("attempts") or [])):
            if str(item.get("document_date") or "") != document_date:
                continue
            if item.get("dry_run"):
                continue
            if str(item.get("status") or "") in _SUCCESS_STATUSES:
                return dict(item)
        return None

    def get_activation_document_date(self) -> date | None:
        data = self._read_unlocked()
        activation = data.get("activation") or {}
        raw = activation.get("document_date_min")
        if not raw:
            return None
        try:
            return date.fromisoformat(str(raw)[:10])
        except ValueError:
            return None

    def set_activation_document_date(self, document_date_min: date) -> None:
        with self._locked():
            data = self._read_unlocked()
            data["activation"] = {
                "document_date_min": document_date_min.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._write_atomic_unlocked(data)

    @contextmanager
    def acquire_run_lock(self) -> Iterator[bool]:
        self._state_dir.mkdir(parents=True, exist_ok=True)
        handle = self._run_lock_path.open("a+", encoding="utf-8")
        acquired = False
        try:
            if fcntl is None:
                acquired = True
            else:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except BlockingIOError:
                    acquired = False
            yield acquired
        finally:
            if acquired and fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

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
            prefix="invoice_publisher_state_",
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
