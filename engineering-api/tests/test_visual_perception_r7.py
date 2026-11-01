"""R7 — visual perception contracts, adapters, registry, harness,
dedup, spatial evidence and governed profile wiring tests.

Environment-agnostic: vision extras (cv2/paddleocr) may be absent —
adapters must degrade honestly (provider_unavailable /
model_not_provisioned), never fabricate.
"""

from __future__ import annotations

import hashlib

import pytest

from engineering_app.application.drawing.extraction_ports import (
    OcrToken,
    PreprocessResult,
    ProviderResolutionError,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
)
from engineering_app.application.drawing.visual_benchmark import (
    VISUAL_PIPELINE_CATALOG,
    _token_sample_entry,
    dedupe_visual_evidence,
    run_visual_benchmark,
    visual_records_to_jsonl,
)
from engineering_app.infrastructure.extraction.registry import (
    _OCR_CATALOG,
    _PREPROCESS_CATALOG,
    _RENDER_CATALOG,
    list_visual_providers,
    resolve_visual_provider,
)
from tests.test_drawing_analysis import _minimal_pdf
from tests.test_drawing_analysis_r2 import _EnvelopeSource, PDF_90264302

_PDF = _minimal_pdf("CHICOTE 90264302 CABO 643MM 663MM")


def _has(module: str) -> bool:
    try:
        __import__(module)
        return True
    except Exception:
        return False


# --- contracts ---------------------------------------------------------------


def test_rendered_page_spatial_provenance_fields():
    from engineering_app.application.drawing.extraction_ports import (
        RenderedPage,
    )

    page = RenderedPage(
        page=1, image_bytes=b"x", width=10, height=10,
        dpi=150, provider_id="pdfium_experimental",
    )
    assert page.coordinate_system == "pixels_pdfium_top_left"
    assert page.scale is None and page.rotation is None


def test_pdfium_render_respects_bounds_and_transform():
    from engineering_app.infrastructure.extraction.pdfium_adapter import (
        PdfiumExtractionAdapter,
        _PDFIUM_AVAILABLE,
    )

    adapter = PdfiumExtractionAdapter()
    if not _PDFIUM_AVAILABLE:
        with pytest.raises(PdfExtractionError, match="unavailable"):
            adapter.render_page(_PDF, page=1)
        return
    rendered = adapter.render_page(_PDF, page=1, dpi=150)
    assert rendered.width > 0 and rendered.height > 0
    assert rendered.scale == pytest.approx(150 / 72)
    assert rendered.rotation in (0, 90, 180, 270)
    assert rendered.page_width_pt == pytest.approx(595)
    assert rendered.image_bytes[:4] == b"\x89PNG"
    with pytest.raises(PdfExtractionError, match="page_out_of_bounds"):
        adapter.render_page(_PDF, page=99)
    with pytest.raises(PdfExtractionError, match="dpi_limit"):
        adapter.render_page(_PDF, page=1, dpi=9999)
    with pytest.raises(PdfExtractionError, match="invalid_mime"):
        adapter.render_page(b"NOTAPDF", page=1)


# --- OpenCV adapter ------------------------------------------------------------


def test_opencv_unknown_profile_rejected():
    from engineering_app.infrastructure.extraction.opencv_adapter import (
        OpencvPreprocessingAdapter,
        _CV2_AVAILABLE,
    )

    adapter = OpencvPreprocessingAdapter()
    with pytest.raises(PdfExtractionError) as exc:
        adapter.preprocess(b"\x89PNGxxxx", mode="magic_enhance")
    if _CV2_AVAILABLE:
        assert "unknown_preprocess_profile" in str(exc.value)
    else:
        assert "provider_unavailable" in str(exc.value)


@pytest.mark.skipif(not _has("cv2"), reason="opencv extras not installed")
def test_opencv_profiles_traceable_and_bounded():
    import cv2
    import numpy as np

    from engineering_app.infrastructure.extraction.opencv_adapter import (
        OpencvPreprocessingAdapter,
    )

    img = np.full((40, 40, 3), 255, dtype=np.uint8)
    cv2.putText(img, "643", (2, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 0, 0), 2)
    _, buf = cv2.imencode(".png", img)
    adapter = OpencvPreprocessingAdapter()

    raw = adapter.preprocess(buf.tobytes(), mode="raw_render")
    assert isinstance(raw, PreprocessResult)
    assert raw.ops_applied == ["decode_reencode"]
    gray = adapter.preprocess(buf.tobytes(), mode="grayscale")
    assert gray.ops_applied == ["grayscale"]
    thr = adapter.preprocess(buf.tobytes(), mode="adaptive_threshold")
    assert "adaptive_threshold_mean_c" in thr.ops_applied
    assert thr.width == 40 and thr.height == 40
    assert len({raw.image_bytes, gray.image_bytes}) >= 1

    with pytest.raises(PdfExtractionError, match="empty_image"):
        adapter.preprocess(b"", mode="grayscale")
    with pytest.raises(PdfExtractionError):
        adapter.preprocess(b"not-an-image", mode="grayscale")


# --- PaddleOCR adapter (governance) ---------------------------------------------


def test_paddleocr_model_governance_fail_closed(monkeypatch):
    from engineering_app.infrastructure.extraction.paddleocr_adapter import (
        PaddleOcrAdapter,
    )

    monkeypatch.delenv("ENG_DRAWING_OCR_MODEL_DIR", raising=False)
    monkeypatch.delenv(
        "ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD", raising=False
    )
    adapter = PaddleOcrAdapter()
    assert adapter._resolve_models() is False
    assert "model_not_provisioned" in adapter._engine_error

    monkeypatch.setenv("ENG_DRAWING_OCR_MODEL_DIR", "/nonexistent-dir")
    adapter = PaddleOcrAdapter()
    assert adapter._resolve_models() is False
    assert "missing_dir" in adapter._engine_error

    monkeypatch.setenv("ENG_DRAWING_OCR_MODEL_DIR", "/tmp")
    adapter = PaddleOcrAdapter()
    assert adapter._resolve_models() is True
    assert adapter._model_source.startswith("provisioned_dir")

    monkeypatch.delenv("ENG_DRAWING_OCR_MODEL_DIR", raising=False)
    monkeypatch.setenv("ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD", "true")
    adapter = PaddleOcrAdapter()
    assert adapter._resolve_models() is True
    assert adapter._model_source == "paddlex_official_auto_download"


def test_paddleocr_capability_honest():
    from engineering_app.infrastructure.extraction.paddleocr_adapter import (
        PaddleOcrAdapter,
    )

    desc = PaddleOcrAdapter().capability_descriptor()
    assert desc.runs_local is True
    assert desc.requires_credentials is False
    assert desc.license == "Apache-2.0"
    assert desc.status in {"experimental", "unavailable"}


def test_paddleocr_input_contract_before_engine(monkeypatch):
    """Entradas inválidas falham antes de tocar o engine (fail-closed)."""
    from engineering_app.infrastructure.extraction import (
        paddleocr_adapter as mod,
    )

    adapter = mod.PaddleOcrAdapter()
    if not (mod._PADDLEOCR_AVAILABLE and mod._CV2_AVAILABLE):
        with pytest.raises(PdfExtractionError, match="unavailable"):
            adapter.extract_text(b"x")
        return
    monkeypatch.delenv("ENG_DRAWING_OCR_MODEL_DIR", raising=False)
    monkeypatch.delenv(
        "ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD", raising=False
    )
    with pytest.raises(PdfExtractionError, match="empty_image"):
        adapter.extract_text(b"")
    with pytest.raises(PdfExtractionError, match="image_too_large"):
        adapter.extract_text(b"\x89PNG" + b"0" * (40 * 1024 * 1024))
    with pytest.raises(PdfExtractionError, match="unreadable_image"):
        adapter.extract_text(b"not-an-image")
    # modelo ausente → fail honesto, nunca download implícito
    import cv2
    import numpy as np

    _, buf = cv2.imencode(".png", np.zeros((8, 8, 3), dtype=np.uint8))
    with pytest.raises(PdfExtractionError, match="model_not_provisioned"):
        adapter.extract_text(buf.tobytes())


def test_paddleocr_timeout_bounds(monkeypatch):
    from engineering_app.infrastructure.extraction import (
        paddleocr_adapter as mod,
    )

    monkeypatch.delenv("ENG_DRAWING_OCR_TIMEOUT_SECONDS", raising=False)
    assert mod._timeout_seconds() == 120.0
    monkeypatch.setenv("ENG_DRAWING_OCR_TIMEOUT_SECONDS", "1")
    assert mod._timeout_seconds() == 5.0  # piso
    monkeypatch.setenv("ENG_DRAWING_OCR_TIMEOUT_SECONDS", "99999")
    assert mod._timeout_seconds() == 600.0  # teto
    monkeypatch.setenv("ENG_DRAWING_OCR_TIMEOUT_SECONDS", "abc")
    assert mod._timeout_seconds() == 120.0


def test_normalize_box_json_safe():
    from engineering_app.infrastructure.extraction.paddleocr_adapter import (
        _normalize_box,
    )

    assert _normalize_box(None, 0) is None
    assert _normalize_box([], 0) is None
    poly = [[[1.5, 2.5], [10.5, 2.5], [10.5, 8.5], [1.5, 8.5]]]
    box = _normalize_box(poly, 0)
    assert box == [1.5, 2.5, 10.5, 2.5, 10.5, 8.5, 1.5, 8.5]
    assert _normalize_box(poly, 5) is None


# --- registry -------------------------------------------------------------------


def test_visual_registry_governance():
    with pytest.raises(ProviderResolutionError) as exc:
        resolve_visual_provider("magic", "x", allow_experimental=True)
    assert exc.value.code == "unknown_provider_kind"
    with pytest.raises(ProviderResolutionError) as exc:
        resolve_visual_provider("ocr", "not_a_provider",
                                allow_experimental=True)
    assert exc.value.code == "unknown_provider"
    for kind, catalog in (
        ("render", _RENDER_CATALOG),
        ("preprocess", _PREPROCESS_CATALOG),
        ("ocr", _OCR_CATALOG),
    ):
        for pid in catalog:
            with pytest.raises(ProviderResolutionError) as exc:
                resolve_visual_provider(kind, pid)
            assert exc.value.code == "provider_not_enabled"
            provider = resolve_visual_provider(
                kind, pid, allow_experimental=True
            )
            desc = provider.capability_descriptor()
            # o adapter pdfium serve os dois catálogos — a identidade do
            # provider vem do registry; o descriptor afirma capacidades.
            assert desc.status in {"experimental", "unavailable"}
            assert desc.runs_local is True


def test_visual_pipeline_catalog_integrity():
    for pid, spec in VISUAL_PIPELINE_CATALOG.items():
        assert spec["render"] in _RENDER_CATALOG, pid
        if spec.get("preprocess"):
            assert spec["preprocess"] in _PREPROCESS_CATALOG, pid
            assert spec["preprocess_mode"] in (
                "raw_render", "grayscale", "adaptive_threshold"
            )
        assert spec["ocr"] in _OCR_CATALOG, pid


def test_list_visual_providers_shape():
    listed = list_visual_providers()
    kinds = {p["kind"] for p in listed}
    assert kinds == {"render", "preprocess", "ocr"}
    assert all("provider_id" in p and "descriptor" in p for p in listed)


# --- visual benchmark harness -----------------------------------------------------


def test_visual_benchmark_unknown_pipeline():
    runs = run_visual_benchmark(_PDF, pipelines=["does_not_exist"])
    assert runs[0]["status"] == "provider_error"
    assert "unknown_pipeline" in runs[0]["error"]
    assert runs[0]["document_hash"] == hashlib.sha256(_PDF).hexdigest()


def test_visual_benchmark_same_bytes_honest_status():
    pipelines = [
        "pdfium_render_paddleocr",
        "pdfium_render_opencv_paddleocr",
    ]
    runs = run_visual_benchmark(_PDF, pipelines=pipelines)
    assert len(runs) == 2
    doc_hash = hashlib.sha256(_PDF).hexdigest()
    for run in runs:
        assert run["document_hash"] == doc_hash
        assert run["input_bytes"] == len(_PDF)
        assert run["status"] in {
            "ok", "partial", "error", "extraction_error",
            "provider_error",
        }
        # nunca vaza imagem integral nem bytes do documento
        assert "image_bytes" not in str(run)
        assert "access_token" not in str(run)
        if run["status"] == "ok":
            assert run["pages_rendered"] >= 1
            assert len(run["_tokens_sample"]) <= 200


def test_token_sample_coordinate_transform():
    token = OcrToken(text="643MM", confidence=0.9,
                     box=[10.0, 20.0, 60.0, 20.0, 60.0, 40.0, 10.0, 40.0])
    entry = _token_sample_entry(
        token, page=1, scale=2.0833, width=1240, height=1754,
        provider_id="paddleocr_experimental",
        provider_version="3.3.0",
        extraction_method="paddleocr_local",
    )
    assert entry["normalized_text"] == "643mm"
    assert entry["bounding_box_normalized"] == [
        round(10 / 1240, 4), round(20 / 1754, 4),
        round(60 / 1240, 4), round(40 / 1754, 4),
    ]
    assert entry["bounding_box_pdf_points"][0] == pytest.approx(
        10 / 2.0833, abs=0.01
    )
    assert entry["pdf_transform"].startswith("pdf_pt = px /")
    # caixa ausente → coordenadas honestamente desconhecidas
    bare = _token_sample_entry(
        OcrToken(text="X", confidence=None, box=None),
        page=1, scale=None, width=0, height=0,
        provider_id="p", provider_version=None,
        extraction_method="m",
    )
    assert bare["bounding_box_normalized"] is None
    assert bare["bounding_box_pdf_points"] is None


def test_dedupe_conservative_exact_match_only():
    def _tok(page, text):
        return {
            "page": page, "normalized_text": "".join(
                text.split()).lower(),
            "confidence": 0.9, "bounding_box_px": [1, 1, 2, 2],
        }

    runs = [
        {"provider_id": "pdfium_render_paddleocr",
         "_tokens_sample": [_tok(1, "643MM"), _tok(1, "663MM")]},
        {"provider_id": "pdfium_render_opencv_paddleocr",
         "_tokens_sample": [_tok(1, "643MM"), _tok(1, "643 MM")]},
    ]
    out = dedupe_visual_evidence(runs)
    by_text = {e["normalized_text"]: e for e in out["entries"]}
    # "643mm" dedup entre pipelines; "663mm" nunca funde com "643mm"
    assert by_text["643mm"]["copies"] == 3
    assert set(by_text["643mm"]["providers"]) == {
        "pdfium_render_paddleocr",
        "pdfium_render_opencv_paddleocr",
    }
    assert by_text["663mm"]["copies"] == 1
    assert out["duplicated_texts"] == 1
    assert out["unique_texts"] == 2


def test_visual_jsonl_strips_transient_evidence():
    runs = [
        {"provider_id": "x", "_text_blob": "SECRET-TEXT",
         "_tokens_sample": [{"a": 1}], "status": "ok"}
    ]
    blob = visual_records_to_jsonl(runs)
    assert "_text_blob" not in blob and "_tokens_sample" not in blob
    assert "SECRET-TEXT" not in blob


# --- bridge: perfil visual governado -------------------------------------------------


async def test_visual_profile_requires_own_flag(monkeypatch):
    from engineering_app.interface.mcp import semantic_bridge as sem
    from tests.test_eva_mcp import _human_user, _set_context

    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    monkeypatch.delenv(
        "ENG_DRAWING_OCR_BENCHMARK_ENABLED", raising=False
    )
    _set_context(_human_user())
    result = await sem.tool_analyze(
        analysis_type="product.drawing_benchmark",
        parameters={
            "product_code": "90264302",
            "benchmark_profile": "approved_local_visual_ocr",
        },
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "feature_disabled"
    assert (
        result.structured_content["data"]["required_flag"]
        == "ENG_DRAWING_OCR_BENCHMARK_ENABLED"
    )


async def test_visual_profile_executes_with_honest_status(monkeypatch):
    from engineering_app.interface.mcp import semantic_bridge as sem
    from engineering_app.interface.mcp import tool_bridge as bridge
    from tests.test_eva_mcp import _human_user, _set_context

    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    monkeypatch.setenv("ENG_DRAWING_OCR_BENCHMARK_ENABLED", "true")
    monkeypatch.delenv("ENG_DRAWING_OCR_MODEL_DIR", raising=False)
    monkeypatch.delenv(
        "ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD", raising=False
    )
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source",
        lambda: _EnvelopeSource(PDF_90264302),
    )
    result = await sem.tool_analyze(
        analysis_type="product.drawing_benchmark",
        parameters={
            "product_code": "90264302",
            "benchmark_profile": "approved_local_visual_ocr",
            "fields": ["90264302"],
        },
    )
    assert not result.is_error, result.structured_content
    data = result.structured_content["data"]
    assert data["benchmark_profile"] == "approved_local_visual_ocr"
    assert len(data["providers"]) == 2
    assert all(
        r["pipeline_kind"] == "visual_ocr" for r in data["providers"]
    )
    assert "evidence_dedup" in data
    assert "image_bytes" not in str(data)
    # limitações refletem a execução real — nunca a mensagem falsa fixa
    assert "não executam — status honesto" not in str(
        data["limitations"]
    )
    # paddleocr sem modelo provisionado → falha honesta registrada
    statuses = {r["status"] for r in data["providers"]}
    assert statuses <= {
        "ok", "partial", "error", "extraction_error",
        "provider_error",
    }


# --- R7-16: residual de limitações R6-D.2 --------------------------------------------


def test_limitations_derived_from_real_status():
    from engineering_app.interface.mcp.semantic_bridge import (
        _benchmark_limitations,
    )

    ok = _benchmark_limitations(
        [{"provider_id": "p1", "status": "ok", "limitations": []}]
    )
    assert all("não executou" not in lim for lim in ok)
    err = _benchmark_limitations(
        [{"provider_id": "p1", "status": "provider_error",
          "error": "unknown_provider"}]
    )
    assert any("p1" in lim and "não executou" in lim for lim in err)
    assert any("unknown_provider" in lim for lim in err)
    part = _benchmark_limitations(
        [{"provider_id": "p1", "status": "partial",
          "limitations": ["page_errors:1_of_2_pages"]}]
    )
    assert any("cobertura parcial" in lim for lim in part)


async def test_benchmark_limitations_match_real_runs(monkeypatch):
    """Contradição R6-D.2: status ok + 'providers não executam' global
    não pode mais coexistir — regression gate."""
    from engineering_app.interface.mcp import semantic_bridge as sem
    from engineering_app.interface.mcp import tool_bridge as bridge
    from tests.test_eva_mcp import _human_user, _set_context

    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source",
        lambda: _EnvelopeSource(PDF_90264302),
    )
    result = await sem.tool_analyze(
        analysis_type="product.drawing_benchmark",
        parameters={"product_code": "90264302"},
    )
    assert not result.is_error
    data = result.structured_content["data"]
    ok_ids = {
        r["provider_id"]
        for r in data["providers"]
        if r["status"] == "ok"
    }
    for lim in data["limitations"]:
        if "não executou" in lim:
            pid = lim.split("provider ")[1].split(" ")[0]
            assert pid not in ok_ids, (
                f"provider {pid} executou mas limitação diz o contrário"
            )


# --- bridge oficial: modo visual -------------------------------------------------------


async def test_official_bridge_visual_mode_same_hash():
    from engineering_app.application.drawing.document_benchmark_service import (
        run_official_document_benchmark,
    )

    out = await run_official_document_benchmark(
        code="90264302",
        source=_EnvelopeSource(PDF_90264302),
        ctx=None,
        visual_pipelines=["pdfium_render_paddleocr"],
    )
    assert out["same_document_verified"] is True
    assert out["runs"][0]["pipeline_kind"] == "visual_ocr"
    assert "evidence_dedup" in out
    assert out["document"]["document_hash_sha256"] == hashlib.sha256(
        PDF_90264302
    ).hexdigest()
