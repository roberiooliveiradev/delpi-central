"""Visual-job admission gate + operational status (RQ-OPS-01/04).

Regra do owner: **no máximo um processamento visual pesado por vez
no host compartilhado.** O gate reserva o slot ANTES de criar o job
— check-and-reserve atômico sob um único lock, impedindo que duas
requisições simultâneas iniciem dois OCRs por race.

Camadas de proteção (cada uma cobre um escopo):

- ``VisualAdmissionGate`` — serializa JOBS pesados deste processo
  (max_heavy_jobs, default 1);
- ``BoundedSemaphore`` em ``subprocess_executor`` — serializa as
  chamadas OCR dentro de cada job (max_concurrency, default 1);
- ``RLIMIT_AS/CPU`` — bounda o worker filho;
- orçamento de admissão — fail-closed quando a memória medida não
  comprova capacidade (``resource_limit``/``unknown_capacity``).

Limitação honesta: o gate governa ESTE processo. Containers
descartáveis ou probes externos ao serviço compartilham o host e
não passam pelo gate — mitigação é a política operacional do owner
(1 PDF por vez, budget check antes de executar), não código.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from engineering_app.application.drawing.analysis_jobs import (
    analysis_job_store,
)
from engineering_app.infrastructure.extraction import (
    resource_monitor,
    subprocess_executor,
)

_MAX_HEAVY_ENV = "ENG_DRAWING_OCR_MAX_HEAVY_JOBS"
_OCR_FLAG_ENV = "ENG_DRAWING_OCR_BENCHMARK_ENABLED"

ADMITTED = "ADMITTED"
REUSED_EXISTING = "REUSED_EXISTING"
BUSY = "BUSY"
RESOURCE_LIMIT = "RESOURCE_LIMIT"
OCR_UNAVAILABLE = "OCR_UNAVAILABLE"
SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
FORBIDDEN = "FORBIDDEN"
UNKNOWN_CAPACITY = "UNKNOWN_CAPACITY"


def max_heavy_jobs() -> int:
    try:
        value = int(os.getenv(_MAX_HEAVY_ENV, "").strip() or 1)
    except ValueError:
        return 1
    return max(1, min(value, 4))


def ocr_enabled() -> bool:
    return os.getenv(_OCR_FLAG_ENV, "").strip().lower() == "true"


class VisualAdmissionGate:
    """Reserva atômica de slot de processamento visual pesado."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._slots_in_use = 0

    def try_acquire(
        self, *, usage: dict[str, Any] | None = None
    ) -> tuple[str, dict[str, Any]]:
        """Decisão + detalhe — atômico: check e reserva no mesmo lock.

        Retorna ``(outcome, detail)``; ``ADMITTED`` já deixa o slot
        reservado — o caller DEVE chamar ``release()`` ao terminar
        (sucesso, falha ou exceção).
        """
        with self._lock:
            detail: dict[str, Any] = {
                "max_heavy_jobs": max_heavy_jobs(),
                "active_heavy_jobs": self._slots_in_use,
            }
            if not ocr_enabled():
                return OCR_UNAVAILABLE, detail
            if self._slots_in_use >= max_heavy_jobs():
                detail["reason"] = (
                    "heavy_ocr_slot_occupied — política do owner: 1 "
                    "processamento visual pesado por vez no host."
                )
                return BUSY, detail
            decision, budget_detail = (
                resource_monitor.admission_budget_check(usage)
            )
            detail.update(budget_detail)
            if decision == "resource_limit":
                detail["reason"] = (
                    "memória disponível abaixo do orçamento de "
                    "admissão — fail-closed."
                )
                return RESOURCE_LIMIT, detail
            if decision == "unknown_capacity":
                detail["reason"] = (
                    "métricas de memória indisponíveis — fail-closed, "
                    "não declarar SAFE_TO_START sem medição."
                )
                return UNKNOWN_CAPACITY, detail
            self._slots_in_use += 1
            detail["active_heavy_jobs"] = self._slots_in_use
            return ADMITTED, detail

    def release(self) -> None:
        with self._lock:
            if self._slots_in_use > 0:
                self._slots_in_use -= 1

    def active_heavy_jobs(self) -> int:
        with self._lock:
            return self._slots_in_use


_gate: VisualAdmissionGate | None = None


def visual_admission_gate() -> VisualAdmissionGate:
    global _gate
    if _gate is None:
        _gate = VisualAdmissionGate()
    return _gate


def reset_visual_admission_gate() -> None:
    """Somente testes."""
    global _gate
    _gate = None


def ocr_runtime_status() -> dict[str, Any]:
    """Estado operacional READ_ONLY — nunca inicia OCR/modelo.

    Diferencia: serviço disponível, OCR habilitado, OCR ocupado,
    recursos suficientes/insuficientes e métricas indisponíveis.
    """
    usage = resource_monitor.resource_usage()
    enabled = ocr_enabled()
    active = visual_admission_gate().active_heavy_jobs()
    running_jobs = analysis_job_store().running_job_count()
    configured_max = subprocess_executor.max_concurrency()
    workers = subprocess_executor.active_workers()
    decision, budget_detail = resource_monitor.admission_budget_check(
        usage
    )

    if not enabled:
        status = "UNAVAILABLE"
        reason = "ocr_disabled_by_flag"
    elif active >= max_heavy_jobs() or workers >= configured_max:
        status = "BUSY"
        reason = "heavy_job_or_ocr_worker_running"
    elif decision == "resource_limit":
        status = "RESOURCE_LIMIT"
        reason = "admission_budget_below_required"
    elif decision == "unknown_capacity":
        status = "UNKNOWN"
        reason = "memory_metrics_unavailable"
    else:
        status = "AVAILABLE"
        reason = "admission_ok"

    return {
        "status": status,
        "observed_at": usage["observed_at"],
        "observed_at_iso": usage["observed_at_iso"],
        "freshness": "live",
        "ocr_enabled": enabled,
        "ocr_busy": workers > 0 or active > 0,
        "active_heavy_jobs": active,
        "max_heavy_jobs": max_heavy_jobs(),
        "running_jobs": running_jobs,
        "admission_state": {
            BUSY: "rejected_busy",
            RESOURCE_LIMIT: "rejected_resource_limit",
            UNKNOWN_CAPACITY: "fail_closed",
        }.get(status, status),
        "admission_reason": reason,
        "resource_limits": {
            "ocr_max_concurrency": configured_max,
            "ocr_max_rss_mb_virtual_address_space": int(
                os.getenv("ENG_DRAWING_OCR_MAX_RSS_MB", "0") or 0
            )
            or None,
            "ocr_cpu_seconds": int(
                os.getenv("ENG_DRAWING_OCR_CPU_SECONDS", "0") or 0
            )
            or None,
            "isolation": subprocess_executor.isolation_mode(),
            "job_running_cap_s": 2700,
            "job_result_ttl_s": 3600,
        },
        "resource_usage": {
            "observed_at": usage["observed_at"],
            "observed_at_iso": usage["observed_at_iso"],
            "scope": ["host", "container"],
            "memory": usage["memory"],
            "cpu": usage["cpu"],
            "ocr": {
                "configured_max_concurrency": configured_max,
                "active_workers": workers,
                "available_slots": max(0, configured_max - workers),
            },
        },
        "budget_check": budget_detail,
        "result": {
            "process_local_jobs": True,
            "restart_loses_jobs": True,
            "notes": usage.get("notes") or [],
        },
    }
