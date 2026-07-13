"""Regressão: gateway emite só as chaves de data canônicas de cada rota do catálogo."""

from __future__ import annotations

from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
    reset_tv_data_route_catalog_cache,
)
from tv_app.infrastructure.gateways.delpi_operational_gateway import _build_query_params

_DATE_ALIASES = frozenset(
    {
        "date_start",
        "date_end",
        "start_date",
        "end_date",
        "issue_date_start",
        "issue_date_end",
        "date_from",
        "date_to",
        "dataInicio",
        "dataFim",
        "data_inicial",
        "data_final",
        "modified_from",
        "modified_to",
        "from",
        "to",
    }
)


def _expected_pair(route: dict) -> tuple[str, str] | None:
    keys = route.get("dateRangeKeys")
    if isinstance(keys, list) and len(keys) >= 2:
        return str(keys[0]), str(keys[1])
    schema = route.get("paramSchema") or {}
    for start, end in (
        ("date_start", "date_end"),
        ("start_date", "end_date"),
        ("issue_date_start", "issue_date_end"),
    ):
        if start in schema and end in schema:
            return start, end
    if str(route.get("paramStrategy") or "") == "date_range":
        return "start_date", "end_date"
    return None


def test_all_catalog_routes_emit_only_canonical_date_keys():
    reset_tv_data_route_catalog_cache()
    catalog = TvDataRouteCatalogService()
    checked = 0
    for route in catalog.list_routes():
        pair = _expected_pair(route)
        if not pair:
            continue
        checked += 1
        start_key, end_key = pair
        query = _build_query_params(
            route,
            {
                "branch": "01",
                "date_start": "2026-01-01",
                "date_end": "2026-07-13",
                "start_date": "2026-01-01",
                "end_date": "2026-07-13",
                "issue_date_start": "2026-01-01",
                "issue_date_end": "2026-07-13",
            },
        )
        assert start_key in query, route.get("operationId")
        assert end_key in query, route.get("operationId")
        leaked = (_DATE_ALIASES - {start_key, end_key}) & set(query)
        assert not leaked, f"{route.get('operationId')}: aliases vazaram {leaked}"
    assert checked >= 40


def test_ppm_and_oee_use_distinct_canonical_keys():
    reset_tv_data_route_catalog_cache()
    catalog = TvDataRouteCatalogService()
    ppm = catalog.get_route("get_ppm_internal_summary")
    oee = catalog.get_route("get_production_oee")
    assert ppm and oee
    assert ppm.get("dateRangeKeys") == ["date_start", "date_end"]
    assert oee.get("dateRangeKeys") == ["start_date", "end_date"]
    ppm_q = _build_query_params(ppm, {"date_start": "2026-01-01", "date_end": "2026-07-13"})
    oee_q = _build_query_params(oee, {"date_start": "2026-01-01", "date_end": "2026-07-13"})
    assert "date_start" in ppm_q and "start_date" not in ppm_q
    assert "start_date" in oee_q and "date_start" not in oee_q
