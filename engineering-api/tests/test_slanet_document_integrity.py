"""Integridade documental do caminho SLANet — EVA #131 / VAL-01.

Regressão do defeito produtivo: uma falha na obtenção auxiliar do PDF
era transformada silenciosamente em ``b""`` e entregue ao PDFium,
produzindo ``PdfiumError: Failed to load document`` mascarado como
``UNAVAILABLE`` de modelo. O contrato agora exige:

1. O documento percebido é o MESMO obtido e validado pelo benchmark
   oficial na mesma execução autorizada — sem segunda busca.
2. Ausência/vazio/tipo inválido/divergência de SHA são erros tipados
   antes do PDFium, nunca ``UNAVAILABLE`` genérico.
3. Falha na abertura do PDF remove o arquivo temporário.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile

import pytest

from engineering_app.application.drawing.perception_contract import (
    ERROR_KINDS,
    make_result,
)
from engineering_app.application.drawing.understanding import (
    apply_native_table_observations,
)
from engineering_app.infrastructure.extraction import engine_adapters


FAKE_PDF = b"%PDF-1.4 fake-body for contract tests"


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


# --- contrato de erros ------------------------------------------------------


def test_document_error_kinds_are_in_the_closed_set():
    for kind in (
        "DOCUMENT_CONTENT_MISSING",
        "DOCUMENT_CONTENT_INVALID",
        "DOCUMENT_HASH_MISMATCH",
        "PDF_OPEN_FAILED",
    ):
        assert kind in ERROR_KINDS
        res = make_result(
            provider_id="x",
            provider_version="1",
            document_hash_sha256="",
            error_kind=kind,
        )
        assert res["error_kind"] == kind


# --- gates de entrada do motor ----------------------------------------------


def test_missing_bytes_is_typed_before_pdfium(monkeypatch):
    calls = []
    monkeypatch.setattr(
        engine_adapters,
        "_open_pdf_document",
        lambda _b: calls.append(_b) or (None, None),
    )
    engine = engine_adapters.TableStructureEngine()
    result = engine.run(b"", document_hash_sha256="a" * 64)
    assert result["error_kind"] == "DOCUMENT_CONTENT_MISSING"
    assert result["error_detail"]
    assert calls == []


def test_non_pdf_content_is_typed_invalid(monkeypatch):
    calls = []
    monkeypatch.setattr(
        engine_adapters,
        "_open_pdf_document",
        lambda _b: calls.append(_b) or (None, None),
    )
    engine = engine_adapters.TableStructureEngine()
    payload = b'{"status":"unavailable","reason":"timeout"}'
    result = engine.run(payload, document_hash_sha256=_sha(payload))
    assert result["error_kind"] == "DOCUMENT_CONTENT_INVALID"
    assert calls == []


def test_hash_mismatch_fails_closed_before_pdfium(monkeypatch):
    calls = []
    monkeypatch.setattr(
        engine_adapters,
        "_open_pdf_document",
        lambda _b: calls.append(_b) or (None, None),
    )
    engine = engine_adapters.TableStructureEngine()
    other = b"%PDF-1.4 different document"
    result = engine.run(other, document_hash_sha256="f" * 64)
    assert result["error_kind"] == "DOCUMENT_HASH_MISMATCH"
    assert calls == []


def test_pdfium_open_failure_is_typed_and_not_unavailable(monkeypatch):
    def boom(_bytes):
        raise RuntimeError("simulated pdfium failure")

    monkeypatch.setattr(engine_adapters, "_open_pdf_document", boom)
    engine = engine_adapters.TableStructureEngine()
    result = engine.run(FAKE_PDF, document_hash_sha256=_sha(FAKE_PDF))
    assert result["error_kind"] == "PDF_OPEN_FAILED"
    assert result["error_kind"] != "UNAVAILABLE"
    assert "RuntimeError" in (result["error_detail"] or "")


def test_open_pdf_document_removes_temp_file_on_failure(monkeypatch):
    import pypdfium2

    before = set(os.listdir(tempfile.gettempdir()))

    def boom(_path):
        raise RuntimeError("simulated pdfium failure")

    monkeypatch.setattr(pypdfium2, "PdfDocument", boom)
    with pytest.raises(RuntimeError):
        engine_adapters._open_pdf_document(b"%PDF-1.4 x")
    after = set(os.listdir(tempfile.gettempdir()))
    assert after - before == set()


class _FakeCrop:
    size = 1600


class _FakeImage:
    def __init__(self, width, height):
        self.shape = (height, width, 3)

    def __getitem__(self, _slice):
        return _FakeCrop()


def test_valid_document_reaches_engine(monkeypatch):
    class FakePdf:
        def __len__(self):
            return 1

        def close(self):
            return None

    monkeypatch.setattr(
        engine_adapters,
        "_open_pdf_document",
        lambda _b: (FakePdf(), "tmp"),
    )
    monkeypatch.setattr(
        engine_adapters,
        "_render_page",
        lambda _pdf, _index: {
            "image": _FakeImage(120, 80),
            "page_index": _index,
        },
    )
    monkeypatch.setattr(
        engine_adapters, "_predict_table_structure", lambda _crop: []
    )
    engine = engine_adapters.TableStructureEngine()
    result = engine.run(
        FAKE_PDF,
        document_hash_sha256=_sha(FAKE_PDF),
        pages=[1],
        crop_box=[0, 0, 40, 40],
        ocr_tokens=[],
    )
    assert result["error_kind"] is None
    assert result["pdf_sha_match"] is True
    assert result["source_pdf_sha256"] == _sha(FAKE_PDF)


# --- propagação ao consumidor ------------------------------------------------


def test_typed_document_error_reaches_table_perception():
    understanding = {
        "component_table": {"rows": [], "row_count": 0, "col_types": {}},
        "limitations": [],
    }
    updated = apply_native_table_observations(
        understanding,
        [
            {
                "region_type": "component_table",
                "page": 9,
                "result": {
                    "error_kind": "DOCUMENT_CONTENT_MISSING",
                    "error_detail": "document bytes absent",
                    "cells": [],
                    "source_pdf_sha256": "x" * 64,
                },
            }
        ],
    )
    perception = updated["table_perception"][0]
    assert perception["error_kind"] == "DOCUMENT_CONTENT_MISSING"
    assert perception["error_detail"] == "document bytes absent"
    assert perception["source_pdf_sha256"] == "x" * 64
    assert perception["cells"] == []
    assert "table_perception:DOCUMENT_CONTENT_MISSING" in updated[
        "limitations"
    ]


# --- reutilização do documento oficial (sem 2ª busca) -------------------------


class _CountingSource:
    def __init__(self):
        self.pdf_calls = 0

    async def fetch_product_drawing(self, ctx, *, code):
        return {
            "status": "available",
            "data": {
                "found": True,
                "filename": f"{code}.pdf",
                "revision": "A",
            },
        }

    async def fetch_product_drawing_pdf(self, ctx, *, code):
        self.pdf_calls += 1
        return {
            "status": "available",
            "status_code": 200,
            "content": FAKE_PDF,
            "content_type": "application/pdf",
            "filename": f"{code}.pdf",
        }

    async def fetch_product_structure(self, ctx, *, code, **_kw):
        return {"status": "available", "data": {"items": []}}


def _fake_benchmark_runs(pdf: bytes):
    doc_hash = _sha(pdf)
    return [
        {
            "status": "ok",
            "provider_id": "fake_visual",
            "document_hash": doc_hash,
            "token_count": 1,
            "dpi": 200,
            "pdf_page_count": 1,
            "_tokens_sample": [
                {
                    "raw_text": "ITEM",
                    "normalized_text": "ITEM",
                    "bounding_box_px": [1, 1, 5, 1, 5, 5, 1, 5],
                    "confidence": 0.9,
                    "page": 1,
                }
            ],
            "pages": [
                {
                    "page": 1,
                    "status": "ok",
                    "render": {"width": 100, "height": 80},
                }
            ],
        }
    ]


def test_produce_understanding_reuses_benchmark_bytes_single_fetch(
    monkeypatch,
):
    from engineering_app.interface.mcp import semantic_bridge as sem
    from engineering_app.interface.mcp import tool_bridge
    from engineering_app.application.drawing import (
        document_benchmark_service,
        visual_benchmark,
    )
    from tests.test_eva_mcp import _human_user, _set_context

    source = _CountingSource()
    monkeypatch.setattr(
        tool_bridge, "build_delegated_auxiliary_source", lambda: source
    )
    monkeypatch.setattr(
        visual_benchmark,
        "run_visual_benchmark",
        lambda pdf_bytes, **_kw: _fake_benchmark_runs(pdf_bytes),
    )
    seen = {}

    class FakeEngine:
        def run(self, pdf_bytes, **kwargs):
            seen["pdf_bytes"] = pdf_bytes
            return {
                "provider_id": "table_structure_slanet",
                "error_kind": None,
                "cells": [],
                "tables": [],
                "render": {},
                "document_hash_sha256": kwargs.get(
                    "document_hash_sha256"
                ),
            }

    monkeypatch.setattr(
        engine_adapters, "TableStructureEngine", lambda: FakeEngine()
    )
    _set_context(_human_user())
    context = object()
    monkeypatch.setattr(
        tool_bridge, "_source_context", lambda _c: object()
    )
    understanding, _structure, _best, _tokens, pdf_bytes = asyncio.run(
        sem._produce_drawing_understanding(context, "90264017")
    )
    assert source.pdf_calls == 1
    assert seen["pdf_bytes"] == FAKE_PDF
    assert pdf_bytes == FAKE_PDF


def test_produce_understanding_never_calls_pdfium_on_fetch_failure(
    monkeypatch,
):
    from engineering_app.interface.mcp import semantic_bridge as sem
    from engineering_app.interface.mcp import tool_bridge
    from engineering_app.application.drawing.drawing_contracts import (
        DrawingAnalysisError,
    )
    from tests.test_eva_mcp import _human_user, _set_context

    class _FailingSource(_CountingSource):
        async def fetch_product_drawing_pdf(self, ctx, *, code):
            self.pdf_calls += 1
            return {"status": "unavailable", "reason": "timeout"}

    source = _FailingSource()
    monkeypatch.setattr(
        tool_bridge, "build_delegated_auxiliary_source", lambda: source
    )
    monkeypatch.setattr(
        tool_bridge, "_source_context", lambda _c: object()
    )
    _set_context(_human_user())
    with pytest.raises(DrawingAnalysisError) as excinfo:
        asyncio.run(
            sem._produce_drawing_understanding(object(), "90264017")
        )
    assert excinfo.value.code == "drawing_pdf_unavailable"
    assert source.pdf_calls == 1


def test_line_texts_distributed_by_visual_band_rows():
    """Célula rowspan=1 'C 6 D 3' (caso real p9) → bandas redistribuídas
    às linhas SLANet por centroide Y das colunas confiáveis."""
    cells = [
        {"row": 0, "col": 0, "text": "Item", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [0, 0, 40, 0, 40, 18, 0, 18]},
        {"row": 0, "col": 1, "text": "Codigo", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [40, 0, 120, 0, 120, 18, 40, 18]},
        # célula real observada: rowspan=1, texto de 2 linhas visuais
        {"row": 1, "col": 0, "text": "C 6 D 3", "rowspan": 1, "colspan": 1,
         "line_texts": ["C 6", "D 3"], "line_centers": [30.0, 50.0],
         "bounding_box_px": [0, 20, 40, 20, 40, 60, 0, 60]},
        {"row": 1, "col": 1, "text": "10081389", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [40, 20, 120, 20, 120, 38, 40, 38]},
        {"row": 2, "col": 1, "text": "10081685", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [40, 40, 120, 40, 120, 58, 40, 58]},
    ]
    from engineering_app.application.drawing.understanding import (
        rows_from_native_cells,
    )
    rows, _ = rows_from_native_cells(cells, page=9)
    assert [r["item"] for r in rows] == ["C", "D"]
    assert [r["quantity"] for r in rows] == ["6", "3"]
    assert [r["component_code"] for r in rows] == [
        "10081389", "10081685",
    ]


def test_multiline_single_row_is_not_split():
    """Duas bandas mapeando para a MESMA linha (descrição multilinha
    legítima) não são divididas."""
    cells = [
        {"row": 0, "col": 0, "text": "Codigo", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [0, 0, 120, 0, 120, 18, 0, 18]},
        {"row": 1, "col": 0, "text": "10081389", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [0, 20, 120, 20, 120, 38, 0, 38]},
        {"row": 2, "col": 0, "text": "TUBO FLEX", "rowspan": 1,
         "colspan": 1, "line_texts": ["TUBO FLEX", "ALTA PRESS"],
         "line_centers": [50.0, 58.0],
         "bounding_box_px": [0, 40, 120, 40, 120, 70, 0, 70]},
        {"row": 3, "col": 0, "text": "10081685", "rowspan": 1, "colspan": 1,
         "bounding_box_px": [0, 72, 120, 72, 120, 90, 0, 90]},
    ]
    from engineering_app.application.drawing.understanding import (
        rows_from_native_cells,
    )
    rows, _ = rows_from_native_cells(cells, page=9)
    # Bandas mapeiam para a mesma linha → nenhuma linha extra criada;
    # o texto permanece junto na row 2.
    assert len(rows) == 3
    row2 = [r for r in rows if r["row"] == 2][0]
    text2 = " ".join(c["text"] for c in row2["cells"])
    assert "TUBO FLEX" in text2


def _quad(x1, y1, x2, y2):
    return [x1, y1, x2, y1, x2, y2, x1, y2]


def test_engine_emits_line_texts_for_two_band_tokens(monkeypatch):
    """Tokens quad de 2 bandas Y numa célula rowspan=1 → line_texts."""
    class FakePdf:
        def __len__(self):
            return 1
        def close(self):
            return None

    monkeypatch.setattr(
        engine_adapters, "_open_pdf_document",
        lambda _b: (FakePdf(), "tmp"),
    )
    monkeypatch.setattr(
        engine_adapters, "_render_page",
        lambda _p, _i: {"image": _FakeImage(120, 80), "page_index": _i},
    )
    # 6 <td>: header(0,1) + row1(c0 fundida cobrindo 2 bandas, c1) +
    # row2(c0 vazia, c1) — reproduz o defeito real: rowspan=1, caixa
    # geométrica cobrindo duas linhas visuais.
    monkeypatch.setattr(
        engine_adapters,
        "_predict_table_structure",
        lambda _crop: [
            {
                "structure": (
                    "<table><tr><td></td><td></td></tr>"
                    "<tr><td></td><td></td></tr>"
                    "<tr><td></td><td></td></tr></table>"
                ),
                "bbox": [
                    _quad(0, 0, 30, 18),
                    _quad(40, 0, 90, 18),
                    _quad(0, 18, 30, 62),
                    _quad(40, 18, 90, 40),
                    _quad(0, 62, 30, 62),
                    _quad(40, 40, 90, 62),
                ],
                "structure_score": 0.9,
            }
        ],
    )
    # tokens: 2 bandas Y na col 0 (cy≈30 e ≈50), códigos separados col 1
    toks = [
        {"text": "X", "bounding_box_px": _quad(2, 24, 10, 36)},
        {"text": "4", "bounding_box_px": _quad(14, 24, 22, 36)},
        {"text": "Y", "bounding_box_px": _quad(2, 44, 10, 56)},
        {"text": "7", "bounding_box_px": _quad(14, 44, 22, 56)},
        {"text": "90000001", "bounding_box_px": _quad(40, 24, 80, 36)},
        {"text": "90000002", "bounding_box_px": _quad(40, 44, 80, 56)},
    ]
    pdf = b"%PDF-fixture"
    res = engine_adapters.TableStructureEngine().run(
        pdf,
        document_hash_sha256=_sha(pdf),
        pages=[1],
        crop_box=[0, 0, 120, 60],
        ocr_tokens=toks,
    )
    assert res["error_kind"] is None
    split = [c for c in res["cells"] if c.get("line_texts")]
    assert len(split) == 1
    assert split[0]["line_texts"] == ["X 4", "Y 7"]
    assert len(split[0]["line_centers"]) == 2
