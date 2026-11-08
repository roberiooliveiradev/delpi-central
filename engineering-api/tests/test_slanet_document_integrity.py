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
