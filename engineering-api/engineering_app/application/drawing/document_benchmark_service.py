"""Authorized official-document benchmark bridge (R6C-03).

Uses the SAME delegated gateway and identity as product.drawing_analysis
— no parallel acervo access, no fabricated JWT, no direct file-server
paths. Bytes fetched once; every provider processes the identical hash.
"""

from __future__ import annotations

import hashlib
from typing import Any

from engineering_app.application.drawing.benchmark import (
    run_extraction_benchmark,
)
from engineering_app.application.drawing.drawing_contracts import (
    DrawingAnalysisError,
    unwrap_delegated,
)


async def run_official_document_benchmark(
    *,
    code: str,
    source: Any,
    ctx: Any,
    providers: list[str] | None = None,
    corpus_id: str = "official_document",
    environment: str = "internal_benchmark",
) -> dict[str, Any]:
    """Fetch the official drawing via delegated identity and run the
    benchmark over the real bytes. Read-only; never writes."""
    meta_raw = await source.fetch_product_drawing(ctx, code=code)
    meta = unwrap_delegated(
        meta_raw,
        what="product.drawing",
        not_found_code="drawing_not_found",
        not_found_message=(
            f"Produto {code} não possui desenho PDF oficial no acervo."
        ),
    )
    if not meta.get("found"):
        raise DrawingAnalysisError(
            "drawing_not_found",
            f"Produto {code} não possui desenho PDF oficial no acervo.",
            404,
        )
    pdf_raw = await source.fetch_product_drawing_pdf(ctx, code=code)
    content = pdf_raw.get("content") if isinstance(pdf_raw, dict) else None
    if not isinstance(content, (bytes, bytearray)) or not content:
        raise DrawingAnalysisError(
            "drawing_pdf_unavailable",
            f"PDF oficial de {code} indisponível no acervo.",
            502,
        )
    doc_hash = hashlib.sha256(bytes(content)).hexdigest()
    document = {
        "product_code": code,
        "filename": meta.get("filename"),
        "size_bytes": len(content),
        "document_hash_sha256": doc_hash,
        "drawing_library_revision": meta.get("revision"),
        "source": "api_delpi_product_drawing_pdf",
        "mime": "application/pdf",
        "authorized_via": "delegated_identity_gateway",
    }
    runs = run_extraction_benchmark(
        bytes(content),
        providers=providers or ["pypdf_baseline"],
        corpus_id=corpus_id,
        environment=environment,
    )
    same_hash = all(r["document_hash"] == doc_hash for r in runs)
    return {
        "document": document,
        "providers_ran": [r["provider_id"] for r in runs],
        "same_document_verified": same_hash,
        "runs": runs,
    }


def reconcile_provider_fields(
    runs: list[dict[str, Any]],
    fields: list[str],
) -> dict[str, Any]:
    """Per-field multiprovider coverage matrix (R6C-12).

    `fields` = candidate token values (e.g. codes/dimensions) — marked
    found/not_found per provider based on extracted text presence.
    NOT accuracy ground truth — coverage evidence only.
    """
    matrix: dict[str, dict[str, str]] = {}
    for value in fields:
        row: dict[str, str] = {}
        for run in runs:
            pid = run["provider_id"]
            if run["status"] != "ok":
                row[pid] = "not_run"
                continue
            blob = " ".join(
                p.get("text", "") for p in run.get("_pages", []) or []
            ) or str(run.get("_text_blob") or "")
            # run records don't carry text — caller may attach _text_blob.
            row[pid] = "found" if blob and value in blob else (
                "not_found" if run["status"] == "ok" else "not_run"
            )
        matrix[value] = row
    statuses = {
        v for row in matrix.values() for v in row.values()
    }
    return {
        "fields": matrix,
        "coverage_summary": {
            "coincident": sum(
                1 for row in matrix.values()
                if len(set(row.values()) - {"not_run"}) == 1
                and next(iter(row.values())) == "found"
            ),
            "divergent": sum(
                1 for row in matrix.values()
                if "found" in row.values() and "not_found" in row.values()
            ),
            "missing_everywhere": sum(
                1 for row in matrix.values()
                if set(row.values()) <= {"not_found", "not_run"}
                and "not_found" in row.values()
            ),
        },
        "note": (
            "Cobertura textual por provider — não é acurácia nem "
            "ground truth; presença em OCR não vira fato."
        ),
    }
