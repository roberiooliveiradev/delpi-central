"""R6-D — analyze(product.drawing_benchmark) governed action tests."""

from __future__ import annotations

import hashlib

import pytest

from engineering_app.interface.mcp import semantic_bridge as sem
from engineering_app.interface.mcp import tool_bridge as bridge
from tests.test_drawing_analysis_r2 import _EnvelopeSource, PDF_90264302
from tests.test_eva_mcp import _human_user, _set_context


async def test_flag_off_fails_closed(monkeypatch):
    monkeypatch.delenv("ENG_DRAWING_BENCHMARK_ENABLED", raising=False)
    _set_context(_human_user())
    result = await sem.tool_analyze(
        analysis_type="product.drawing_benchmark",
        parameters={"product_code": "90264302"},
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "feature_disabled"


async def test_unknown_profile_rejected(monkeypatch):
    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    _set_context(_human_user())
    result = await sem.tool_analyze(
        analysis_type="product.drawing_benchmark",
        parameters={
            "product_code": "90264302",
            "benchmark_profile": "run_arbitrary_ocr",
        },
    )
    assert result.is_error
    assert result.structured_content["error_code"] == (
        "provider_profile_not_allowed"
    )


async def test_happy_path_same_hash_all_providers(monkeypatch):
    monkeypatch.setenv("ENG_DRAWING_BENCHMARK_ENABLED", "true")
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source",
        lambda: _EnvelopeSource(PDF_90264302),
    )
    result = await sem.tool_analyze(
        analysis_type="product.drawing_benchmark",
        parameters={
            "product_code": "90264302",
            "fields": ["90264302", "10080106", "ZZZ"],
        },
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["schema_version"] == "drawing_benchmark.v1"
    doc_hash = hashlib.sha256(PDF_90264302).hexdigest()
    assert data["document"]["document_hash_sha256"] == doc_hash
    assert data["same_document_verified"] is True
    assert len(data["providers"]) == 3
    assert all(r["document_hash"] == doc_hash
               for r in data["providers"])
    assert all("_text_blob" not in r for r in data["providers"])
    assert data["field_coverage"]["coverage_summary"]["valid_providers"] >= 1
    assert data["quality_gate"] == "EVAL_PENDING"
    assert "token" not in str(data)


def test_registry_lists_benchmark_action():
    from engineering_app.application.eva.semantic_registry import (
        SEMANTIC_ACTIONS,
    )
    caps = {a.capability for a in SEMANTIC_ACTIONS}
    assert "product.drawing_benchmark" in caps

def test_every_registered_analyze_action_has_dispatch():
    """R6-D.2 integrity: registry e dispatcher não podem divergir —
    perda silenciosa de branch em merge (46da939277) deve falhar."""
    import inspect

    from engineering_app.interface.mcp import semantic_bridge as sem

    src = inspect.getsource(sem.tool_analyze)
    for cap in ("product.drawing_analysis", "product.drawing_benchmark"):
        assert 'kind == "' + cap + '"' in src, "dispatch ausente: " + cap
