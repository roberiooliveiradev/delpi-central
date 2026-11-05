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
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

JOB_TTL_S = 3600  # resultado consultável por 1h após conclusão
JOB_RUNNING_CAP_S = 2700  # 2 pipelines × 25 páginas com margem
_JOB_MAX = 64

_FINAL_STATES = {"COMPLETED", "FAILED", "EXPIRED"}


@dataclass
class AnalysisJob:
    job_id: str
    key: str
    product_code: str
    owner_hash: str
    status: str = "RUNNING"
    created_ts: float = field(default_factory=time.time)
    finished_ts: float | None = None
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class AnalysisJobStore:
    """Registro idempotente de jobs de análise — processo-local."""

    def __init__(self, *, ttl_s: int = JOB_TTL_S):
        self._ttl_s = ttl_s
        self._jobs: dict[str, AnalysisJob] = {}
        self._by_key: dict[str, str] = {}

    @staticmethod
    def make_key(
        product_code: str, identity_fingerprint: str, params_fingerprint: str
    ) -> str:
        raw = f"{product_code}|{identity_fingerprint}|{params_fingerprint}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def _sweep(self, now: float) -> None:
        for jid, job in list(self._jobs.items()):
            if job.status == "RUNNING":
                if now - job.created_ts > JOB_RUNNING_CAP_S:
                    job.status = "FAILED"
                    job.finished_ts = now
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

    def get_or_start(
        self,
        *,
        product_code: str,
        identity_fingerprint: str,
        params_fingerprint: str,
    ) -> tuple[AnalysisJob, bool]:
        """Retorna ``(job, created)`` — deduplicação por (produto,
        identidade, parâmetros): chamadas idênticas compartilham o job."""
        now = time.time()
        self._sweep(now)
        key = self.make_key(
            product_code, identity_fingerprint, params_fingerprint
        )
        existing_id = self._by_key.get(key)
        if existing_id:
            job = self._jobs.get(existing_id)
            if job and job.status in {"RUNNING", "COMPLETED"} and (
                job.status == "RUNNING"
                or (
                    job.finished_ts
                    and now - job.finished_ts <= self._ttl_s
                )
            ):
                return job, False
            # FAILED/expirado não bloqueia retry — libera a chave.
            self._by_key.pop(key, None)
        if len(self._jobs) >= _JOB_MAX:
            self._sweep(now + self._ttl_s + 1)
        job = AnalysisJob(
            job_id=f"aj-{uuid.uuid4().hex[:16]}",
            key=key,
            product_code=product_code,
            owner_hash=hashlib.sha256(
                identity_fingerprint.encode()
            ).hexdigest()[:16],
        )
        self._jobs[job.job_id] = job
        self._by_key[key] = job.job_id
        return job, True

    def get_for_owner(
        self, job_id: str, identity_fingerprint: str
    ) -> AnalysisJob | None:
        self._sweep(time.time())
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.owner_hash != hashlib.sha256(
            identity_fingerprint.encode()
        ).hexdigest()[:16]:
            return None  # não vaza entre identidades delegadas
        return job

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job and job.status == "RUNNING":
            job.status = "COMPLETED"
            job.finished_ts = time.time()
            job.result = result

    def fail(
        self,
        job_id: str,
        code: str,
        message: str,
        status_code: int = 500,
    ) -> None:
        job = self._jobs.get(job_id)
        if job and job.status == "RUNNING":
            job.status = "FAILED"
            job.finished_ts = time.time()
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
