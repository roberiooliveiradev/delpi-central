"""R10 cost-center-expenses — HTTP contract (S2S + delegated user +
scope) and engine tests over a fake repository (doc 126/127).

Historical-selection parity (353 lines / R$ 169.704,12 / 139 docs /
46 CC buckets for 2026-09/01) was proven live against the TOTVS
database during IMPLEMENTATION-STAGE-01; these tests pin the predicate,
the universe partition, the implemented DV-R10 subset and the route
contract so the selection cannot silently drift.
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
R10 = "/financeiro/cost-center-expenses"


@pytest.fixture
def r10_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.cost_center_expenses_router import (
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


def test_router_exposes_r10_routes() -> None:
    from app.interface.http.routes.financeiro.cost_center_expenses_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert {f"{R10}", f"{R10}/export"} <= paths
    operation_ids = {
        getattr(route, "operation_id", None) for route in router.routes
    }
    assert {
        "get_financeiro_cost_center_expenses",
        "export_financeiro_cost_center_expenses",
    } <= operation_ids


def test_missing_service_header_returns_401(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = r10_client.get(f"{R10}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = r10_client.get(f"{R10}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_wrong_client_returns_403(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = r10_client.get(f"{R10}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    response = r10_client.get(f"{R10}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_flag_off_returns_typed_403(
    r10_client: TestClient, monkeypatch
) -> None:
    """Dataset gate closed: valid S2S + delegated user still gets
    `scope_unavailable`, never real rows."""
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    from app.application.security.stock_inventory_scope import (
        SharedDatasetStockInventoryScopeResolver,
    )

    monkeypatch.setattr(
        "app.composition.financeiro_cost_center_expenses_composer."
        "get_stock_inventory_scope_resolver",
        lambda: SharedDatasetStockInventoryScopeResolver(enabled=False),
    )
    response = r10_client.get(f"{R10}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403
    body = response.json()
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "scope_unavailable"


def test_service_principal_as_user_does_not_unlock(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = r10_client.get(f"{R10}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_invalid_period_returns_400(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = r10_client.get(f"{R10}?period=bad", headers=S2S_HEADERS)
    assert response.status_code in (400, 422)


def test_invalid_universe_returns_400(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = r10_client.get(
        f"{R10}?{PERIOD}&universe=combined", headers=S2S_HEADERS
    )
    assert response.status_code in (400, 422)


def _fake_response():
    result = MagicMock()
    result.to_dict.return_value = {
        "report": "cost-center-expenses",
        "reportId": "R10",
        "period": "2026-09",
        "universe": "calculation",
        "status": "available",
        "parityStatus": "PENDING",
        "summary": {"lineCount": 1},
        "items": [{"productCode": "P1"}],
        "findings": [],
    }
    return result


def test_happy_path_envelope_and_params(
    r10_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = _fake_response()
    import app.interface.http.routes.financeiro.cost_center_expenses_router as mod

    monkeypatch.setattr(
        mod, "build_cost_center_expenses_use_case", lambda: use_case
    )
    response = r10_client.get(
        f"{R10}?{PERIOD}&branch=01&universe=investigation"
        f"&view=divergences&cost_center=0401&tes=101",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["meta"]["operationId"] == "get_financeiro_cost_center_expenses"
    assert body["data"]["reportId"] == "R10"
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.universe == "investigation"
    assert request_arg.view == "divergences"
    assert request_arg.cost_center == "0401"
    assert request_arg.tes == "101"
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"


def test_export_streams_document_bytes(
    r10_client: TestClient, monkeypatch
) -> None:
    import io

    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = {
        "stream": io.BytesIO(b"a,b\n1,2\n"),
        "content_type": "text/csv",
        "filename": "cost-center-expenses-2026-09-01-calculation.csv",
        "exported_count": 2,
    }
    import app.interface.http.routes.financeiro.cost_center_expenses_router as mod

    monkeypatch.setattr(
        mod, "build_export_cost_center_expenses_use_case", lambda: use_case
    )
    response = r10_client.get(
        f"{R10}/export?{PERIOD}&format=csv&universe=investigation",
        headers=S2S_HEADERS,
    )
    assert response.status_code == 200
    kwargs = use_case.execute.call_args.kwargs
    assert kwargs["export_format"] == "csv"
    assert kwargs["user_subject"] == "user-1"
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.universe == "investigation"


# -- engine (use case over a fake repository) ---------------------------------


def _row(**overrides):
    row = {
        "line_id": 1,
        "branch_code": "01",
        "document": "000123",
        "series": "001",
        "item": "001",
        "sequence_number": "000001",
        "product_code": "P1",
        "product_description": "Produto",
        "product_type": "PA",
        "product_group": "2000",
        "document_type": "N",
        "cost_center": "0404",
        "cost_center_description": "MANUTENCAO DE MAQUINAS",
        "cost_center_class_kind": "2",
        "cost_center_blocked": "2",
        "account_code": "31101001",
        "tes": "101",
        "cf": "1102",
        "supplier_code": "F001",
        "supplier_store": "01",
        "supplier_name": "Fornecedor",
        "warehouse": "01",
        "order_number": "",
        "entry_date": "20260905",
        "issue_date": "20260901",
        "quantity": "1.000000000",
        "unit_value": "100.000000000",
        "total_value": "100.000000000",
    }
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
    from app.application.use_cases.financeiro_cost_center_expenses.list_cost_center_expenses_use_case import (
        ListCostCenterExpensesUseCase,
    )

    return ListCostCenterExpensesUseCase(
        repository=_FakeRepository(rows),
        scope_resolver=SharedDatasetStockInventoryScopeResolver(
            enabled=True
        ),
    )


def _request(**overrides):
    from app.application.dto.financeiro_cost_center_expenses.cost_center_expenses_request import (
        CostCenterExpensesRequest,
    )

    params = {"period": "2026-09", "branch": "01"}
    params.update(overrides)
    return CostCenterExpensesRequest.from_query(**params)


def test_scope_unresolved_raises() -> None:
    from app.application.security.stock_inventory_scope import (
        StockInventoryScopeUnavailableError,
        UnresolvedStockInventoryScopeResolver,
    )
    from app.application.use_cases.financeiro_cost_center_expenses.list_cost_center_expenses_use_case import (
        ListCostCenterExpensesUseCase,
    )

    use_case = ListCostCenterExpensesUseCase(
        repository=_FakeRepository([]),
        scope_resolver=UnresolvedStockInventoryScopeResolver(),
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        use_case.execute(_request(), user_subject="user-1")


def test_calculation_universe_partitions_rows() -> None:
    """calculation keeps only the official-selection rows; every MP,
    excluded-TES and benefit line stays out."""
    rows = [
        _row(line_id=1, tes="101", product_type="PA"),
        _row(line_id=2, tes="001", product_type="PA"),  # excluded TES
        _row(line_id=3, tes="101", product_type="MP"),  # raw material
        _row(
            line_id=4,
            tes="046",
            product_type="GG",
            product_group="4100",
            cost_center="",
        ),  # benefit line
    ]
    response = _use_case(rows).execute(
        _request(universe="calculation"), user_subject="u"
    )
    assert response.summary is not None
    assert response.summary.lineCount == 1
    assert response.summary.totalValue == "100.00"
    assert response.items[0].lineId == 1


def test_investigation_universe_is_the_complement() -> None:
    """investigation returns exactly the rows the selection excluded —
    totals never mix with the calculation universe."""
    rows = [
        _row(line_id=1, tes="101", product_type="PA"),
        _row(line_id=2, tes="001", product_type="PA"),
        _row(
            line_id=3,
            tes="101",
            product_type="MP",
            cost_center="0401",
            total_value="250.50",
        ),
    ]
    response = _use_case(rows).execute(
        _request(universe="investigation"), user_subject="u"
    )
    assert response.summary is not None
    assert response.summary.lineCount == 2
    assert response.summary.totalValue == "350.50"
    exclusions = {item.calculationExclusion for item in response.items}
    assert exclusions == {"tes_excluded", "raw_material_product"}


def test_missing_cost_center_finding() -> None:
    """DV-R10-04 — expense line without cost center."""
    rows = [_row(cost_center="", cost_center_class_kind="")]
    response = _use_case(rows).execute(_request(), user_subject="u")
    rules = {f.ruleId for f in response.findings}
    assert "DV-R10-04" in rules
    finding = next(
        f for f in response.findings if f.ruleId == "DV-R10-04"
    )
    assert finding.status == "POSSIBLE_DIVERGENCE"
    assert "Protheus" in finding.erpReviewGuidance
    assert finding.sourceRecord["document"] == "000123"


def test_cc_not_in_catalog_finding() -> None:
    """DV-R10-02 — cost center absent from the current CTT catalog."""
    rows = [
        _row(
            cost_center="9999",
            cost_center_class_kind="",
            cost_center_blocked="",
        )
    ]
    response = _use_case(rows).execute(_request(), user_subject="u")
    rules = {f.ruleId for f in response.findings}
    assert "DV-R10-02" in rules
    item = response.items[0]
    assert item.costCenterCatalogStatus == "not_registered"


def test_mp_with_cost_center_fires_only_in_investigation() -> None:
    """DV-R10-01 — MP rows live in the investigation universe; the rule
    never fires inside the calculation universe."""
    rows = [
        _row(line_id=1, product_type="MP", tes="101", cost_center="0401"),
        _row(line_id=2, product_type="PA", tes="101"),
    ]
    investigation = _use_case(rows).execute(
        _request(universe="investigation"), user_subject="u"
    )
    rules = {f.ruleId for f in investigation.findings}
    assert "DV-R10-01" in rules
    calculation = _use_case(rows).execute(
        _request(universe="calculation"), user_subject="u"
    )
    calc_rules = {f.ruleId for f in calculation.findings}
    assert "DV-R10-01" not in calc_rules


def test_every_row_is_unclassified() -> None:
    """DV-R10-05/D-01 — no homologated class exists; every line is
    UNCLASSIFIED, never an inferred Direto/Indireto/Adm."""
    rows = [_row(), _row(line_id=2, cost_center="")]
    response = _use_case(rows).execute(_request(), user_subject="u")
    assert {i.costClass for i in response.items} == {"UNCLASSIFIED"}
    assert response.summary is not None
    assert response.summary.unclassifiedCount == 2


def test_blocked_rules_declared_not_executed() -> None:
    """DV-R10-03 and DV-R10-06 depend on the pending E10a catalog —
    declared in rulesCatalog, never fired."""
    rows = [_row()]
    response = _use_case(rows).execute(_request(), user_subject="u")
    catalog = {r["ruleId"]: r for r in response.rulesCatalog}
    assert catalog["DV-R10-03"]["implemented"] is False
    assert catalog["DV-R10-06"]["implemented"] is False
    fired = {f.ruleId for f in response.findings}
    assert "DV-R10-03" not in fired
    assert "DV-R10-06" not in fired
    # The historical cases (0401/0404 are registered in CTT today) must
    # NOT be auto-marked invalid by the catalog check alone.
    assert "DV-R10-02" not in fired


def test_view_divergences_filters_items_not_summary() -> None:
    rows = [
        _row(line_id=1, cost_center=""),  # has DV-R10-04 finding
        _row(line_id=2),
    ]
    response = _use_case(rows).execute(
        _request(view="divergences"), user_subject="u"
    )
    assert len(response.items) == 1
    assert response.summary is not None
    assert response.summary.lineCount == 2  # summary covers the universe
    assert response.pagination["universe_items"] == 2
    assert response.pagination["total_items"] == 1


def test_summary_cost_center_buckets_count_empty_group() -> None:
    """The historical artifact counts the no-CC group among its 46
    centers — the bucket count includes it."""
    rows = [
        _row(line_id=1, cost_center="0401"),
        _row(line_id=2, cost_center="0404"),
        _row(line_id=3, cost_center=""),
    ]
    response = _use_case(rows).execute(_request(), user_subject="u")
    assert response.summary is not None
    assert response.summary.costCenterCount == 3
    labels = {b["costCenter"] for b in response.summary.byCostCenter}
    assert labels == {"0401", "0404", None}


def test_monetary_totals_quantized_at_2dp() -> None:
    rows = [
        _row(line_id=1, total_value="10.005"),
        _row(line_id=2, total_value="0.005"),
    ]
    response = _use_case(rows).execute(_request(), user_subject="u")
    assert response.summary is not None
    assert Decimal(response.summary.totalValue) == Decimal("10.01")


def test_pagination_is_stable_and_sliced() -> None:
    rows = [_row(line_id=i, document=f"DOC{i:03d}") for i in range(1, 8)]
    response = _use_case(rows).execute(
        _request(page=2, page_size=3), user_subject="u"
    )
    assert response.pagination["page"] == 2
    assert response.pagination["total_items"] == 7
    assert len(response.items) == 3


def test_selection_metadata_declares_axis_and_exclusions() -> None:
    response = _use_case([_row()]).execute(_request(), user_subject="u")
    selection = response.selection
    assert selection["axis"] == "D1_DTDIGIT"
    assert selection["grain"] == "sd1_item"
    assert len(selection["excludedTes"]) == 13
    assert selection["excludeMp"] is True
    assert selection["excludeBenefits"] is True
    assert response.parityStatus == "PENDING"
    assert response.provenance["officialProducer"] == "EDAPP"


def test_empty_universe_is_honest_not_error() -> None:
    response = _use_case([]).execute(_request(), user_subject="u")
    assert response.status == "no_matching_items"
    assert response.items == []
    assert response.summary is not None
    assert response.summary.lineCount == 0


# -- SQL builder ---------------------------------------------------------------


def test_sql_uses_dtdigit_axis_and_is_parameterized() -> None:
    from app.infrastructure.persistence.totvs.financeiro_cost_center_expenses.cost_center_expenses_sql import (
        build_lines_query,
    )

    sql, params = build_lines_query(
        period_start="20260901",
        period_end="20260930",
        branches=("01",),
        cost_center="0401",
        product_code=None,
        document=None,
        supplier_code=None,
        tes=None,
    )
    assert "D1_DTDIGIT BETWEEN ? AND ?" in sql
    assert "D1_EMISSAO BETWEEN" not in sql
    assert "CTT010" in sql
    assert "0401" not in sql  # every filter is a bound parameter
    assert params[:3] == ["01", "20260901", "20260930"]
    assert params[-1] == "0401"


def test_request_validation() -> None:
    with pytest.raises(ValueError):
        _request(period="2026-13")
    with pytest.raises(ValueError):
        _request(universe="totals")
    with pytest.raises(ValueError):
        _request(view="everything")
    with pytest.raises(ValueError):
        _request(sort="value;drop")
    request = _request(branch="all")
    assert request.period_start() == "20260901"
    assert request.period_end() == "20260930"
