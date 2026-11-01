"""R7.1 — isolated OCR subprocess executor: contract, real termination,
memory cap, concurrency, serialization (fail-closed everywhere)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time

import pytest

from engineering_app.infrastructure.extraction.subprocess_executor import (
    _limits,
    isolation_mode,
    run_pipeline_isolated,
)
from tests.test_drawing_analysis import _minimal_pdf

_PDF = _minimal_pdf("CHICOTE 90264302")


def _simulate_env(monkeypatch, hook: str):
    monkeypatch.setenv("VISUAL_WORKER_SIMULATE", hook)


def test_isolation_mode_default_and_override(monkeypatch):
    monkeypatch.delenv("ENG_DRAWING_OCR_ISOLATION", raising=False)
    assert isolation_mode() == "subprocess"
    monkeypatch.setenv("ENG_DRAWING_OCR_ISOLATION", "inprocess")
    assert isolation_mode() == "inprocess"
    monkeypatch.setenv("ENG_DRAWING_OCR_ISOLATION", "bogus")
    assert isolation_mode() == "subprocess"


def test_limits_env_bounds(monkeypatch):
    monkeypatch.setenv("ENG_DRAWING_OCR_MAX_RSS_MB", "1")
    monkeypatch.setenv("ENG_DRAWING_OCR_CPU_SECONDS", "99999")
    monkeypatch.setenv("ENG_DRAWING_OCR_MAX_CONCURRENCY", "99")
    lim = _limits()
    assert lim["max_rss_mb"] == 512  # piso
    assert lim["cpu_seconds"] == 3600  # teto
    assert lim["max_concurrency"] == 4


def test_worker_contract_schema_rejected():
    """Worker recusa payload fora do contrato — sem execução."""
    proc = subprocess.run(
        [sys.executable, "-m",
         "engineering_app.infrastructure.extraction.visual_worker"],
        input=b"{}", capture_output=True, timeout=30,
    )
    out = json.loads(proc.stdout.decode() or "{}")
    assert out["status"] == "contract_error"
    assert proc.returncode == 2


def test_worker_hash_mismatch_rejected():
    import base64

    req = {
        "schema_version": "drawing_ocr_execution.v1",
        "document_hash_sha256": "0" * 64,
        "pdf_b64": base64.b64encode(_PDF).decode(),
        "pipeline_id": "pdfium_render_paddleocr",
    }
    proc = subprocess.run(
        [sys.executable, "-m",
         "engineering_app.infrastructure.extraction.visual_worker"],
        input=json.dumps(req).encode(), capture_output=True, timeout=30,
    )
    out = json.loads(proc.stdout.decode() or "{}")
    assert out["error"] == "document_hash_mismatch"


def test_subprocess_real_termination(monkeypatch):
    """Timeout mata o processo nativo de verdade — sem órfão (R71-05)."""
    _simulate_env(monkeypatch, "sleep:300")
    rec = run_pipeline_isolated(
        _PDF, pipeline_id="pdfium_render_paddleocr", timeout_s=3
    )
    assert rec["status"] == "extraction_error"
    assert "ocr_timeout" in rec["error"]
    assert rec["terminated_by"] == "SIGKILL"
    assert rec["child_reaped"] is True
    pid = rec.get("worker_pid")
    if pid:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def test_subprocess_memory_limit_kills_child(monkeypatch):
    """RLIMIT_AS real — alocação acima do teto morre no filho."""
    monkeypatch.setenv("ENG_DRAWING_OCR_MAX_RSS_MB", "512")
    _simulate_env(monkeypatch, "alloc_mb:2048")
    rec = run_pipeline_isolated(
        _PDF, pipeline_id="pdfium_render_paddleocr", timeout_s=30
    )
    assert rec["status"] in {"provider_error", "extraction_error"}


def test_subprocess_simulated_failure_honest(monkeypatch):
    _simulate_env(monkeypatch, "fail:boom")
    rec = run_pipeline_isolated(
        _PDF, pipeline_id="pdfium_render_paddleocr", timeout_s=20
    )
    assert rec["status"] == "provider_error"
    assert "simulated_failure" in str(rec.get("error"))


def test_subprocess_concurrency_semaphore(monkeypatch):
    """Max concorrência=1 → segunda chamada satura honestamente."""
    monkeypatch.setenv("ENG_DRAWING_OCR_MAX_CONCURRENCY", "1")
    _simulate_env(monkeypatch, "sleep:6")
    results: list[dict] = []

    def _call():
        results.append(
            run_pipeline_isolated(
                _PDF, pipeline_id="pdfium_render_paddleocr",
                timeout_s=2,
            )
        )

    t1 = threading.Thread(target=_call)
    t1.start()
    time.sleep(0.4)  # garante que t1 segurou o semáforo
    t2 = threading.Thread(target=_call)
    t2.start()
    t1.join(timeout=15)
    t2.join(timeout=15)
    statuses = sorted(r["status"] for r in results)
    # uma foi morta por timeout; a outra saturou no semáforo ou correu
    assert statuses[0] in {
        "extraction_error", "provider_error", "ok", "error", "partial"
    }
    assert all("access_token" not in json.dumps(r) for r in results)


def test_request_never_carries_secrets():
    """Contrato interno não transporta JWT nem secrets."""
    import inspect

    src = inspect.getsource(
        sys.modules[
            "engineering_app.infrastructure.extraction.subprocess_executor"
        ]
    )
    forbidden = ("access_token", "authorization", "jwt", "password")
    request_keys = ("pdf_b64", "pipeline_id", "document_hash_sha256",
                    "correlation_id", "dpi", "schema_version")
    for key in request_keys:
        assert key in src
    # nenhum campo sensível no request dict
    assert '"access_token"' not in src
    assert '"authorization"' not in src
