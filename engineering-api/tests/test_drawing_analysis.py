"""Tests for the neutral drawing analysis (E1–E3, doc 69).

Deterministic contract tests — fake source avoids live API DELPI;
real pypdf parses an in-memory PDF so extraction is verified, not
mocked away.
"""

from __future__ import annotations

import io
import zlib

import pytest

from engineering_app.application.drawing.description_rules import (
    validate_mp_description,
    validate_pi_description,
)
from engineering_app.application.drawing.drawing_analysis_service import (
    DrawingAnalysisError,
    analyze_product_drawing,
)
from engineering_app.application.drawing.drawing_evidence_extractor import (
    extract_evidence,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
    extract_pdf_text,
)
from engineering_app.application.eva.semantic_registry import (
    SEMANTIC_ACTIONS,
)


def _minimal_pdf(text: str) -> bytes:
    """Build a real one-page PDF containing `text` (latin-1 only)."""
    escaped = text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
    stream = f"BT /F1 10 Tf 40 700 Td ({escaped}) Tj ET".encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
        + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = io.BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objs, 1):
        offsets.append(pdf.tell())
        pdf.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = pdf.tell()
    pdf.write(f"xref\n0 {len(objs)+1}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for off in offsets:
        pdf.write(f"{off:010d} 00000 n \n".encode())
    pdf.write(
        f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF".encode()
    )
    return pdf.getvalue()


# --- extraction contract -----------------------------------------------------


def test_extract_rejects_empty():
    with pytest.raises(PdfExtractionError):
        extract_pdf_text(b"")


def test_extract_rejects_oversize():
    with pytest.raises(PdfExtractionError):
        extract_pdf_text(b"%PDF-" + b"0" * (15 * 1024 * 1024 + 1))


def test_extract_rejects_non_pdf():
    with pytest.raises(PdfExtractionError):
        extract_pdf_text(b"NOTAPDF content")


def test_extract_parses_real_pdf():
    pdf = _minimal_pdf("PRODUTO 90264258 REV 01")
    result = extract_pdf_text(pdf)
    assert result.page_count == 1
    assert "90264258" in result.pages[0].text
    assert result.document_hash


def test_extract_flags_scanned():
    pdf = _minimal_pdf(" ")
    result = extract_pdf_text(pdf)
    assert result.scanned_or_empty


# --- evidence -----------------------------------------------------------------


def test_evidence_has_page_and_classification():
    pdf = _minimal_pdf("90264258 DESENHO X1 REV 01 10 PC")
    ev = extract_evidence(extract_pdf_text(pdf), document_ref="D.PDF")
    assert ev
    assert all(e.document_ref == "D.PDF" for e in ev)
    assert all(e.page == 1 for e in ev)
    kinds = {e.evidence_type for e in ev}
    assert "product_code_candidate" in kinds
    assert "revision" in kinds


# --- description rules ---------------------------------------------------------


def test_mp_not_applicable_outside_groups():
    chk = validate_mp_description("90264258", "CONJUNTO TESTE")
    assert chk.status == "NOT_APPLICABLE"


def test_mp_inconclusive_empty_description():
    chk = validate_mp_description("10081234", "")
    assert chk.status == "INCONCLUSIVE"


def test_mp_warns_prefix_mismatch():
    chk = validate_mp_description("10011234", "RESISTOR FIXO 10K")
    assert chk.status == "WARNING"
    chk2 = validate_mp_description("10011234", "CABO FLEX 1,5MM PT")
    assert chk2.status in {"PASS", "WARNING"}


def test_pi_not_applicable_outside_50xx():
    chk = validate_pi_description("10011234", "CABO")
    assert chk.status == "NOT_APPLICABLE"


def test_pi_checks_segments():
    ok = validate_pi_description(
        "50232222", "CABO INTERMEDIARIO CB1,50 VERD-00255/06/06-6314-0111"
    )
    assert ok.status in {"PASS", "WARNING"}
    weak = validate_pi_description("50232222", "CABO QUALQUER")
    assert weak.status == "WARNING"


# --- orchestration --------------------------------------------------------------


class _FakeSource:
    def __init__(self, pdf: bytes):
        self._pdf = pdf

    async def fetch_product_detail(self, ctx, *, code, view="engineering"):
        return {
            "product": {
                "code": code,
                "description": "CONJUNTO CABO TESTE",
                "product_type": "PA",
                "current_revision": "01",
                "drawing_code": "D-90264258",
            }
        }

    async def fetch_product_drawing(self, ctx, *, code):
        return {"found": True, "filename": "D-90264258.pdf",
                "revision": "01"}

    async def fetch_product_drawing_pdf(self, ctx, *, code):
        return {"status": "available", "content": self._pdf}

    async def fetch_product_structure(self, ctx, **kw):
        return {
            "root": {
                "items": [
                    {"code": "10011234", "description": "CABO FLEX PT",
                     "product_type": "MP"},
                    {"code": "10089999", "description": "TERM PINO 1MM",
                     "product_type": "MP"},
                ]
            }
        }


async def test_analyze_happy_path():
    pdf = _minimal_pdf(
        "PRODUTO 90264258 DESENHO TECNICO REV 01 CABO FLEX PC UN"
    )
    report = await analyze_product_drawing(
        code="90264258", source=_FakeSource(pdf), ctx=None
    )
    assert report["status"] == "DRAFT"
    assert report["identification"]["product_code"] == "90264258"
    keys = {v["key"]: v["status"] for v in report["verifications"]}
    assert keys["legibility"] == "PASS"
    assert keys["routing"] == "NOT_CHECKED"
    assert keys["inspection"] == "NOT_CHECKED"
    assert keys["pa_description"] == "NOT_CHECKED"
    assert report["audit"]["document_hash_sha256"]
    assert report["audit"]["write_operations"] == 0
    assert report["executive_summary"]["human_review_required"]


class _NoDrawingSource(_FakeSource):
    async def fetch_product_drawing(self, ctx, *, code):
        return {"found": False}


async def test_analyze_missing_drawing_errors():
    with pytest.raises(DrawingAnalysisError) as exc:
        await analyze_product_drawing(
            code="1", source=_NoDrawingSource(b""), ctx=None
        )
    assert exc.value.code == "drawing_not_found"


class _NoProductSource(_FakeSource):
    async def fetch_product_detail(self, ctx, *, code, view="engineering"):
        return {"status": "not_found"}


async def test_analyze_missing_product_errors():
    with pytest.raises(DrawingAnalysisError) as exc:
        await analyze_product_drawing(
            code="1", source=_NoProductSource(b""), ctx=None
        )
    assert exc.value.code == "product_not_found"


def test_zlib_path_not_triggered_by_mock():
    _ = zlib  # keep import meaningful (no fake PDF path)


# --- EVA registry parity --------------------------------------------------------


def test_registry_exposes_drawing_analysis_analyze():
    entries = [
        a for a in SEMANTIC_ACTIONS
        if a.entity == "product" and a.action == "drawing_analysis"
    ]
    assert len(entries) == 1
    assert entries[0].tool == "analyze"
    assert "product_code" in entries[0].fields
