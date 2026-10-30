"""R11 billing-exclusion roster — HTTP contract (S2S + delegated user +
scope) and engine tests over a fake repository (doc 126/127).

Historical-selection parity (11 lines / R$ 97.462,71 / 11 docs / 3 docs
without a stock-moving sibling item for 2026-09/01) was proven live
against the TOTVS database during IMPLEMENTATION-STAGE-02; these tests
pin the observed predicate, the candidates/out-of-criteria split, the
implemented DV-R11 subset and the route contract so the selection
cannot silently drift.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from delpi_auth.service_errors import (
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceTokenInvalidError,
)
from delpi_auth.service_identity import ServiceIdentity

VALID_IDENTITY = ServiceIdentity(
    client_id="controllership-finance-api",
    subject="service-account-cf",
    scopes=frozenset({"stock-inventory.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)

S2S_HEADERS = {
    "X-Delpi-Service-Authorization": "Bearer service-jwt",
    "X-Delpi-Caller-App": "controllership-finance-api",
    "Authorization": "Bearer user-jwt",
}

PERIOD = "period=2026-09"
R11 = "/financeiro/billing-exclusion-roster"


@pytest.fixture
def r11_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.billing_exclusion_roster_router import (
        router,
    )

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _request_headers(headers):
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _validator(identity=VALID_IDENTITY, error=None):
    validator = MagicMock()
    if error is not None:
        validator.validate.side_effect = error
    else:
        validator.validate.return_value = identity
    return validator


def _patch_s2s(monkeypatch, request, validator=None):
    monkeypatch.setattr(
        "app.interface.http.s2s_service_access.get_request",
        lambda: request,
    )
    if validator is not None:
        monkeypatch.setattr(
            "app.interface.http.s2s_service_access.ServiceTokenValidator.from_env",
            classmethod(lambda cls: validator),
        )


def _patch_user(monkeypatch, principal_type="user"):
    user = SimpleNamespace(
        id="user-1",
        email="user@delpi.local",
        principal_type=principal_type,
    )
    monkeypatch.setattr(
        "app.interface.http.routes.financeiro.stock_inventory_route_helpers."
        "resolve_user_context",
        lambda: user,
    )


# -- route surface ------------------------------------------------------------


def test_router_exposes_r11_routes() -> None:
    from app.interface.http.routes.financeiro.billing_exclusion_roster_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert {f"{R11}", f"{R11}/export"} <= paths
    operation_ids = {
        getattr(route, "operation_id", None) for route in router.routes
    }
    assert {
        "get_financeiro_billing_exclusion_roster",
        "export_financeiro_billing_exclusion_roster",
    } <= operation_ids


def test_missing_service_header_returns_401(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = r11_client.get(f"{R11}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = r11_client.get(f"{R11}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_wrong_client_returns_403(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = r11_client.get(f"{R11}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    response = r11_client.get(f"{R11}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_flag_off_returns_typed_403(
    r11_client: TestClient, monkeypatch
) -> None:
    """Dataset gate closed: valid S2S + delegated user still gets
    `scope_unavailable`, never real rows."""
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    from app.application.security.stock_inventory_scope import (
        SharedDatasetStockInventoryScopeResolver,
    )

    monkeypatch.setattr(
        "app.composition.financeiro_billing_exclusion_roster_composer."
        "get_stock_inventory_scope_resolver",
        lambda: SharedDatasetStockInventoryScopeResolver(enabled=False),
    )
    response = r11_client.get(f"{R11}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403
    body = response.json()
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "scope_unavailable"


def test_service_principal_as_user_does_not_unlock(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = r11_client.get(f"{R11}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_invalid_period_returns_400(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = r11_client.get(f"{R11}?period=bad", headers=S2S_HEADERS)
    assert response.status_code in (400, 422)


def test_invalid_view_returns_400(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = r11_client.get(
        f"{R11}?{PERIOD}&view=combined", headers=S2S_HEADERS
    )
    assert response.status_code in (400, 422)


def _fake_response():
    result = MagicMock()
    result.to_dict.return_value = {
        "report": "billing-exclusion-roster",
        "reportId": "R11",
        "period": "2026-09",
        "view": "candidates",
        "status": "available",
        "parityStatus": "PENDING",
        "summary": {"lineCount": 1},
        "items": [{"productCode": "P1"}],
        "findings": [],
    }
    return result


def test_happy_path_envelope_and_params(
    r11_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = _fake_response()
    import app.interface.http.routes.financeiro.billing_exclusion_roster_router as mod

    monkeypatch.setattr(
        mod, "build_billing_exclusion_roster_use_case", lambda: use_case
    )
    response = r11_client.get(
        f"{R11}?{PERIOD}&branch=01&view=out_of_criteria"
        f"&product_group=9035&tes=594",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert (
        body["meta"]["operationId"]
        == "get_financeiro_billing_exclusion_roster"
    )
    assert body["data"]["reportId"] == "R11"
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.view == "out_of_criteria"
    assert request_arg.product_group == "9035"
    assert request_arg.tes == "594"
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"


def test_export_streams_document_bytes(
    r11_client: TestClient, monkeypatch
) -> None:
    import io

    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = {
        "stream": io.BytesIO(b"a,b\n1,2\n"),
        "content_type": "text/csv",
        "filename": "billing-exclusion-roster-2026-09-01-candidates.csv",
        "exported_count": 2,
    }
    import app.interface.http.routes.financeiro.billing_exclusion_roster_router as mod

    monkeypatch.setattr(
        mod,
        "build_export_billing_exclusion_roster_use_case",
        lambda: use_case,
    )
    response = r11_client.get(
        f"{R11}/export?{PERIOD}&format=csv&view=all",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    kwargs = use_case.execute.call_args.kwargs
    assert kwargs["export_format"] == "csv"
    assert kwargs["user_subject"] == "user-1"
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.view == "all"


# -- engine (use case over a fake repository) ---------------------------------


def _candidate_row(**overrides):
    """Roster candidate: group 9035 + TES 594, zero stock cost."""
    row = {
        "line_id": 1,
        "branch_code": "01",
        "document": "103033",
        "series": "001",
        "item": "002",
        "sequence_number": "000002",
        "product_code": "90350001",
        "product_description": "SERVICO INDUSTRIALIZACAO",
        "product_type": "SV",
        "product_group": "9035",
        "tes": "594",
        "tes_description": "VENDA DE PRODUCAO DO ESTABELECIMENTO",
        "tes_stock_movement": "N",
        "tes_duplicate_flag": "S",
        "cf": "5101",
        "customer_code": "C001",
        "customer_store": "01",
        "customer_name": "Cliente",
        "account_code": "31101001",
        "warehouse": "01",
        "order_number": "",
        "issue_date": "20260905",
        "quantity": "1.000000000",
        "unit_price": "100.000000000",
        "total_value": "100.000000000",
        "stock_cost": "0.000000000",
        "document_item_count": 1,
        "has_stock_sibling_item": False,
    }
    row.update(overrides)
    return row


def _out_of_criteria_row(**overrides):
    """Related row: group 9035 with a different TES (DV-R11-04)."""
    row = _candidate_row(
        line_id=99,
        document="200001",
        tes="511",
        cf="5102",
        total_value="50.000000000",
        stock_cost="40.000000000",
        has_stock_sibling_item=True,
    )
    row.update(overrides)
    return row


class _FakeRepository:
    def __init__(self, rows):
        self._rows = rows
        self.calls = []

    def fetch_lines(self, **kwargs):
        self.calls.append(kwargs)
        return list(self._rows)


def _use_case(rows):
    from app.application.security.stock_inventory_scope import (
        SharedDatasetStockInventoryScopeResolver,
    )
    from app.application.use_cases.financeiro_billing_exclusion_roster.list_billing_exclusion_roster_use_case import (
        ListBillingExclusionRosterUseCase,
    )

    return ListBillingExclusionRosterUseCase(
        repository=_FakeRepository(rows),
        scope_resolver=SharedDatasetStockInventoryScopeResolver(
            enabled=True
        ),
    )


def _request(**overrides):
    from app.application.dto.financeiro_billing_exclusion_roster.billing_exclusion_roster_request import (
        BillingExclusionRosterRequest,
    )

    params = {"period": "2026-09", "branch": "01"}
    params.update(overrides)
    return BillingExclusionRosterRequest.from_query(**params)


def test_scope_unresolved_raises() -> None:
    from app.application.security.stock_inventory_scope import (
        StockInventoryScopeUnavailableError,
        UnresolvedStockInventoryScopeResolver,
    )
    from app.application.use_cases.financeiro_billing_exclusion_roster.list_billing_exclusion_roster_use_case import (
        ListBillingExclusionRosterUseCase,
    )

    use_case = ListBillingExclusionRosterUseCase(
        repository=_FakeRepository([]),
        scope_resolver=UnresolvedStockInventoryScopeResolver(),
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        use_case.execute(_request(), user_subject="user-1")


def test_candidates_view_keeps_only_observed_predicate() -> None:
    """DV-R11-01 — candidates = group 9035 ∩ TES 594 only; related
    rows never leak into the candidate totals."""
    rows = [
        _candidate_row(line_id=1, document="103033"),
        _candidate_row(
            line_id=2, document="103199", total_value="200.000000000"
        ),
        _out_of_criteria_row(),
    ]
    response = _use_case(rows).execute(
        _request(view="candidates"), user_subject="u"
    )
    assert response.summary is not None
    assert response.summary.lineCount == 3  # summary = full population
    assert response.summary.candidateLineCount == 2
    assert response.summary.outOfCriteriaLineCount == 1
    assert len(response.items) == 2
    assert {i.selectionStatus for i in response.items} == {
        "matches_historical_criteria"
    }
    item_values = {i.document for i in response.items}
    assert item_values == {"103033", "103199"}


def test_out_of_criteria_view_returns_related_rows_separately() -> None:
    """DV-R11-04 — group 9035 with other TES or TES 594 in another
    group: returned with own totals, never marked candidate."""
    rows = [
        _candidate_row(),
        _out_of_criteria_row(line_id=10, document="200001"),
        _candidate_row(
            line_id=11, document="200002", product_group="4100"
        ),  # TES 594, other group
    ]
    response = _use_case(rows).execute(
        _request(view="out_of_criteria"), user_subject="u"
    )
    assert len(response.items) == 2
    assert {
        i.selectionStatus for i in response.items
    } == {"related_out_of_criteria"}
    # Out-of-criteria rows never allege divergence findings.
    assert response.summary is not None
    assert response.summary.outOfCriteriaLineCount == 2


def test_all_view_returns_both_populations() -> None:
    rows = [_candidate_row(), _out_of_criteria_row()]
    response = _use_case(rows).execute(
        _request(view="all"), user_subject="u"
    )
    assert len(response.items) == 2
    statuses = {i.selectionStatus for i in response.items}
    assert statuses == {
        "matches_historical_criteria",
        "related_out_of_criteria",
    }


def test_missing_stock_sibling_finding() -> None:
    """DV-R11-03 — candidate document without a stock-moving sibling
    item: POSSIBLE_DIVERGENCE, never CONFIRMED_ERROR."""
    rows = [
        _candidate_row(line_id=1, has_stock_sibling_item=False),
        _candidate_row(
            line_id=2, document="102779", has_stock_sibling_item=True
        ),
    ]
    response = _use_case(rows).execute(
        _request(view="candidates"), user_subject="u"
    )
    rules = {f.ruleId for f in response.findings}
    assert "DV-R11-03" in rules
    finding = next(
        f for f in response.findings if f.ruleId == "DV-R11-03"
    )
    assert finding.status == "POSSIBLE_DIVERGENCE"
    assert "Protheus" in finding.erpReviewGuidance
    assert finding.sourceRecord["document"] == "103033"
    # The summary counts documents, not lines.
    assert response.summary is not None
    assert response.summary.missingStockSiblingDocumentCount == 1


def test_findings_never_fire_on_out_of_criteria_rows() -> None:
    rows = [
        _out_of_criteria_row(has_stock_sibling_item=False),
    ]
    response = _use_case(rows).execute(
        _request(view="all"), user_subject="u"
    )
    assert response.findings == []


def test_structural_zero_cost_is_explanation_not_finding() -> None:
    """DV-R11-02 — zero D2_CUSTO1 with F4_ESTOQUE='N' is the expected
    structural condition: costStatus flag, never a divergence."""
    rows = [
        _candidate_row(
            line_id=1, stock_cost="0.000000000", tes_stock_movement="N"
        ),
        _candidate_row(
            line_id=2,
            document="999001",
            stock_cost="25.000000000",
            tes_stock_movement="S",
        ),
    ]
    response = _use_case(rows).execute(
        _request(view="candidates"), user_subject="u"
    )
    statuses = {i.lineId: i.costStatus for i in response.items}
    assert statuses[1] == "structural_zero_expected"
    assert statuses[2] == "standard"
    assert response.summary is not None
    assert response.summary.zeroCostCount == 1
    fired = {f.ruleId for f in response.findings}
    assert "DV-R11-02" not in fired


def test_selection_metadata_declares_axis_and_pending_decisions() -> None:
    response = _use_case([_candidate_row()]).execute(
        _request(), user_subject="u"
    )
    selection = response.selection
    assert selection["axis"] == "D2_EMISSAO"
    assert selection["grain"] == "sd2_item"
    assert selection["observedCriteria"] == {
        "productGroup": "9035",
        "tes": "594",
    }
    assert "E11b" in selection["predicateOfficiality"]
    assert "E11a" in selection["affectedCalculation"]
    baseline = selection["historicalBaseline"]
    assert baseline["lineCount"] == 11
    assert baseline["totalValue"] == "97462.71"
    assert baseline["missingStockSiblingDocumentCount"] == 3
    assert response.parityStatus == "PENDING"
    assert response.provenance["officialProducer"] == "EDAPP"
    assert response.provenance["affectedCalculation"] == "TO_INVENTORY"
    assert response.provenance["correctiveAction"] == "PENDING_EVIDENCE"


def test_monetary_totals_quantized_at_2dp() -> None:
    rows = [
        _candidate_row(line_id=1, total_value="10.005"),
        _candidate_row(line_id=2, total_value="0.005"),
    ]
    response = _use_case(rows).execute(
        _request(view="all"), user_subject="u"
    )
    assert response.summary is not None
    assert Decimal(response.summary.totalValue) == Decimal("10.01")


def test_pagination_is_stable_and_sliced() -> None:
    rows = [
        _candidate_row(line_id=i, document=f"DOC{i:03d}")
        for i in range(1, 8)
    ]
    response = _use_case(rows).execute(
        _request(view="all", page=2, page_size=3), user_subject="u"
    )
    assert response.pagination["page"] == 2
    assert response.pagination["total_items"] == 7
    assert response.pagination["population_items"] == 7
    assert len(response.items) == 3


def test_empty_population_is_honest_not_error() -> None:
    response = _use_case([]).execute(_request(), user_subject="u")
    assert response.status == "no_matching_items"
    assert response.items == []
    assert response.summary is not None
    assert response.summary.lineCount == 0


# -- SQL builder ---------------------------------------------------------------


def test_sql_uses_emissao_axis_and_is_parameterized() -> None:
    from app.infrastructure.persistence.totvs.financeiro_billing_exclusion_roster.billing_exclusion_roster_sql import (
        build_lines_query,
    )

    sql, params = build_lines_query(
        period_start="20260901",
        period_end="20260930",
        branches=("01",),
        roster_product_group="9035",
        roster_tes="594",
        product_group=None,
        product_code=None,
        document="103033",
        customer_code=None,
        tes=None,
    )
    assert "D2_EMISSAO BETWEEN ? AND ?" in sql
    assert "D2_EMISSAO" in sql
    assert "SF4010" in sql
    assert "SA1010" in sql
    # Union of both observed predicates — the app splits the views.
    assert "RTRIM(D2.D2_GRUPO) = ? OR RTRIM(D2.D2_TES) = ?" in sql
    assert "103033" not in sql  # every filter is a bound parameter
    assert params == ["01", "20260901", "20260930", "9035", "594", "103033"]
