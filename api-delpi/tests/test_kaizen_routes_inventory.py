"""Inventário: toda rota Kaizômetro tem operationId citado em testes."""

from __future__ import annotations

from pathlib import Path

from app.interface.http.routes.quality.kaizen_public_router import router as public_router
from app.interface.http.routes.quality.kaizen_records_router import router as records_router
from app.interface.http.routes.quality.quality_router import router as quality_router

_TESTS_ROOT = Path(__file__).resolve().parent
_QUALITY_KAIZEN_OPS = {
    "get_kaizen_summary",
    "get_kaizen_summary_series",
    "get_kaizen_by_id",
}


def _operation_ids(router) -> set[str]:
    ids: set[str] = set()
    for route in router.routes:
        op = getattr(route, "operation_id", None) or getattr(route, "name", None)
        if isinstance(op, str) and op:
            ids.add(op)
    return ids


def test_all_kaizometro_operation_ids_have_test_mentions() -> None:
    ops = _operation_ids(records_router) | _operation_ids(public_router) | _QUALITY_KAIZEN_OPS
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in _TESTS_ROOT.rglob("*.py"))
    missing = sorted(op for op in ops if op not in corpus)
    assert not missing, f"operationId sem menção em tests/: {missing}"


def test_quality_kaizen_collection_routes_are_registered() -> None:
    paths = [getattr(route, "path", "") for route in quality_router.routes]
    assert any(path.endswith("/kaizens/summary") for path in paths)
    assert any(path.endswith("/kaizens/summary/series") for path in paths)
    assert any("{kaizen_id" in path for path in paths)
