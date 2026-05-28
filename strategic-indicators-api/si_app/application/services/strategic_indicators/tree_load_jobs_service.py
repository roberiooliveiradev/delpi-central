from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class TreeLoadJobStatus:
    job_id: str
    state: str  # queued|running|succeeded|failed
    phase: str  # snapshot|trends|done|error
    progress_pct: int
    message: str
    created_at: str
    updated_at: str
    snapshot: dict[str, Any] | None = None
    trends: dict[str, Any] | None = None
    error: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TreeLoadJobsService:
    """
    Job runner simples em memória para carregamento progressivo da árvore.

    Observação: este registry é **in-memory** (bom para local/dev).
    Em produção multi-worker, deve ser substituído por storage compartilhado
    (Postgres/Redis) para garantir consistência entre instâncias.
    """

    def __init__(self, *, ttl_seconds: int = 15 * 60) -> None:
        self._ttl_seconds = int(ttl_seconds)
        self._lock = threading.Lock()
        self._jobs: dict[str, tuple[float, TreeLoadJobStatus]] = {}

    def _gc(self) -> None:
        now = time.time()
        cutoff = now - self._ttl_seconds
        expired = [job_id for job_id, (ts, _) in self._jobs.items() if ts < cutoff]
        for job_id in expired:
            self._jobs.pop(job_id, None)

    def get(self, job_id: str) -> TreeLoadJobStatus | None:
        with self._lock:
            self._gc()
            entry = self._jobs.get(job_id)
            if entry is None:
                return None
            return entry[1]

    def _set(self, status: TreeLoadJobStatus) -> None:
        with self._lock:
            self._gc()
            self._jobs[status.job_id] = (time.time(), status)

    def create_and_start(
        self,
        *,
        snapshot_fn,
        trends_fn,
    ) -> TreeLoadJobStatus:
        job_id = str(uuid4())
        now = _utc_now_iso()
        status = TreeLoadJobStatus(
            job_id=job_id,
            state="queued",
            phase="snapshot",
            progress_pct=0,
            message="Preparando carregamento...",
            created_at=now,
            updated_at=now,
        )
        self._set(status)

        def run() -> None:
            try:
                st = self.get(job_id)
                if st is None:
                    return
                st.state = "running"
                st.phase = "snapshot"
                st.progress_pct = 10
                st.message = "Carregando snapshot da árvore..."
                st.updated_at = _utc_now_iso()
                self._set(st)

                snapshot_payload = snapshot_fn()
                st = self.get(job_id)
                if st is None:
                    return
                st.snapshot = snapshot_payload
                st.progress_pct = 55
                st.message = "Snapshot carregado. Carregando histórico..."
                st.phase = "trends"
                st.updated_at = _utc_now_iso()
                self._set(st)

                trends_payload = trends_fn()
                st = self.get(job_id)
                if st is None:
                    return
                st.trends = trends_payload
                st.progress_pct = 100
                st.message = "Carregamento concluído."
                st.phase = "done"
                st.state = "succeeded"
                st.updated_at = _utc_now_iso()
                self._set(st)
            except Exception as exc:  # noqa: BLE001 - surface error to UI
                st = self.get(job_id)
                if st is None:
                    return
                st.state = "failed"
                st.phase = "error"
                st.progress_pct = min(st.progress_pct, 95)
                st.message = "Falha ao carregar dados da árvore."
                st.error = str(exc)
                st.updated_at = _utc_now_iso()
                self._set(st)

        thread = threading.Thread(target=run, name=f"si-tree-job-{job_id}", daemon=True)
        thread.start()
        return status


_shared_tree_jobs_service: TreeLoadJobsService | None = None


def get_tree_load_jobs_service() -> TreeLoadJobsService:
    global _shared_tree_jobs_service
    if _shared_tree_jobs_service is None:
        _shared_tree_jobs_service = TreeLoadJobsService()
    return _shared_tree_jobs_service

