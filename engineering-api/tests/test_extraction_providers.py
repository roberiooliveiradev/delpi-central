"""R6-A provider interchangeability tests (T01–T24 core set)."""

from __future__ import annotations

import pytest

from engineering_app.application.drawing.benchmark import (
    records_to_jsonl,
    run_extraction_benchmark,
)
from engineering_app.application.drawing.drawing_analysis_service import (
    analyze_product_drawing,
)
from engineering_app.application.drawing.extraction_ports import (
    ProviderResolutionError,
)
from engineering_app.infrastructure.extraction.registry import (
    list_providers,
    resolve_extraction_provider,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
    PdfTextExtraction,
)
from tests.test_drawing_analysis import _minimal_pdf
from tests.test_drawing_analysis_r2 import _EnvelopeSource, PDF_90264302

PDF = _minimal_pdf("PRODUTO 90264302 DESENHO REV 01 CABO FLEX PC UN")


class _FakeAdapter:
    """Contractual fake — proves swap without touching domain (T02)."""

    def extract(self, pdf_bytes, *, filename=None):
        return PdfTextExtraction(
            document_hash="fakehash", pages=[],
            page_count=1, pages_processed=0, text_chars=0,
            scanned_or_empty=True,
            limitations=["fake_provider"],
        )

    def capability_descriptor(self):
        from engineering_app.application.drawing.extraction_ports import (
            ProviderCapability,
        )
        return ProviderCapability(
            provider_id="fake", version="0", status="experimental"
        )


def test_t01_pypdf_baseline_resolves_and_extracts():
    adapter = resolve_extraction_provider()
    assert adapter.capability_descriptor().provider_id == "pypdf_baseline"
    result = adapter.extract(PDF)
    assert result.document_hash
    assert result.text_chars > 40


async def test_t02_service_accepts_swap_via_extractor_param():
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302),
        ctx=None, extractor=_FakeAdapter(),
    )
    assert report["verifications"]
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    # fake yields no text → legibility inconclusive, não crash
    assert keys["legibility"] in {"INCONCLUSIVE", "WARNING"}


def test_t12_unknown_provider_rejected():
    with pytest.raises(ProviderResolutionError):
        resolve_extraction_provider("totally_made_up_provider")


def test_t13_experimental_id_alone_is_not_authorization():
    # R6B-02: ID explícito sem flag NÃO seleciona provider experimental.
    import pytest as _pt
    with _pt.raises(ProviderResolutionError):
        resolve_extraction_provider("pdfplumber_experimental")
    # backend autorizado resolve
    adapter = resolve_extraction_provider(
        "pdfplumber_experimental", allow_experimental=True
    )
    assert adapter is not None


def test_catalog_descriptor_contract():
    listed = {p["provider_id"] for p in list_providers()}
    assert "pypdf_baseline" in listed
    assert "pdfplumber_experimental" in listed
    for p in list_providers():
        assert p["descriptor"]["runs_local"] is True


def test_t20_no_fabricated_results_when_unavailable():
    adapter = resolve_extraction_provider(
        "pdfplumber_experimental", allow_experimental=True
    )
    desc = adapter.capability_descriptor()
    if desc.status == "unavailable":
        with pytest.raises(PdfExtractionError):
            adapter.extract(PDF)


def test_t16_benchmark_same_doc_two_providers():
    records = run_extraction_benchmark(
        PDF, providers=["pypdf_baseline", "pdfplumber_experimental"],
        corpus_id="t16",
    )
    assert len(records) == 2
    assert {r["provider_id"] for r in records} == {
        "pypdf_baseline", "pdfplumber_experimental"
    }
    assert all(r["document_hash"] == records[0]["document_hash"]
               for r in records)
    assert records[0]["status"] == "ok"
    assert all(r["precision"] == "metric_not_available" for r in records)
    jsonl = records_to_jsonl(records)
    assert len(jsonl.strip().splitlines()) == 2


def test_t10_invalid_pdf_rejected_by_baseline():
    adapter = resolve_extraction_provider()
    with pytest.raises(PdfExtractionError):
        adapter.extract(b"not-a-pdf")


def test_t15_domain_pure_of_provider_imports():
    """T15/T16: nenhum import de adapter/SDK no domínio/aplicação."""
    import inspect
    import engineering_app.domain.drawing as domain
    import engineering_app.application.drawing.pdf_text_extractor as ext

    src = inspect.getsource(ext)
    assert "pdfplumber" not in src
    assert "pymupdf" not in src.lower()


async def test_t21_service_default_provider_unchanged():
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    assert report["contract_version"] == "drawing_analysis.v3"
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["legibility"] == "PASS"
