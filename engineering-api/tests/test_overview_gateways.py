"""F3.OVERVIEW — adapters da Visão geral com httpx.MockTransport.

Verifica serialização de filtros por owner (LMP: YYYYMMDD + branch;
TRANSFORMA+: ISO + filial_id; SI: competence/dates/branch), mapeamento
dos seis indicadores, repasse dos campos de meta enriquecidos,
401/403 → forbidden, falhas → unavailable com reason e delegação do
Bearer humano sem service token (F2a.R1).
"""

from __future__ import annotations

import httpx
import pytest

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.overview_sources import OverviewQuery
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
)
from engineering_app.infrastructure.gateways.overview_api_delpi import (
    ApiDelpiEngineeringSiSource,
    ApiDelpiLmpOverviewSource,
    ApiDelpiTransformaOverviewSource,
)

CTX = HomeSourceContext(
    user_id="user-1", access_token="user-jwt-1", request_id="req-1"
)
QUERY = OverviewQuery(
    start_date="2026-10-01",
    end_date="2026-10-31",
    competence="2026-10",
    branch="01",
)


def _capture(handler):
    captured = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return handler(request)

    return captured, _handler


def _envelope(data):
    return {"success": True, "data": data}


def _client(handler):
    return DownstreamClient(
        "http://api-delpi:8000",
        timeout_seconds=2.0,
        transport=httpx.MockTransport(handler),
    )


# --- LMP ---


async def test_lmp_summary_maps_three_indicators_and_serializes_dates(
    monkeypatch,
):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-x")
    payload = {
        "total_lmps": 41,
        "percent_dentro_prazo": 92.5,
        "avg_lead_time": 7.3,
        "has_goal": True,
        "goal_label": "Meta oficial",
        "goal_value": 90.0,
        "goal_scope_label": "Consolidado",
        "performance_direction": "higher_is_better",
        "value_unit": "%",
        "value_decimals": 1,
    }
    captured, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope(payload))
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))

    result = await source.fetch(CTX, query=QUERY)

    assert result.status == "available"
    assert len(result.indicators) == 3
    by_id = {ind.id: ind for ind in result.indicators}
    assert by_id["lmp_on_time"].value == 92.5
    assert by_id["lmp_on_time"].unit == "%"
    assert by_id["lmp_on_time"].has_goal is True
    assert by_id["lmp_on_time"].goal_value == 90.0
    assert by_id["lmp_on_time"].scope == "01"
    assert by_id["lmp_lead_time"].value == 7.3
    assert by_id["lmp_lead_time"].unit == "dias úteis"
    assert by_id["lmp_total_proposals"].value == 41

    request = captured["request"]
    assert request.url.path == "/engineering/lmps/dashboard/summary"
    # Contrato LMP: YYYYMMDD compacto + branch.
    assert request.url.params["start_date"] == "20261001"
    assert request.url.params["end_date"] == "20261031"
    assert request.url.params["branch"] == "01"
    assert request.headers["Authorization"] == "Bearer user-jwt-1"
    assert request.headers["X-Delpi-Caller-App"] == "engineering-api"
    assert request.headers["X-Request-Id"] == "req-1"
    assert "x-delpi-service-token" not in request.headers


async def test_lmp_goal_fields_only_on_strategic_indicator():
    # OVERVIEW.R1: metas enriquecidas no resumo LMP pertencem a
    # engineering-projects-on-time (lmp_on_time) — nunca vazam para
    # lead time nem total de propostas.
    payload = {
        "total_lmps": 41,
        "percent_dentro_prazo": 92.5,
        "avg_lead_time": 7.3,
        "has_goal": True,
        "goal_value": 90.0,
        "goal_label": "Meta oficial",
        "reference_goal": 88.0,
        "value_suffix": "%",
        "goal_scope_label": "Consolidado",
    }
    _, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope(payload))
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)

    by_id = {ind.id: ind for ind in result.indicators}
    assert by_id["lmp_on_time"].has_goal is True
    assert by_id["lmp_on_time"].goal_value == 90.0
    for ind_id in ("lmp_lead_time", "lmp_total_proposals"):
        ind = by_id[ind_id]
        assert ind.has_goal is None
        assert ind.goal_value is None
        assert ind.goal_label is None
        assert ind.reference_goal is None
        assert ind.value_suffix is None
        assert ind.goal_scope_label is None


async def test_lmp_prefers_total_items_when_owner_provides():
    payload = {"total_lmps": 41, "total_items": 57,
               "percent_dentro_prazo": 92.5, "avg_lead_time": 7.3}
    _, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope(payload))
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)
    by_id = {ind.id: ind for ind in result.indicators}
    assert by_id["lmp_total_proposals"].value == 57


async def test_lmp_zero_total_is_empty():
    payload = {"total_lmps": 0, "percent_dentro_prazo": 0.0,
               "avg_lead_time": None}
    _, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope(payload))
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)
    assert result.status == "empty"
    assert result.indicators == ()


async def test_lmp_403_is_forbidden():
    _, handler = _capture(
        lambda req: httpx.Response(403, json={"success": False,
                                              "error": {"code": "forbidden"}})
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)
    assert result.status == "forbidden"


async def test_lmp_500_is_unavailable():
    _, handler = _capture(
        lambda req: httpx.Response(500, json={"success": False})
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)
    assert result.status == "unavailable"
    assert result.reason == "upstream_error"


async def test_lmp_contract_error():
    _, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope("não-dict"))
    )
    source = ApiDelpiLmpOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)
    assert result.status == "unavailable"
    assert result.reason == "contract_error"


# --- TRANSFORMA+ ---


async def test_transforma_summary_maps_and_serializes_filial():
    payload = {
        "implemented_solutions_count": 8,
        "total_gross_savings_in_period": 12500.0,
        "average_roi": 3.4,
        "has_goal": True,
        "goal_value": 10000.0,
        "value_prefix": "R$ ",
        "value_unit": "BRL",
    }
    captured, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope(payload))
    )
    source = ApiDelpiTransformaOverviewSource(_client(handler))

    result = await source.fetch(CTX, query=QUERY)

    assert result.status == "available"
    by_id = {ind.id: ind for ind in result.indicators}
    assert by_id["transforma_gross_savings"].value == 12500.0
    assert by_id["transforma_gross_savings"].unit == "BRL"
    assert by_id["transforma_gross_savings"].value_prefix == "R$ "
    assert by_id["transforma_solutions"].value == 8
    assert by_id["transforma_roi"].value == 3.4
    assert by_id["transforma_roi"].unit == "x"

    request = captured["request"]
    assert request.url.path == "/engineering/transforma-mais/processes/summary"
    # Contrato TRANSFORMA+: ISO dates + filial_id.
    assert request.url.params["filial_id"] == "01"
    assert request.url.params["start_date"] == "2026-10-01"
    assert request.url.params["end_date"] == "2026-10-31"


async def test_transforma_goal_fields_only_on_gross_savings():
    # OVERVIEW.R1: metas do grupo TRANSFORMA+ pertencem a
    # engineering-transforma-plus (ganhos brutos) — soluções e ROI não
    # herdam meta, IDD, badges nem metadados de apresentação.
    payload = {
        "implemented_solutions_count": 8,
        "total_gross_savings_in_period": 12500.0,
        "average_roi": 3.4,
        "has_goal": True,
        "goal_value": 10000.0,
        "goal_label": "Meta TRANSFORMA+",
        "value_prefix": "R$ ",
        "value_unit": "BRL",
        "performance_direction": "higher_is_better",
    }
    _, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope(payload))
    )
    source = ApiDelpiTransformaOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)

    by_id = {ind.id: ind for ind in result.indicators}
    savings = by_id["transforma_gross_savings"]
    assert savings.has_goal is True
    assert savings.goal_value == 10000.0
    for ind_id in ("transforma_solutions", "transforma_roi"):
        ind = by_id[ind_id]
        assert ind.has_goal is None
        assert ind.goal_value is None
        assert ind.goal_label is None
        assert ind.value_prefix is None
        assert ind.value_unit is None
        assert ind.performance_direction is None


async def test_transforma_401_is_forbidden():
    _, handler = _capture(lambda req: httpx.Response(401))
    source = ApiDelpiTransformaOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=QUERY)
    assert result.status == "forbidden"


async def test_transforma_scope_consolidado_without_branch():
    query = OverviewQuery(branch=None)
    _, handler = _capture(
        lambda req: httpx.Response(
            200, json=_envelope({"implemented_solutions_count": 1,
                                 "total_gross_savings_in_period": 0,
                                 "average_roi": 0})
        )
    )
    source = ApiDelpiTransformaOverviewSource(_client(handler))
    result = await source.fetch(CTX, query=query)
    assert all(ind.scope == "consolidado" for ind in result.indicators)


# --- Strategic Indicators (IDD) ---


async def test_si_scores_mapped_by_indicator_id():
    item = {
        "department_id": "engineering",
        "score": 91.0,
        "indicators": [
            {"indicator_id": "engineering-projects-on-time",
             "score": 94.0},
            {"indicator_id": "engineering-transforma-plus",
             "score": 88.0},
            {"indicator_id": "other", "score": 10},
        ],
    }
    captured, handler = _capture(
        lambda req: httpx.Response(200, json=_envelope({"item": item}))
    )
    source = ApiDelpiEngineeringSiSource(_client(handler))

    scores = await source.fetch_scores(CTX, query=QUERY)

    assert scores == {
        "engineering-projects-on-time": 94.0,
        "engineering-transforma-plus": 88.0,
        "other": 10.0,
    }
    request = captured["request"]
    assert request.url.params["department_id"] == "engineering"
    assert request.url.params["competence"] == "2026-10"
    assert request.url.params["branch"] == "01"
    assert request.headers["Authorization"] == "Bearer user-jwt-1"


async def test_si_failure_returns_none():
    _, handler = _capture(lambda req: httpx.Response(500))
    source = ApiDelpiEngineeringSiSource(_client(handler))
    assert await source.fetch_scores(CTX, query=QUERY) is None


async def test_si_forbidden_returns_none():
    _, handler = _capture(lambda req: httpx.Response(403))
    source = ApiDelpiEngineeringSiSource(_client(handler))
    assert await source.fetch_scores(CTX, query=QUERY) is None
