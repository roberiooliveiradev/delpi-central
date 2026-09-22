"""Suggest façade delegates to owner-local discovery."""

from __future__ import annotations

from tv_app.application.services.data.tv_data_route_suggest_service import (
    TvDataRouteSuggestService,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def test_suggest_empty_query():
    result = TvDataRouteSuggestService(TvDataRouteCatalogService()).suggest(
        query="  ",
        limit=3,
    )
    assert result["suggestions"] == []
    assert result["total"] == 0


def test_suggest_respects_limit():
    result = TvDataRouteSuggestService(TvDataRouteCatalogService()).suggest(
        query="commercial rol",
        limit=2,
    )
    assert result["total"] <= 2
    assert len(result["suggestions"]) <= 2
