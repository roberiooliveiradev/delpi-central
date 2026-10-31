"""R2 regression suite — produto 90264302 (CHICOTE DE LIGACAO).

Reproduces the real defect: read(product.drawing) returned
found=true/90264302.pdf but analyze() answered drawing_not_found —
the delegated envelope {"status","data"} was not unwrapped.
"""

from __future__ import annotations

import pytest

from engineering_app.application.drawing.drawing_analysis_service import (
    DrawingAnalysisError,
    analyze_product_drawing,
)
from engineering_app.application.drawing.drawing_contracts import (
    unwrap_delegated,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    extract_pdf_text,
)
from engineering_app.domain.drawing.visual_observation import (
    parse_visual_observations,
)
from tests.test_drawing_analysis import _minimal_pdf


class _EnvelopeSource:
    """Realistic delegated gateway: {"status","data"} envelopes."""

    def __init__(self, pdf: bytes):
        self._pdf = pdf

    async def fetch_product_detail(self, ctx, *, code, view="engineering"):
        return {
            "status": "available",
            "data": {
                "product": {
                    "code": code,
                    "description": "CHICOTE DE LIGACAO",
                    "product_type": "PA",
                    "current_revision": "001",
                    "drawing_code": "90264302",
                }
            },
        }

    async def fetch_product_drawing(self, ctx, *, code):
        return {
            "status": "available",
            "data": {
                "found": True,
                "filename": "90264302.pdf",
                "size_bytes": 103498,
                "revision": None,
            },
        }

    async def fetch_product_drawing_pdf(self, ctx, *, code):
        return {"status": "available", "content": self._pdf}

    async def fetch_product_structure(self, ctx, **kw):
        return {
            "status": "available",
            "data": {
                "root": {
                    "items": [
                        {"code": "50226113",
                         "description": "CABO INTERMEDIARIO CA 0,75 PRET "
                                        "-00643/00/00-0000-0000",
                         "product_type": "PI", "quantity": 1,
                         "unit": "PC"},
                        {"code": "50226114",
                         "description": "CABO INTERMEDIARIO CA 0,75 VERD "
                                        "-00663/00/00-0000-0000",
                         "product_type": "PI", "quantity": 1,
                         "unit": "PC"},
                        {"code": "10020033",
                         "description": "CABO FLEX 0,75MM PRETO",
                         "product_type": "MP", "quantity": 643,
                         "unit": "MT"},
                        {"code": "10080106",
                         "description": "TERM. PINO 0,75MM",
                         "product_type": "MP", "quantity": 1000,
                         "unit": "PC"},
                    ]
                }
            },
        }


PDF_90264302 = _minimal_pdf(
    "CHICOTE DE LIGACAO 90264302 REV 00 CABO 643MM 663MM TERM PC"
)


async def test_t02_analyze_recovers_same_drawing():
    """T02: envelope is unwrapped — no spurious drawing_not_found."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    assert report["identification"]["product_code"] == "90264302"
    assert report["identification"]["drawing_file"] == "90264302.pdf"


async def test_t03_pdf_bytes_signature():
    """T03: bytes accessible, signature valid, extraction works."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["legibility"] == "PASS"
    assert report["audit"]["document_hash_sha256"]


async def test_t08_revision_00_vs_001_is_inconclusive_not_mismatch():
    """T08/R5: '00' vs '001' — different width ⇒ different control."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["revision"] == "INCONCLUSIVE"
    assert not any(
        f["category"] == "revision" and f["divergence"] == "revision_mismatch"
        for f in report["findings"]
    )


async def test_t09_t11_bom_pi_and_quantities_no_fake_error():
    """T09/T11/R4: PI 50226113/114 found; 643MT/663MT/1000PC honest."""
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["bom_comparison"] in {"PASS", "WARNING"}
    assert keys["quantity_semantics"] == "INCONCLUSIVE"
    assert keys["pi_items_descriptions"] in {"PASS", "WARNING"}
    assert report["executive_summary"]["bom_items_compared"] == 4
    # sem conversão inventada — nenhum finding de divergência de qty
    assert not any(
        "quantity" in (f["divergence"] or "") for f in report["findings"]
    )


async def test_t10_visual_length_observations_accepted():
    obs = parse_visual_observations([
        {"kind": "dimension",
         "raw_observation": "comprimento 643 mm",
         "normalized_value": "643", "unit": "MM", "page": 1,
         "document_identity": {"product_code": "90264302"}},
        {"kind": "dimension",
         "raw_observation": "comprimento 663 mm",
         "normalized_value": "663", "unit": "MM", "page": 1,
         "document_identity": {"product_code": "90264302"}},
    ])
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None,
        visual_observations=obs,
    )
    assert len(report["visual_observations"]) == 2
    assert report["source_match"] in {"possible_match", "unknown"}


async def test_t13_t16_full_report_and_pending_contracts():
    report = await analyze_product_drawing(
        code="90264302", source=_EnvelopeSource(PDF_90264302), ctx=None
    )
    sections = report["sections"]
    assert sections["H_technical_review"]["status"] == "DRAFT"
    assert sections["H_technical_review"]["automatic_approval"] is False
    inconclusive_keys = {
        v["key"] for v in sections["F_inconclusions"]
    }
    assert {"routing", "inspection", "pa_description"} <= inconclusive_keys
    assert report["contract_version"] == "drawing_analysis.v3"


class _ForbiddenSource(_EnvelopeSource):
    async def fetch_product_drawing(self, ctx, *, code):
        return {"status": "forbidden", "reason": "owner_denied"}


async def test_forbidden_not_mislabeled_as_not_found():
    with pytest.raises(DrawingAnalysisError) as exc:
        await analyze_product_drawing(
            code="90264302", source=_ForbiddenSource(b""), ctx=None
        )
    assert exc.value.code == "forbidden"
    assert exc.value.status_code == 403


class _UnavailableSource(_EnvelopeSource):
    async def fetch_product_drawing(self, ctx, *, code):
        return {"status": "unavailable", "reason": "upstream_error"}


async def test_unavailable_not_mislabeled_as_not_found():
    with pytest.raises(DrawingAnalysisError) as exc:
        await analyze_product_drawing(
            code="90264302", source=_UnavailableSource(b""), ctx=None
        )
    assert exc.value.code == "source_unavailable"


def test_unwrap_delegated_envelope_and_raw():
    assert unwrap_delegated(
        {"status": "available", "data": {"found": True}},
        what="x", not_found_code="n", not_found_message="m",
    ) == {"found": True}
    assert unwrap_delegated(
        {"found": True}, what="x", not_found_code="n",
        not_found_message="m",
    ) == {"found": True}
    with pytest.raises(DrawingAnalysisError):
        unwrap_delegated("x", what="x", not_found_code="n",
                         not_found_message="m")


def test_t03_extraction_pages_and_evidence():
    result = extract_pdf_text(PDF_90264302)
    assert result.page_count == 1
    assert "90264302" in result.pages[0].text
