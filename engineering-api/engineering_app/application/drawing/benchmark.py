"""Reproducible extraction benchmark harness (R6A-11/14).

Runs the same document through selected providers under the neutral
contract and emits serializable run records. Precision/recall require
owner-approved labels — absent them, quality fields stay
`metric_not_available`.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from engineering_app.infrastructure.extraction.registry import (
    resolve_extraction_provider,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
)


def run_extraction_benchmark(
    pdf_bytes: bytes,
    *,
    providers: list[str] | None = None,
    corpus_id: str = "local",
    environment: str = "test",
) -> list[dict[str, Any]]:
    """Execute providers over the same bytes → run records (JSON-safe)."""
    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
    records: list[dict[str, Any]] = []
    for pid in providers or ["pypdf_baseline"]:
        rec: dict[str, Any] = {
            "run_id": uuid.uuid4().hex[:12],
            "corpus_id": corpus_id,
            "environment": environment,
            "provider_id": pid,
            "document_hash": doc_hash,
            "input_bytes": len(pdf_bytes),
            "precision": "metric_not_available",
            "recall": "metric_not_available",
        }
        try:
            adapter = resolve_extraction_provider(
                pid, allow_experimental=True
            )
            desc = adapter.capability_descriptor()
            rec["provider_version"] = desc.version
            rec["provider_status"] = desc.status
            t0 = time.monotonic()
            result = adapter.extract(pdf_bytes)
            rec.update(
                {
                    "duration_ms": round(
                        (time.monotonic() - t0) * 1000
                    ),
                    "status": "ok",
                    "page_count": result.page_count,
                    "pages_processed": result.pages_processed,
                    "text_chars": result.text_chars,
                    "scanned_or_empty": result.scanned_or_empty,
                    "limitations": result.limitations,
                    "has_positional_data": bool(
                        result.metadata.get("positional_words")
                    ),
                }
            )
        except PdfExtractionError as exc:
            rec["status"] = "extraction_error"
            rec["error"] = str(exc)
        except Exception as exc:  # provider resolution/infra failure
            rec["status"] = "provider_error"
            rec["error"] = f"{type(exc).__name__}:{exc}"
        records.append(rec)
    return records


def records_to_jsonl(records: list[dict[str, Any]]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
