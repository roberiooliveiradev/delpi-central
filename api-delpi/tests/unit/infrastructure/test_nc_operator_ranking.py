"""GLPI #1538 — contrato do ranking de NC por operador."""

from __future__ import annotations

from unittest.mock import patch

import httpx

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.application.use_cases.nonconformity.get_operator_ranking_use_case import (
    build_operator_ranking,
)
from app.infrastructure.gateways import portal_rh_nonconformity_operator_gateway as rh
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_operator_ranking_repository import (
    NonconformityOperatorRankingRepository,
)


def _repo():
    repo = NonconformityOperatorRankingRepository()
    repo._connect = lambda: None
    repo._close = lambda *a, **kw: None
    return repo


def test_query_aggregates_all_current_ncs_and_preserves_filters():
    repo = _repo()
    with patch.object(repo, "execute_query", return_value=[]) as execute:
        repo.count_by_operator_and_defect(
            ListNonconformityRequest(
                type="internal",
                branch="02",
                date_start="2026-11-01",
                date_end="2026-11-06",
                status="3",
                item_code="9026",
                description="TERMOSTATO",
                page=2,
                page_size=20,
            )
        )

    sql, params = execute.call_args[0]
    assert "QI2_OPERAD" in sql
    assert "QI2_DESCR" in sql
    assert "QI2_OBSOL <> 'S'" in sql
    assert "D_E_L_E_T_ = ''" in sql
    assert "GROUP BY" in sql
    assert "OFFSET" not in sql
    assert "QI2_OCORRE" in sql
    assert "QI2_FILIAL" in sql
    assert "QI2_TIPO" in sql
    assert "QI2_STATUS" in sql
    assert "QI2_ITEM" in sql
    assert "9026" not in sql
    assert "9026" in str(params)


def test_top_five_detail_counts_all_descriptions_and_history():
    rows = [
        {"operator_code": "001", "defect": "ITEM TROCADO", "nc_count": 7},
        {"operator_code": "001", "defect": "MONTAGEM INCORRETA", "nc_count": 3},
        {"operator_code": "002", "defect": "ITEM TROCADO", "nc_count": 5},
        {"operator_code": "003", "defect": "X", "nc_count": 4},
        {"operator_code": "004", "defect": "X", "nc_count": 3},
        {"operator_code": "005", "defect": "X", "nc_count": 2},
        {"operator_code": "006", "defect": "X", "nc_count": 1},
        {"operator_code": "  ", "defect": "X", "nc_count": 99},
    ]
    resolved = []
    def resolve(code):
        resolved.append(code)
        return {"001": "ANA EXEMPLO"}.get(code)
    result = build_operator_ranking(rows, resolve_name=resolve)
    assert len(result["ranking"]) == 5
    assert result["ranking"][0]["operator_code"] == "001"
    assert result["ranking"][0]["operator_name"] == "ANA EXEMPLO"
    assert result["ranking"][0]["total_ncs"] == 10
    assert result["ranking"][0]["main_defect"] == "ITEM TROCADO"
    assert result["detail"]["defect_types_count"] == 2
    assert sum(x["count"] for x in result["detail"]["defects"]) == 10
    assert result["total_operators"] == 6
    assert len(resolved) == 5  # não faz lookup N+1 de todos os operadores


def test_can_select_operator_outside_top_five_with_fallback_label():
    rows = [
        {"operator_code": f"{i:03d}", "defect": "X", "nc_count": 20 - i}
        for i in range(1, 8)
    ]
    result = build_operator_ranking(
        rows,
        selected_code="007",
        resolve_name=lambda code: None,
    )
    assert result["detail"]["operator_code"] == "007"
    assert result["detail"]["operator_name"] == "Operador 007"
    assert result["detail"]["total_ncs"] == 13


def test_portal_rh_name_lookup_preserves_leading_zeros(monkeypatch):
    rh._cache.clear()
    monkeypatch.setenv("PORTAL_RH_API_URL", "http://portal-rh.test:8000")
    monkeypatch.setenv("PORTAL_RH_API_SERVICE_TOKEN", "secret")
    captured = {}

    def fake_get(url, *, headers, **kwargs):
        captured.update(url=url, headers=headers)
        return httpx.Response(200, json={
            "registration": "001", "full_name": "OPERADORA EXEMPLO"
        })

    monkeypatch.setattr(rh.httpx, "get", fake_get)
    assert rh.resolve_nc_operator_name("001") == "OPERADORA EXEMPLO"
    assert captured["url"].endswith("/collaborators/001/")
    assert captured["headers"]["X-Delpi-Service-Token"] == "secret"
    rh._cache.clear()


def test_portal_rh_unavailable_retains_operator_code(monkeypatch):
    rh._cache.clear()
    monkeypatch.setenv("PORTAL_RH_API_URL", "http://portal-rh.test")
    monkeypatch.setenv("PORTAL_RH_API_SERVICE_TOKEN", "secret")
    monkeypatch.setattr(
        rh.httpx,
        "get",
        lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("offline")),
    )
    assert rh.resolve_nc_operator_name("002") is None
    assert build_operator_ranking(
        [{"operator_code": "002", "defect": "X", "nc_count": 1}],
        resolve_name=rh.resolve_nc_operator_name,
    )["ranking"][0]["operator_name"] == "Operador 002"
    rh._cache.clear()
