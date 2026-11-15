"""Operational resource monitor — lowest-privilege readers (RQ-OPS).

Métricas reais do próprio processo/container — sem Docker Socket,
sem introspecção de outros containers/tenants:

- ``/proc/meminfo`` — visão do HOST (proc não é namespaced para
  memória): escopo ``host``, sempre rotulado.
- ``/sys/fs/cgroup`` (v2, fallback v1) — limite e uso do CONTAINER:
  escopo ``container``. Quando o cgroup não limita, o bound efetivo
  é a memória do host — marcado ``bounded=False``.
- ``/proc/loadavg`` + ``os.cpu_count`` + cgroup cpu.max — CPU.

Semânticas distintas (nunca trocar uma pela outra):

- ``host_available_mb`` — MemAvailable do host inteiro;
- ``container_remaining_mb`` — espaço até o limite do cgroup;
- ``RLIMIT_AS`` — espaço de ENDEREÇAMENTO VIRTUAL do worker OCR
  (não é RSS, não é memória livre — ver subprocess_executor).

Métricas indisponíveis retornam ``None`` + escopo ``UNKNOWN`` —
nunca fabricadas.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

_PROC_MEMINFO = Path("/proc/meminfo")
_PROC_LOADAVG = Path("/proc/loadavg")
_CG2_ROOT = Path("/sys/fs/cgroup")
_CG1_MEM = Path("/sys/fs/cgroup/memory")
_CG1_CPU = Path("/sys/fs/cgroup/cpu")

_ADMISSION_MIN_MB_ENV = "ENG_DRAWING_ADMISSION_MIN_AVAILABLE_MB"
_HEADROOM_MB_ENV = "ENG_DRAWING_ADMISSION_HOST_HEADROOM_MB"
_DEFAULT_ADMISSION_MIN_MB = 2560  # pico medido do worker ~2–2,5GB
_DEFAULT_HEADROOM_MB = 1024  # reserva do host + serviços vizinhos


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default
    return max(lo, min(value, hi))


def admission_min_available_mb() -> int:
    return _int_env(
        _ADMISSION_MIN_MB_ENV, _DEFAULT_ADMISSION_MIN_MB, 256, 65536
    )


def admission_headroom_mb() -> int:
    return _int_env(
        _HEADROOM_MB_ENV, _DEFAULT_HEADROOM_MB, 0, 65536
    )


def read_meminfo(path: Path = _PROC_MEMINFO) -> dict[str, int] | None:
    """MemTotal/MemAvailable/Swap do HOST (kB→MB). ``None`` se ilegível."""
    try:
        fields: dict[str, int] = {}
        for line in path.read_text().splitlines():
            key, _, rest = line.partition(":")
            if key in {
                "MemTotal", "MemFree", "MemAvailable",
                "SwapTotal", "SwapFree",
            }:
                fields[key] = int(rest.strip().split()[0]) // 1024
        return fields or None
    except Exception:
        return None


def _read_int(path: Path) -> int | None:
    try:
        raw = path.read_text().strip()
        return None if raw in {"", "max"} else int(raw)
    except Exception:
        return None


def read_container_memory(
    cg2: Path = _CG2_ROOT, cg1: Path = _CG1_MEM
) -> dict[str, int | None] | None:
    """Limite/uso do cgroup do container (bytes→MB); ``None`` = sem dados."""
    limit = _read_int(cg2 / "memory.max")
    current = _read_int(cg2 / "memory.current")
    if limit is None and current is None:
        limit = _read_int(cg1 / "memory.limit_in_bytes")
        current = _read_int(cg1 / "memory.usage_in_bytes")
        # cgroup v1 sem bound reporta um teto absurdo — tratar como
        # unbounded em vez de apresentar um limite fictício.
        if limit is not None and limit >= 1 << 60:
            limit = None
    if limit is None and current is None:
        return None
    mb = lambda b: None if b is None else int(b) // (1024 * 1024)
    return {"limit_mb": mb(limit), "used_mb": mb(current)}


def read_cpu(
    loadavg_path: Path = _PROC_LOADAVG,
    cg2: Path = _CG2_ROOT,
    cg1: Path = _CG1_CPU,
) -> dict[str, Any]:
    """load1/cpu_count + quota cgroup (cpus efetivas) — honesto, sem amostragem."""
    out: dict[str, Any] = {}
    try:
        parts = loadavg_path.read_text().split()
        out["load1"] = float(parts[0])
        out["load5"] = float(parts[1])
    except Exception:
        out["load1"] = None
        out["load5"] = None
    out["cpu_count"] = os.cpu_count()
    quota = _read_int(cg2 / "cpu.max")
    period = None
    try:
        raw = (cg2 / "cpu.max").read_text().split()
        quota = None if raw[0] == "max" else int(raw[0])
        period = int(raw[1]) if len(raw) > 1 else 100000
    except Exception:
        q = _read_int(cg1 / "cpu.cfs_quota_us")
        p = _read_int(cg1 / "cpu.cfs_period_us")
        if q is not None and p:
            quota, period = q, p
    out["configured_limit_cpus"] = (
        round(quota / period, 3) if quota and period else None
    )
    return out


def resource_usage(
    *,
    meminfo_path: Path = _PROC_MEMINFO,
    cg2: Path = _CG2_ROOT,
    cg1_mem: Path = _CG1_MEM,
    cg1_cpu: Path = _CG1_CPU,
    loadavg_path: Path = _PROC_LOADAVG,
) -> dict[str, Any]:
    """Snapshot de recursos com escopo e timestamp — sem estimativas."""
    host = read_meminfo(meminfo_path)
    cont = read_container_memory(cg2, cg1_mem)
    cpu = read_cpu(loadavg_path, cg2, cg1_cpu)

    host_available = host.get("MemAvailable") if host else None
    cont_limit = cont.get("limit_mb") if cont else None
    cont_used = cont.get("used_mb") if cont else None
    cont_remaining = (
        cont_limit - cont_used
        if cont_limit is not None and cont_used is not None
        else None
    )
    # Orçamento de admissão = o mais restritivo dos bounds
    # comprovados, menos a reserva de headroom do host.
    bounds = [b for b in (host_available, cont_remaining) if b is not None]
    budget = (
        max(0, min(bounds) - admission_headroom_mb())
        if bounds
        else None
    )
    return {
        "observed_at": round(time.time(), 3),
        "observed_at_iso": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        ),
        "memory": {
            "host_scope": {
                "total_mb": host.get("MemTotal") if host else None,
                "available_mb": host_available,
                "swap_total_mb": host.get("SwapTotal") if host else None,
                "swap_free_mb": host.get("SwapFree") if host else None,
                "state": "KNOWN" if host else "UNKNOWN",
            },
            "container_scope": {
                "effective_limit_mb": cont_limit,
                "used_mb": cont_used,
                "remaining_mb": cont_remaining,
                "bounded": cont_limit is not None,
                "state": "KNOWN" if cont else "UNKNOWN",
            },
            "admission_budget_mb": budget,
            "admission_required_mb": admission_min_available_mb(),
            "host_headroom_mb": admission_headroom_mb(),
        },
        "cpu": {
            "load1": cpu.get("load1"),
            "load5": cpu.get("load5"),
            "cpu_count": cpu.get("cpu_count"),
            "configured_limit_cpus": cpu.get("configured_limit_cpus"),
            "state": "KNOWN" if cpu.get("load1") is not None else "UNKNOWN",
        },
        "notes": [
            "RLIMIT_AS governa espaço de endereçamento virtual do "
            "worker OCR — não é memória livre nem RSS.",
            "Métricas de terceiros/outros containers não são "
            "observáveis por este processo.",
        ],
    }


def admission_budget_check(usage: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    """Decisão de orçamento — fail-closed quando a métrica falta.

    Retorna ``("ok"|"resource_limit"|"unknown_capacity", detail)``.
    """
    usage = usage or resource_usage()
    budget = usage["memory"]["admission_budget_mb"]
    required = usage["memory"]["admission_required_mb"]
    detail = {
        "admission_budget_mb": budget,
        "admission_required_mb": required,
        "memory_state": {
            "host": usage["memory"]["host_scope"]["state"],
            "container": usage["memory"]["container_scope"]["state"],
        },
    }
    if budget is None:
        return "unknown_capacity", detail
    if budget < required:
        return "resource_limit", detail
    return "ok", detail
