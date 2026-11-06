"""DEC-VAL-036 — event loop não pode congelar durante benchmark visual."""
import asyncio
import time

import pytest


@pytest.mark.asyncio
async def test_visual_benchmark_does_not_freeze_event_loop(monkeypatch):
    """Um run_visual_benchmark bloqueante não pode impedir que outra
    coroutine progrida — prova do offload asyncio.to_thread."""
    from engineering_app.application.drawing import (
        document_benchmark_service as svc,
    )

    class _Src:
        async def fetch_product_drawing(self, ctx, code):
            return {"found": True, "filename": f"{code}.pdf"}

        async def fetch_product_drawing_pdf(self, ctx, code):
            return {"content": b"%PDF-1.4 fake"}

    calls = {"done": False}

    def slow_benchmark(*_a, **_k):
        time.sleep(0.4)
        calls["done"] = True
        return [{"provider_id": "x", "document_hash": "h"}]

    monkeypatch.setattr(
        "engineering_app.application.drawing.visual_benchmark."
        "run_visual_benchmark",
        slow_benchmark,
    )
    # document_benchmark_service importa lazy — patch no módulo de origem
    ticked = {"n": 0}

    async def ticker():
        while not calls["done"]:
            ticked["n"] += 1
            await asyncio.sleep(0.02)

    bench = asyncio.create_task(
        svc.run_official_document_benchmark(
            code="x",
            source=_Src(),
            ctx=None,
            visual_pipelines=["pdfium_render_paddleocr"],
        )
    )
    tick = asyncio.create_task(ticker())
    done, _ = await asyncio.wait({tick}, timeout=0.9)
    await bench
    assert ticked["n"] > 2, (
        "event loop congelou — benchmark executou inline em vez de "
        "to_thread"
    )
