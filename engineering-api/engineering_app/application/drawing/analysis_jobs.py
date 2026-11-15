"""Analysis job registry (DEC-VAL-030) — execução prolongada governada.

Contrato explícito exigido por RQ-VAL-033: uma análise visual completa
de documento multipágina não cabe no orçamento de uma requisição MCP
interativa (~dezenas de segundos). O job executa desacoplado do ciclo
da requisição; o consumidor consulta o resultado por ``job_id``.

Owner: Engineering API (bounded context). Estado em memória do
processo (single-worker uvicorn) — sem banco, sem cache compartilhado
entre usuários: a chave inclui identidade delegada, e resultados só
são devolvidos ao dono lógico. TTL e timeout são limites operacionais
explícitos; expirados são removidos sem efeito colateral.

Restart do processo descarta TODOS os jobs — comportamento exposto
honestamente ao consumidor (``process_local_registry: true`` nos
envelopes).
"""

from __future__ import annotations

import hashlib
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

JOB_TTL_S = 3600  # resultado consultável por 1h após conclusão
JOB_RUNNING_CAP_S = 2700  # 2 pipelines × 25 páginas com margem
_JOB_MAX = 64

_FINAL_STATES = {"COMPLETED", "FAILED", "EXPIRED"}

# Fases reais do pipeline de leitura visual (RQ — progresso honesto:
# fase/estado, nunca percentual inventado).
JOB_PHASES = (
    "FETCHING_DOCUMENT",
    "OCR",
    "UNDERSTANDING",
    "COMPARING",
    "FINALIZING",
)


@dataclass
class AnalysisJob:
    job_id: str
    key: str
    product_code: str
    owner_hash: str
    status: str = "RUNNING"
    analysis_type: str = ""
    phase: str | None = None
    created_ts: float = field(default_factory=time.time)
    started_ts: float = field(default_factory=time.time)
    updated_ts: float = field(default_factory=time.time)
    finished_ts: float | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    document_sha: str | None = None


def _iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def job_summary(job: AnalysisJob) -> dict[str, Any]:
    """Projeção pública do job — metadados + estado, sem payload pesado."""
    now = time.time()
    return {
        "job_id": job.job_id,
        "analysis_type": job.analysis_type or None,
        "product_code": job.product_code,
        "status": job.status,
        "phase": job.phase,
        "created_at": _iso(job.created_ts),
        "started_at": _iso(job.started_ts),
        "updated_at": _iso(job.updated_ts),
        "finished_at": _iso(job.finished_ts),
        "elapsed_seconds": round(
            (job.finished_ts or now) - job.created_ts, 1
        ),
        "result_available": job.status == "COMPLETED" and bool(job.result),
        "document_sha": job.document_sha,
        "error": job.error,
        "process_local_registry": True,
    }


class AnalysisJobStore:
    """Registro idempotente de jobs de análise — processo-local.

    Todas as mutações passam por ``_lock``: check-and-create é atômico
    para que dois callers simultâneos não criem dois jobs para a mesma
    chave nem dois estados inconsistentes.
    """

    def __init__(self, *, ttl_s: int = JOB_TTL_S):
        self._ttl_s = ttl_s
        self._jobs: dict[str, AnalysisJob] = {}
        self._by_key: dict[str, str] = {}
        self._lock = threading.RLock()

    @staticmethod
    def make_key(
        product_code: str, identity_fingerprint: str, params_fingerprint: str
    ) -> str:
        raw = f"{product_code}|{identity_fingerprint}|{params_fingerprint}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    @staticmethod
    def owner_hash(identity_fingerprint: str) -> str:
        return hashlib.sha256(
            identity_fingerprint.encode()
        ).hexdigest()[:16]

    def _sweep(self, now: float) -> None:
        for jid, job in list(self._jobs.items()):
            if job.status == "RUNNING":
                if now - job.created_ts > JOB_RUNNING_CAP_S:
                    job.status = "FAILED"
                    job.phase = None
                    job.finished_ts = now
                    job.updated_ts = now
                    job.error = {
                        "code": "timeout",
                        "message": (
                            "Execução excedeu o orçamento do job "
                            f"({JOB_RUNNING_CAP_S}s)."
                        ),
                    }
                continue
            if job.finished_ts and now - job.finished_ts > self._ttl_s:
                self._jobs.pop(jid, None)
                self._by_key.pop(job.key, None)

    def _find_by_key_locked(self, key: str, now: float) -> AnalysisJob | None:
        existing_id = self._by_key.get(key)
        if not existing_id:
            return None
        job = self._jobs.get(existing_id)
        if job and job.status in {"RUNNING", "COMPLETED"} and (
            job.status == "RUNNING"
            or (job.finished_ts and now - job.finished_ts <= self._ttl_s)
        ):
            return job
        # FAILED/expirado não bloqueia retry — libera a chave.
        self._by_key.pop(key, None)
        return None

    def find_existing(
        self,
        *,
        product_code: str,
        identity_fingerprint: str,
        params_fingerprint: str,
    ) -> AnalysisJob | None:
        """Resolve a chave idempotente SEM criar job — existing_only."""
        now = time.time()
        with self._lock:
            self._sweep(now)
            job = self._find_by_key_locked(
                self.make_key(
                    product_code, identity_fingerprint, params_fingerprint
                ),
                now,
            )
            if job and job.owner_hash != self.owner_hash(
                identity_fingerprint
            ):
                return None  # nunca vaza entre identidades
            return job

    def get_or_start(
        self,
        *,
        product_code: str,
        identity_fingerprint: str,
        params_fingerprint: str,
        analysis_type: str = "",
    ) -> tuple[AnalysisJob, bool]:
        """Retorna ``(job, created)`` — deduplicação por (produto,
        identidade, parâmetros): chamadas idênticas compartilham o job."""
        now = time.time()
        with self._lock:
            self._sweep(now)
            key = self.make_key(
                product_code, identity_fingerprint, params_fingerprint
            )
            job = self._find_by_key_locked(key, now)
            if job is not None:
                return job, False
            if len(self._jobs) >= _JOB_MAX:
                self._sweep(now + self._ttl_s + 1)
            job = AnalysisJob(
                job_id=f"aj-{uuid.uuid4().hex[:16]}",
                key=key,
                product_code=product_code,
                owner_hash=self.owner_hash(identity_fingerprint),
                analysis_type=analysis_type,
            )
            self._jobs[job.job_id] = job
            self._by_key[key] = job.job_id
            return job, True

    def get_for_owner(
        self, job_id: str, identity_fingerprint: str
    ) -> AnalysisJob | None:
        with self._lock:
            self._sweep(time.time())
            job = self._jobs.get(job_id)
            if job is None:
                return None
            if job.owner_hash != self.owner_hash(identity_fingerprint):
                return None  # não vaza entre identidades delegadas
            return job

    def list_for_owner(
        self, identity_fingerprint: str
    ) -> list[AnalysisJob]:
        """Jobs do caller ordenados por criação desc — nunca de outra
        identidade."""
        with self._lock:
            self._sweep(time.time())
            own = self.owner_hash(identity_fingerprint)
            jobs = [
                j
                for j in self._jobs.values()
                if j.owner_hash == own
            ]
            return sorted(jobs, key=lambda j: j.created_ts, reverse=True)

    def supersede(self, job_id: str) -> None:
        """RQ-03D — invalida um resultado COMPLETED cuja identidade
        documental não confere mais (SHA divergente). Libera a chave
        idempotente para um novo job; o job_id continua consultável
        pelo owner até o TTL."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job.status = "EXPIRED"
            job.phase = None
            job.finished_ts = job.updated_ts = time.time()
            job.error = {
                "code": "stale_document",
                "message": (
                    "Resultado invalidado: o documento oficial atual "
                    "difere do documento analisado (SHA-256 divergente)."
                ),
            }
            self._by_key.pop(job.key, None)

    def running_job_count(self) -> int:
        with self._lock:
            self._sweep(time.time())
            return sum(
                1 for j in self._jobs.values() if j.status == "RUNNING"
            )

    def update_phase(self, job_id: str, phase: str | None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "RUNNING":
                job.phase = phase
                job.updated_ts = time.time()

    def set_document_sha(self, job_id: str, sha: str | None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and sha:
                job.document_sha = sha
                job.updated_ts = time.time()

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "RUNNING":
                job.status = "COMPLETED"
                job.phase = None
                job.finished_ts = job.updated_ts = time.time()
                job.result = result

    def fail(
        self,
        job_id: str,
        code: str,
        message: str,
        status_code: int = 500,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status == "RUNNING":
                job.status = "FAILED"
                job.phase = None
                job.finished_ts = job.updated_ts = time.time()
                job.error = {
                    "code": code,
                    "message": message,
                    "status_code": status_code,
                }


_store: AnalysisJobStore | None = None


def analysis_job_store() -> AnalysisJobStore:
    global _store
    if _store is None:
        _store = AnalysisJobStore()
    return _store


def reset_analysis_job_store() -> None:
    """Somente testes — estado limpo por caso."""
    global _store
    _store = None
