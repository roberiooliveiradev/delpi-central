"""Isolated OCR worker — subprocess entrypoint (R7.1).

Runs the SAME governed pipeline code as the in-process path inside a
resource-limited, killable child process. Contract::

    stdin  ← drawing_ocr_execution.v1 JSON
             {document_hash_sha256, pdf_b64, pipeline_id, dpi,
              correlation_id, corpus_id, environment}
    stdout → drawing_ocr_result.v1 JSON
             {status, record, error?}

No JWT, no acervo access, no writes, no network contract — bytes in,
evidence out. ``VISUAL_WORKER_SIMULATE`` exists solely for controlled
termination tests (never set in production).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import time

_REQUEST_SCHEMA = "drawing_ocr_execution.v1"
_RESPONSE_SCHEMA = "drawing_ocr_result.v1"


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


def _simulate(hook: str) -> None:
    """Controlled-failure hook for isolation tests (opt-in env only)."""
    if hook.startswith("sleep:"):
        time.sleep(float(hook.split(":", 1)[1]))
    elif hook.startswith("alloc_mb:"):
        mb = int(hook.split(":", 1)[1])
        block = bytearray(mb * 1024 * 1024)
        block[0] = 1  # force real allocation
        time.sleep(0.2)
    elif hook.startswith("fail:"):
        raise RuntimeError(f"simulated_failure:{hook.split(':', 1)[1]}")


def main() -> int:
    try:
        request = json.loads(sys.stdin.read() or "{}")
    except Exception:
        _emit(
            {
                "schema_version": _RESPONSE_SCHEMA,
                "status": "contract_error",
                "error": "invalid_request_json",
            }
        )
        return 2
    if request.get("schema_version") != _REQUEST_SCHEMA:
        _emit(
            {
                "schema_version": _RESPONSE_SCHEMA,
                "status": "contract_error",
                "error": "schema_version_mismatch",
            }
        )
        return 2
    hook = os.environ.get("VISUAL_WORKER_SIMULATE", "").strip()
    if hook:
        try:
            _simulate(hook)
        except Exception as exc:
            _emit(
                {
                    "schema_version": _RESPONSE_SCHEMA,
                    "status": "error",
                    "error": str(exc),
                }
            )
            return 3
    try:
        pdf_bytes = base64.b64decode(request.get("pdf_b64") or "")
    except Exception:
        pdf_bytes = b""
    pipeline_id = str(request.get("pipeline_id") or "").strip()
    if not pdf_bytes or not pipeline_id:
        _emit(
            {
                "schema_version": _RESPONSE_SCHEMA,
                "status": "contract_error",
                "error": "missing_pdf_b64_or_pipeline_id",
            }
        )
        return 2
    declared = request.get("document_hash_sha256")
    actual = hashlib.sha256(pdf_bytes).hexdigest()
    if declared and declared != actual:
        _emit(
            {
                "schema_version": _RESPONSE_SCHEMA,
                "status": "contract_error",
                "error": "document_hash_mismatch",
            }
        )
        return 2

    from engineering_app.application.drawing.visual_benchmark import (
        run_visual_benchmark,
    )

    try:
        dpi = int(request.get("dpi") or 200)
    except Exception:
        dpi = 200
    records = run_visual_benchmark(
        pdf_bytes,
        pipelines=[pipeline_id],
        corpus_id=str(request.get("corpus_id") or "isolated"),
        environment=str(request.get("environment") or "subprocess"),
        dpi=dpi,
        isolation="inprocess",
        page_start=request.get("page_start"),
        page_end=request.get("page_end"),
    )
    _emit(
        {
            "schema_version": _RESPONSE_SCHEMA,
            "status": "completed",
            "document_hash_sha256": actual,
            "correlation_id": request.get("correlation_id"),
            "record": records[0] if records else None,
        }
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
