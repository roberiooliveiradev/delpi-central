"""Consumption-audit search & comparison — GLPI #1353 F1/F4.

Covers the new read-only producers:
- ``GET /supplies/consumption-audit/orders`` (paged search)
- ``GET /supplies/consumption-audit/comparison`` (bounded batch 2–10)

Assertions: SELECT-only SQL with ``?`` binding, strict DTO validation,
date-type semantics kept distinct (emission/finished/appointment), S2S
guard identical to the detail route and comparison projection without
mixing units of measure.
"""

from __future__ import annotations

import json
import re
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from delpi_auth.service_identity import ServiceIdentity

from app.application.dto.supplies.get_consumption_audit_comparison_request import (
    GetConsumptionAuditComparisonRequest,
)
from app.application.dto.supplies.search_consumption_audit_orders_request import (
    SearchConsumptionAuditOrdersRequest,
)
from app.application.models.page import Page
from app.application.use_cases.supplies.get_consumption_audit_comparison_use_case import (
    GetConsumptionAuditComparisonUseCase,
)
from app.application.use_cases.supplies.search_consumption_audit_orders_use_case import (
    SearchConsumptionAuditOrdersUseCase,
)
from app.interface.http import s2s_service_access
from app.interface.http.routes.supplies import consumption_audit_router
from app.infrastructure.persistence.totvs.production_repositories import (
    consumption_audit_sql,
)

OP_A = "24884201006"
OP_B = "24884201002"

IDENTITY = ServiceIdentity(
    client_id="supplies-api",
    subject="service-account-subject",
    scopes=frozenset({"consumption-audit.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)

_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|GRANT)\b",
    re.IGNORECASE,
)


def _assert_select_only(sql: str) -> None:
    normalized = re.sub(r"\s+", " ", sql).strip()
    assert normalized.upper().startswith("SELECT"), normalized[:80]
    assert not _FORBIDDEN.search(normalized), normalized
    assert ";" not in normalized


# --------------------------------------------------------------- SQL


def test_search_where_requires_branch_and_binds_params():
    where, params = consumption_audit_sql.orders_search_where(branch="01")
    assert "OP.C2_FILIAL = ?" in where
    assert params == ("01",)


def test_search_where_binds_search_product_status():
    where, params = consumption_audit_sql.orders_search_where(
        branch="01",
        search="248842",
        product="CABO",
        status="A",
        work_center="CT-2",
        operation="01",
    )
    assert "C2_OP" in where and "C2_NUM" in where
    assert "B1_DESC" in where
    assert "C2_STATUS" in where
    assert "H8_CTRAB" in where and "H8_OPER" in where
    # search + product usam curingas; status/work_center/operation exatos/like
    assert params[0] == "01"
    assert "%248842%" in params
    assert "%CABO%" in params
    assert "A" in params
    assert "%CT-2%" in params
    assert "01" in params
    assert where.count("?") == len(params)


def test_search_where_escapes_like_wildcards():
    _, params = consumption_audit_sql.orders_search_where(
        branch="01", search="50%"
    )
    assert "%50\\%%" in params
    assert "ESCAPE" in consumption_audit_sql.orders_search_where(
        branch="01", search="50%"
    )[0]


def test_date_type_columns_are_distinct():
    where_e, _ = consumption_audit_sql.orders_search_where(
        branch="01", date_type="emission", period_start="2026-10-01"
    )
    where_f, _ = consumption_audit_sql.orders_search_where(
        branch="01", date_type="finished", period_start="2026-10-01"
    )
    assert "C2_EMISSAO" in where_e and "C2_DATRF" not in where_e
    assert "C2_DATRF" in where_f and "C2_EMISSAO" not in where_f


def test_appointment_date_type_uses_sh6_exists():
    where, params = consumption_audit_sql.orders_search_where(
        branch="01",
        date_type="appointment",
        period_start="2026-10-01",
        period_end="2026-10-31",
    )
    assert "SH6010" in where
    assert "H6_DTAPONT" in where
    assert "C2_EMISSAO" not in where
    assert params[-2:] == ("2026-10-01", "2026-10-31")


def test_invalid_date_type_rejected():
    with pytest.raises(ValueError):
        consumption_audit_sql.orders_search_where(
            branch="01", date_type="planned"
        )


def test_search_and_count_sql_are_select_only_with_paging():
    where, params = consumption_audit_sql.orders_search_where(
        branch="01", period_start="2026-10-01", period_end="2026-10-31"
    )
    list_sql = consumption_audit_sql.orders_search_sql(where)
    count_sql = consumption_audit_sql.orders_search_count_sql(where)
    _assert_select_only(list_sql)
    _assert_select_only(count_sql)
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in list_sql
    assert where.count("?") == len(params)


# --------------------------------------------------------------- DTO


def test_dto_defaults_and_normalization():
    dto = SearchConsumptionAuditOrdersRequest(branch="01")
    assert dto.branch == "01"
    assert dto.date_type == "emission"
    assert dto.page == 1 and dto.page_size == 25
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="1")
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="03")


def test_dto_rejects_bad_date_type_and_period_order():
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="01", date_type="x")
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(
            branch="01",
            period_start="2026-11-01",
            period_end="2026-10-01",
        )


def test_dto_rejects_bad_date_format_and_search():
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(
            branch="01", period_start="29/10/2026"
        )
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="01", search="AB C!")


def test_dto_page_bounds():
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="01", page=0)
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="01", page_size=0)
    with pytest.raises(ValueError):
        SearchConsumptionAuditOrdersRequest(branch="01", page_size=51)


def test_comparison_dto_rules():
    with pytest.raises(ValueError):
        GetConsumptionAuditComparisonRequest(
            branch="01", production_orders=(OP_A,)
        )
    with pytest.raises(ValueError):
        GetConsumptionAuditComparisonRequest(
            branch="01", production_orders=tuple([OP_A] * 3)
        )
    with pytest.raises(ValueError):
        GetConsumptionAuditComparisonRequest(
            branch="01", production_orders=(OP_A, "XYZ")
        )
    with pytest.raises(ValueError):
        GetConsumptionAuditComparisonRequest(
            branch="01", production_orders=tuple(f"248842010{i:02d}" for i in range(11))
        )
    dto = GetConsumptionAuditComparisonRequest(
        branch="01", production_orders=(OP_A, OP_B)
    )
    assert dto.branch == "01"
    assert dto.production_orders == (OP_A, OP_B)


# --------------------------------------------------------------- use cases


class _Repo:
    def __init__(self):
        self.count_calls = []
        self.search_calls = []

    def count_orders(self, **filters):
        self.count_calls.append(filters)
        return 3

    def search_orders(self, **filters):
        self.search_calls.append(filters)
        return [{"production_order": OP_A}]


def test_search_use_case_paginates_and_passes_filters():
    repo = _Repo()
    uc = SearchConsumptionAuditOrdersUseCase(repo)
    dto = SearchConsumptionAuditOrdersRequest(
        branch="01",
        search="248842",
        date_type="finished",
        period_start="2026-10-01",
        period_end="2026-10-31",
        page=2,
        page_size=10,
    )
    page = uc.execute(dto)
    assert page.total == 3 and page.page == 2 and page.page_size == 10
    assert repo.count_calls[0]["date_type"] == "finished"
    assert repo.search_calls[0]["offset"] == 10
    assert repo.search_calls[0]["limit"] == 10


class _DetailUC:
    def __init__(self, detail_by_op):
        self._detail = detail_by_op

    def execute(self, dto):
        return self._detail.get(dto.production_order)


def _detail(op: str) -> dict:
    return {
        "branch": "01",
        "production_order": op,
        "order": {"product_code": "P1"},
        "operations": [
            {
                "operation": "01",
                "work_center": "CT-23",
                "execution_evidence": {"execution_state": "evidenced"},
                "components": [
                    {
                        "component_code": "C1",
                        "component_description": "cabo",
                        "component_type": "MP",
                        "unit_of_measure": "MT",
                        "bom": {"theoretical_quantity": 80.75},
                        "commitment": {
                            "original_quantity": 80.75,
                            "open_quantity": 0.0,
                            "derived_consumed_quantity": 80.75,
                        },
                        "movements": {"eligible_consumption_quantity": 80.75},
                        "discrepancy": {"value": 0.0},
                        "classification": "reconciled",
                    },
                    {
                        "component_code": "C2",
                        "component_description": "terminal",
                        "component_type": "MP",
                        "unit_of_measure": "PC",
                        "bom": {"theoretical_quantity": 250.0},
                        "commitment": {
                            "original_quantity": 250.0,
                            "open_quantity": 250.0,
                            "derived_consumed_quantity": 0.0,
                        },
                        "movements": {"eligible_consumption_quantity": 0.0},
                        "discrepancy": {"value": 0.0},
                        "classification": "requires_investigation",
                    },
                ],
            }
        ],
        "unmatched_movements": [{"document": "1"}],
        "related_orders": [{"production_order": "x"}],
        "quality": {"status": "partial", "warnings": []},
    }


def test_comparison_projects_and_separates_uoms():
    uc = GetConsumptionAuditComparisonUseCase(
        _DetailUC({OP_A: _detail(OP_A), OP_B: _detail(OP_B)})
    )
    result = uc.execute(
        GetConsumptionAuditComparisonRequest(
            branch="01", production_orders=(OP_A, OP_B)
        )
    )
    assert result["not_found"] == []
    assert len(result["items"]) == 2
    item = result["items"][0]
    totals = {t["unit_of_measure"]: t for t in item["totals_by_unit"]}
    # MT e PC nunca misturados
    assert totals["MT"]["theoretical_quantity"] == 80.75
    assert totals["MT"]["eligible_consumption_quantity"] == 80.75
    assert totals["PC"]["committed_quantity"] == 250.0
    assert item["operations"][0]["execution_state"] == "evidenced"
    assert item["unmatched_movements_count"] == 1


def test_comparison_reports_not_found():
    uc = GetConsumptionAuditComparisonUseCase(
        _DetailUC({OP_A: _detail(OP_A)})
    )
    result = uc.execute(
        GetConsumptionAuditComparisonRequest(
            branch="01", production_orders=(OP_A, OP_B)
        )
    )
    assert result["not_found"] == [OP_B]
    assert len(result["items"]) == 1


# --------------------------------------------------------------- router


def _request(*, s2s_header: str | None = None):
    headers = {}
    if s2s_header is not None:
        headers["X-Delpi-Service-Authorization"] = s2s_header
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _validator(*, identity=IDENTITY):
    validator = Mock()
    validator.validate.return_value = identity
    return validator


def _search_call(*, s2s_header="Bearer svc-jwt", use_case=None, **kwargs):
    request = _request(s2s_header=s2s_header)
    patches = [
        patch.object(s2s_service_access, "get_request", return_value=request),
        patch.object(
            consumption_audit_router,
            "build_search_consumption_audit_orders_use_case",
            return_value=use_case
            or Mock(
                execute=Mock(
                    return_value=Page(items=[], total=0, page=1, page_size=25)
                )
            ),
        ),
        patch.object(
            s2s_service_access.ServiceTokenValidator,
            "from_env",
            return_value=_validator(),
        ),
    ]
    defaults = {
        "branch": "01", "search": None, "product": None,
        "date_type": "emission", "period_start": None, "period_end": None,
        "status": None, "work_center": None, "operation": None,
        "page": 1, "page_size": 25,
    }
    defaults.update(kwargs)
    try:
        for patcher in patches:
            patcher.start()
        return consumption_audit_router.search_consumption_audit_orders(
            **defaults
        )
    finally:
        for patcher in reversed(patches):
            patcher.stop()


def _comparison_call(*, s2s_header="Bearer svc-jwt", use_case=None, orders=None, branch="01"):
    request = _request(s2s_header=s2s_header)
    patches = [
        patch.object(s2s_service_access, "get_request", return_value=request),
        patch.object(
            consumption_audit_router,
            "build_get_consumption_audit_comparison_use_case",
            return_value=use_case or Mock(execute=Mock(return_value={"items": []})),
        ),
        patch.object(
            s2s_service_access.ServiceTokenValidator,
            "from_env",
            return_value=_validator(),
        ),
    ]
    try:
        for patcher in patches:
            patcher.start()
        return consumption_audit_router.get_consumption_audit_comparison(
            orders=orders or f"{OP_A},{OP_B}", branch=branch
        )
    finally:
        for patcher in reversed(patches):
            patcher.stop()


def test_search_route_valid_s2s_returns_envelope():
    uc = Mock()
    uc.execute.return_value = Page(
        items=[{"production_order": OP_A}], total=40, page=2, page_size=25
    )
    response = _search_call(use_case=uc, search="248842", page=2)
    assert response.status_code == 200
    body = json.loads(response.body)
    assert body["success"] is True
    dto = uc.execute.call_args.args[0]
    assert dto.search == "248842" and dto.page == 2


def test_search_route_page_serializes_total_pages():
    """Regressão GLPI #1353: ``Page`` dataclass via ``jsonable_encoder``
    descartava a property ``total_pages`` → 200 sem o campo → o guard do
    MFE derrubava a resposta como «Resposta inválida do servidor». O
    router serializa ``result.to_dict()`` (mesma convenção dos demais
    routers que devolvem Page)."""
    uc = Mock()
    uc.execute.return_value = Page(
        items=[{"production_order": OP_A}], total=40, page=1, page_size=25
    )
    response = _search_call(use_case=uc, date_type="appointment",
                            period_start="2026-10-29",
                            period_end="2026-10-29")
    assert response.status_code == 200
    data = json.loads(response.body)["data"]
    assert data["items"] == [{"production_order": OP_A}]
    assert data["page"] == 1
    assert data["page_size"] == 25
    assert data["total"] == 40
    assert data["total_pages"] == 2


def test_search_route_invalid_params_are_400():
    assert _search_call(date_type="nope").status_code == 400
    assert _search_call(period_start="2026-13-99").status_code == 400
    assert _search_call(page=0).status_code == 400
    assert _search_call(page_size=99).status_code == 400


def test_search_route_missing_branch_is_400():
    assert _search_call(branch=None).status_code == 400


def test_search_route_use_case_failure_is_500_sanitized():
    uc = Mock()
    uc.execute.side_effect = RuntimeError("db down")
    response = _search_call(use_case=uc)
    assert response.status_code == 500
    assert "db down" not in json.loads(response.body)["message"]


def test_comparison_route_valid_and_invalid():
    response = _comparison_call()
    assert response.status_code == 200
    assert _comparison_call(orders=OP_A).status_code == 400
    assert _comparison_call(orders=f"{OP_A},BAD").status_code == 400
    many = ",".join(f"248842010{i:02d}" for i in range(11))
    assert _comparison_call(orders=many).status_code == 400


def test_comparison_route_invalid_s2s_token_denied():
    from delpi_auth.service_errors import ServiceTokenInvalidError

    request = _request(s2s_header="Bearer bad-jwt")
    validator = Mock()
    validator.validate.side_effect = ServiceTokenInvalidError("invalid")
    with patch.object(
        s2s_service_access, "get_request", return_value=request
    ), patch.object(
        s2s_service_access.ServiceTokenValidator,
        "from_env",
        return_value=validator,
    ), pytest.raises(Exception):
        consumption_audit_router.get_consumption_audit_comparison(
            orders=f"{OP_A},{OP_B}", branch="01"
        )
