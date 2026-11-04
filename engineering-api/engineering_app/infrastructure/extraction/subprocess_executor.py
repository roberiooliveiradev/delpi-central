"""Isolated visual-pipeline executor — bounded subprocess (R7.1).

Real OS-level isolation, not a thread wrapper:

- ``RLIMIT_AS`` — hard address-space cap (child dies on excess).
- ``RLIMIT_CPU`` — hard CPU-seconds cap (SIGXCPU kill).
- own process group + ``SIGKILL`` on timeout/cancel — a stuck native
  PaddleOCR call is actually terminated and reaped (no orphans).
- ``BoundedSemaphore`` — governed max concurrency (default 1).
- ``RUSAGE_CHILDREN`` — measured child peak RSS in the run record.
- bytes in via stdin, evidence out via stdout — nothing persisted,
  no JWT, no acervo access inside the worker.

Limits: ``ENG_DRAWING_OCR_MAX_RSS_MB`` (3072), ``ENG_DRAWING_OCR_CPU_
SECONDS`` (300), ``ENG_DRAWING_OCR_MAX_CONCURRENCY`` (1).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from typing import Any

_REQUEST_SCHEMA = "drawing_ocr_execution.v1"
_RESPONSE_SCHEMA = "drawing_ocr_result.v1"
_WORKER_MODULE = (
    "engineering_app.infrastructure.extraction.visual_worker"
)

_MAX_RSS_MB_ENV = "ENG_DRAWING_OCR_MAX_RSS_MB"
_CPU_SECONDS_ENV = "ENG_DRAWING_OCR_CPU_SECONDS"
_CONCURRENCY_ENV = "ENG_DRAWING_OCR_MAX_CONCURRENCY"

_DEFAULT_RSS_MB = 12288
_DEFAULT_CPU_SECONDS = 300
_DEFAULT_TIMEOUT_S = 180.0
_DEFAULT_CONCURRENCY = 1

_semaphore = threading.BoundedSemaphore(_DEFAULT_CONCURRENCY)


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default
    return max(lo, min(value, hi))


def max_concurrency() -> int:
    return _int_env(_CONCURRENCY_ENV, _DEFAULT_CONCURRENCY, 1, 4)


def _limits() -> dict[str, int]:
    return {
        "max_rss_mb": _int_env(_MAX_RSS_MB_ENV, _DEFAULT_RSS_MB, 512, 16384),
        "cpu_seconds": _int_env(_CPU_SECONDS_ENV, _DEFAULT_CPU_SECONDS, 10, 3600),
        "max_concurrency": max_concurrency(),
    }


def _child_rusage_kb() -> int:
    try:
        import resource

        return int(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    except Exception:
        return 0


def _preexec_limits(mem_bytes: int, cpu_seconds: int):
    def _apply() -> None:  # pragma: no cover - runs in child
        import resource

        resource.setrlimit(
            resource.RLIMIT_AS, (mem_bytes, mem_bytes)
        )
        resource.setrlimit(
            resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 5)
        )
        resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))

    return _apply


def run_pipeline_isolated(
    pdf_bytes: bytes,
    *,
    pipeline_id: str,
    dpi: int = 200,
    timeout_s: float | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Execute one visual pipeline in a bounded, killable subprocess."""
    limits = _limits()
    # O timeout pai deve superar o RLIMIT_CPU do filho — senão documentos
    # extensos são mortos antes do teto de CPU e TODA a evidência coletada
    # é descartada (RQ-VAL-029: cobertura multipágina). O teto de CPU
    # permanece a proteção real contra runaway.
    timeout = float(
        timeout_s or max(_DEFAULT_TIMEOUT_S, limits["cpu_seconds"] + 60)
    )
    corr = correlation_id or uuid.uuid4().hex[:12]
    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
    record: dict[str, Any] = {
        "provider_id": pipeline_id,
        "pipeline_kind": "visual_ocr",
        "isolation": "subprocess",
        "correlation_id": corr,
        "document_hash": doc_hash,
        "input_bytes": len(pdf_bytes),
        "resource_limits": limits,
    }
    request = {
        "schema_version": _REQUEST_SCHEMA,
        "document_hash_sha256": doc_hash,
        "pdf_b64": base64.b64encode(pdf_bytes).decode("ascii"),
        "pipeline_id": pipeline_id,
        "dpi": dpi,
        "correlation_id": corr,
    }
    env = dict(os.environ)
    env.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
    rss_before = _child_rusage_kb()
    t0 = time.monotonic()
    acquired = _semaphore.acquire(timeout=timeout)
    if not acquired:
        record.update(
            {
                "status": "provider_error",
                "error": "ocr_concurrency_saturated",
                "limitations": ["max_concurrency_reached"],
            }
        )
        return record
    proc: subprocess.Popen | None = None
    try:
        try:
            proc = subprocess.Popen(
                [sys.executable, "-m", _WORKER_MODULE],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                env=env,
                start_new_session=True,
                preexec_fn=_preexec_limits(
                    limits["max_rss_mb"] * 1024 * 1024,
                    limits["cpu_seconds"],
                )
                if os.name == "posix"
                else None,
            )
        except Exception as exc:
            record.update(
                {
                    "status": "provider_error",
                    "error": f"spawn_failed:{exc.__class__.__name__}",
                }
            )
            return record
        record["worker_pid"] = proc.pid
        try:
            out, _ = proc.communicate(
                json.dumps(request).encode("utf-8"), timeout=timeout
            )
        except subprocess.TimeoutExpired:
            # REAL termination — kill the whole group, reap the child.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                proc.kill()
            proc.wait(timeout=10)
            record.update(
                {
                    "status": "extraction_error",
                    "error": f"ocr_timeout:{timeout:.0f}s_killed",
                    "duration_ms": round((time.monotonic() - t0) * 1000),
                    "child_reaped": proc.returncode is not None,
                    "terminated_by": "SIGKILL",
                }
            )
            return record
        record["duration_ms"] = round((time.monotonic() - t0) * 1000)
        try:
            response = json.loads(out.decode("utf-8") or "{}")
        except Exception:
            record.update(
                {
                    "status": "provider_error",
                    "error": f"worker_bad_response:rc={proc.returncode}",
                }
            )
            return record
        if not out.strip():
            # Worker morto por limite de recurso (RLIMIT_CPU/RSS) antes
            # de escrever o record — rc negativo expõe o sinal real;
            # nunca mascarar como schema_mismatch.
            record.update(
                {
                    "status": "provider_error",
                    "error": f"worker_no_output:rc={proc.returncode}",
                }
            )
            return record
        if response.get("schema_version") != _RESPONSE_SCHEMA:
            record.update(
                {
                    "status": "provider_error",
                    "error": "worker_schema_mismatch",
                }
            )
            return record
        inner = response.get("record") or {}
        if response.get("status") != "completed" or not inner:
            record.update(
                {
                    "status": "provider_error",
                    "error": response.get("error")
                    or f"worker_rc={proc.returncode}",
                }
            )
            return record
        # merge worker record with parent isolation/metrics envelope
        inner.update(
            {
                "isolation": "subprocess",
                "correlation_id": corr,
                "worker_pid": proc.pid,
                "worker_returncode": proc.returncode,
                "resource_limits": limits,
                "parent_duration_ms": record["duration_ms"],
            }
        )
        record = inner
    finally:
        _semaphore.release()
        if proc is not None and proc.poll() is None:  # orphan guard
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
    child_peak = _child_rusage_kb()
    record["memory_peak_kb"] = (
        max(0, child_peak - rss_before) or child_peak or None
    )
    record["child_rusage_kb"] = child_peak or None
    return record


def isolation_mode() -> str:
    """ENG_DRAWING_OCR_ISOLATION: subprocess (default) | inprocess."""
    mode = os.getenv("ENG_DRAWING_OCR_ISOLATION", "").strip().lower()
    return mode if mode in {"subprocess", "inprocess"} else "subprocess"
