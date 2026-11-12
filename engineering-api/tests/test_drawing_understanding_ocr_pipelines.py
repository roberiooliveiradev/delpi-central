"""EVA-VAL01-MULTIPAGE — seleção de pipelines OCR do caminho de
understanding.

Causa-raiz do timeout multipágina: o caminho de understanding rodava
os DOIS pipelines do perfil de benchmark em série (~2x custo OCR por
página), embora consuma apenas UM run (`best`). O pipeline canônico
roda primeiro; o pipeline de comparação (benchmark) vira fallback e
só executa quando o primário não produz evidência utilizável.
"""

from __future__ import annotations

import pytest

from engineering_app.interface.mcp import semantic_bridge as sem


@pytest.fixture
def stub(monkeypatch):
    calls: list[list[str] | None] = []
    state = {"next_out": None, "outs": None}

    async def fake_benchmark(*, code, source, ctx, providers,
                            visual_pipelines, corpus_id, environment):
        calls.append(list(visual_pipelines) if visual_pipelines else None)
        if state["outs"] is not None:
            return next(state["outs"])
        return state["next_out"]

    monkeypatch.setattr(
        "engineering_app.application.drawing.document_benchmark_service."
        "run_official_document_benchmark",
        fake_benchmark,
    )
    monkeypatch.setattr(sem.bridge, "_source_context", lambda _c: None)
    monkeypatch.setattr(
        sem.bridge, "build_delegated_auxiliary_source", lambda: object()
    )
    state["calls"] = calls
    return state


def _out(provider: str, tokens: list | None) -> dict:
    return {
        "runs": [
            {
                "provider_id": provider,
                "status": "ok",
                "token_count": len(tokens or []),
                "_tokens_sample": tokens or [],
                "document_hash": "h",
            }
        ]
    }


async def test_understanding_runs_primary_pipeline_only_when_it_yields(
    stub,
):
    """Primário cobre o documento → pipeline de comparação NÃO roda."""
    stub["next_out"] = _out("pdfium_render_paddleocr", [{"text": "x"}])

    out, runs = await sem._run_understanding_visual_benchmark(
        None, "90264135"
    )

    assert stub["calls"] == [["pdfium_render_paddleocr"]]
    assert runs[0]["provider_id"] == "pdfium_render_paddleocr"
    assert out is stub["next_out"]


async def test_understanding_falls_back_to_comparison_pipeline(stub):
    """Primário sem evidência → fallback roda o pipeline restante."""
    stub["outs"] = iter(
        [
            _out("pdfium_render_paddleocr", []),
            _out("pdfium_render_opencv_paddleocr", [{"text": "y"}]),
        ]
    )

    out, runs = await sem._run_understanding_visual_benchmark(
        None, "90264135"
    )

    assert stub["calls"] == [
        ["pdfium_render_paddleocr"],
        ["pdfium_render_opencv_paddleocr"],
    ]
    assert runs[0]["provider_id"] == "pdfium_render_opencv_paddleocr"


async def test_understanding_fallback_when_primary_errors(stub):
    """Run em erro sem amostra de tokens também aciona fallback."""
    stub["outs"] = iter(
        [
            {
                "runs": [
                    {
                        "provider_id": "pdfium_render_paddleocr",
                        "status": "provider_error",
                        "_tokens_sample": [],
                    }
                ]
            },
            _out("opencv_fb", [{"text": "z"}]),
        ]
    )

    out, runs = await sem._run_understanding_visual_benchmark(
        None, "90264135"
    )

    assert len(stub["calls"]) == 2
    assert runs and runs[0]["provider_id"] == "opencv_fb"
