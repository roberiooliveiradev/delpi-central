"""RES-01 — product.drawing_understanding usa o job store existente."""

from __future__ import annotations

import asyncio

import pytest

from engineering_app.application.drawing.analysis_jobs import (
    reset_analysis_job_store,
)
from engineering_app.application.drawing.drawing_contracts import (
    DrawingAnalysisError,
)
from engineering_app.interface.mcp import semantic_bridge as sem
from tests.test_eva_mcp import _human_user, _set_context


@pytest.fixture
def visual_flags(monkeypatch):
    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    monkeypatch.setenv("ENG_DRAWING_OCR_BENCHMARK_ENABLED", "true")
    reset_analysis_job_store()
    yield
    reset_analysis_job_store()


def _payload(code: str) -> dict:
    return {
        "analysis_type": "product.drawing_understanding",
        "understanding": {
            "tokens": [{"text": "heavy"}],
            "report": {
                "structure_validation": {
                    "schema_version": "structure_validation.v1",
                    "proven_matches": 0,
                    "engineering_approval": "NOT_APPROVED",
                }
            },
        },
        "product_echo": code,
    }


async def test_long_understanding_returns_job_then_completed(monkeypatch, visual_flags):
    started = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def slow(context, code, question):
        calls.append(code)
        started.set()
        await release.wait()
        return _payload(code)

    monkeypatch.setattr(sem, "_execute_drawing_understanding", slow)
    _set_context(_human_user())
    first = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    assert not first.is_error
    data = first.structured_content["data"]
    assert data["status"] == "RUNNING"
    assert data["result_ready"] is False
    assert "understanding" not in data
    job_id = data["job_id"]
    await asyncio.wait_for(started.wait(), 1)
    again = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    assert again.structured_content["data"]["job_id"] == job_id
    assert calls == ["90264030"]
    release.set()
    done = None
    for _ in range(50):
        done = await sem.tool_analyze(
            analysis_type="product.drawing_understanding",
            parameters={"product_code": "90264030", "job_id": job_id},
        )
        if done.structured_content["data"].get("status") == "COMPLETED":
            break
        await asyncio.sleep(0.01)
    body = done.structured_content["data"]
    assert body["status"] == "COMPLETED"
    assert body["result_ready"] is True
    report = body["understanding"]["report"]["structure_validation"]
    assert report["schema_version"] == "structure_validation.v1"
    assert report["proven_matches"] == 0
    assert "tokens" not in body["understanding"]


async def test_understanding_job_failure_is_typed(monkeypatch, visual_flags):
    async def boom(context, code, question):
        raise DrawingAnalysisError(
            "document_unreadable", "PDF ilegível.", status_code=422
        )

    monkeypatch.setattr(sem, "_execute_drawing_understanding", boom)
    _set_context(_human_user())
    started = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264017"},
    )
    job_id = started.structured_content["data"]["job_id"]
    failed = None
    for _ in range(50):
        failed = await sem.tool_analyze(
            analysis_type="product.drawing_understanding",
            parameters={"product_code": "90264017", "job_id": job_id},
        )
        if failed.is_error:
            break
        await asyncio.sleep(0.01)
    assert failed.is_error
    assert failed.structured_content["error_code"] == "document_unreadable"
    assert failed.structured_content["status_code"] == 422
    assert "Upstream" not in failed.structured_content["message"]


async def test_understanding_job_is_hidden_from_another_user(
    monkeypatch, visual_flags
):
    release = asyncio.Event()

    async def slow(context, code, question):
        await release.wait()
        return _payload(code)

    monkeypatch.setattr(sem, "_execute_drawing_understanding", slow)
    _set_context(_human_user())
    started = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030"},
    )
    job_id = started.structured_content["data"]["job_id"]
    _set_context(_human_user(id="user-2"))
    hidden = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264030", "job_id": job_id},
    )
    assert hidden.is_error
    assert hidden.structured_content["error_code"] == "job_not_found"
    release.set()


async def test_understanding_unexpected_error_stays_typed(
    monkeypatch, visual_flags
):
    async def boom(context, code, question):
        raise RuntimeError("serializer blew up")

    monkeypatch.setattr(sem, "_execute_drawing_understanding", boom)
    _set_context(_human_user())
    started = await sem.tool_analyze(
        analysis_type="product.drawing_understanding",
        parameters={"product_code": "90264017"},
    )
    job_id = started.structured_content["data"]["job_id"]
    failed = None
    for _ in range(50):
        failed = await sem.tool_analyze(
            analysis_type="product.drawing_understanding",
            parameters={"product_code": "90264017", "job_id": job_id},
        )
        if failed.is_error:
            break
        await asyncio.sleep(0.01)
    assert failed.structured_content["error_code"] == "analysis_incomplete"
    assert failed.structured_content["success"] is False
