"""R6-C: authorized official-document benchmark bridge tests."""

from __future__ import annotations

import hashlib

import pytest

from engineering_app.application.drawing.document_benchmark_service import (
    reconcile_provider_fields,
    run_official_document_benchmark,
)
from engineering_app.application.drawing.drawing_contracts import (
    DrawingAnalysisError,
)
from tests.test_drawing_analysis_r2 import _EnvelopeSource, PDF_90264302


async def test_bridge_fetches_official_bytes_and_runs_same_hash():
    out = await run_official_document_benchmark(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None,
        providers=["pypdf_baseline"],
    )
    doc = out["document"]
    assert doc["filename"] == "90264302.pdf"
    assert doc["document_hash_sha256"] == hashlib.sha256(
        PDF_90264302
    ).hexdigest()
    assert doc["source"] == "api_delpi_product_drawing_pdf"
    assert "access_token" not in repr(out) and "token" not in str(doc)
    assert out["same_document_verified"] is True
    assert out["runs"][0]["provider_id"] == "pypdf_baseline"
    assert out["runs"][0]["document_hash"] == doc[
        "document_hash_sha256"]
    assert "text" not in out["runs"][0]  # sem texto integral no record


async def test_bridge_error_when_pdf_unavailable():
    class _NoPdf(_EnvelopeSource):
        async def fetch_product_drawing_pdf(self, ctx, *, code):
            return {"status": "unavailable", "reason": "upstream"}

    with pytest.raises(DrawingAnalysisError) as exc:
        await run_official_document_benchmark(
            code="90264302", source=_NoPdf(b""), ctx=None
        )
    assert exc.value.code == "drawing_pdf_unavailable"


def test_reconcile_fields_coverage_matrix():
    runs = [
        {"provider_id": "pypdf", "status": "ok",
         "_text_blob": "90264302 CABO 643MM"},
        {"provider_id": "pdfplumber", "status": "ok",
         "_text_blob": "90264302 10080106"},
        {"provider_id": "pdfium", "status": "provider_error"},
    ]
    out = reconcile_provider_fields(
        runs, ["90264302", "10080106", "ZZZ"]
    )
    assert out["fields"]["90264302"] == {
        "pypdf": "found", "pdfplumber": "found", "pdfium": "not_run"
    }
    assert out["fields"]["10080106"]["pypdf"] == "not_found"
    assert out["fields"]["ZZZ"]["pdfplumber"] == "not_found"
    assert out["coverage_summary"]["missing_everywhere"] == 1
