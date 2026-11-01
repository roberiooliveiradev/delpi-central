"""R09 billing × MOD breakdown — HTTP contract (S2S + delegated user +
scope), engine tests over a fake repository and SQL builder tests
(doc 141, DR-1/DR-2).

The proven DLP204 rules pinned here: levels 02/04/06, direct-children
explosion with edge dedup, propagatedQty = own billed qty else anchor
qty, Quantidade = G2_TEMPAD, Horas = qty × stdTime, and typed
``source_missing`` for every field without proven source (costs,
unmapped MOD bridges, missing route ops).
"""

from __future__ import annotations

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
R09 = "/financeiro/billing-mod-breakdown"


@pytest.fixture
def r09_client() -> TestClient:
    from fastapi import FastAPI

    from app.interface.http.routes.financeiro.billing_mod_breakdown_router import (
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


def test_router_exposes_r09_route() -> None:
    from app.interface.http.routes.financeiro.billing_mod_breakdown_router import (
        router,
    )

    paths = {route.path for route in router.routes if hasattr(route, "path")}
    assert R09 in paths
    operation_ids = {
        getattr(route, "operation_id", None) for route in router.routes
    }
    assert "get_financeiro_billing_mod_breakdown" in operation_ids


def test_missing_service_header_returns_401(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers({}))
    response = r09_client.get(f"{R09}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_service_token_invalid_returns_401(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceTokenInvalidError("bad")),
    )
    response = r09_client.get(f"{R09}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 401


def test_wrong_client_returns_403(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceClientDeniedError("other-api")),
    )
    response = r09_client.get(f"{R09}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_insufficient_scope_returns_403(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(
        monkeypatch,
        _request_headers(S2S_HEADERS),
        _validator(error=ServiceScopeDeniedError("stock-inventory.read")),
    )
    response = r09_client.get(f"{R09}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_flag_off_returns_typed_403(
    r09_client: TestClient, monkeypatch
) -> None:
    """Dataset gate closed: valid S2S + delegated user still gets
    ``scope_unavailable``, never real rows."""
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    from app.application.security.stock_inventory_scope import (
        SharedDatasetStockInventoryScopeResolver,
    )

    monkeypatch.setattr(
        "app.composition.financeiro_billing_mod_breakdown_composer."
        "get_stock_inventory_scope_resolver",
        lambda: SharedDatasetStockInventoryScopeResolver(enabled=False),
    )
    response = r09_client.get(f"{R09}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403
    body = response.json()
    assert body.get("success") is False
    assert body.get("error", {}).get("code") == "scope_unavailable"


def test_service_principal_as_user_does_not_unlock(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch, principal_type="service")
    response = r09_client.get(f"{R09}?{PERIOD}", headers=S2S_HEADERS)
    assert response.status_code == 403


def test_invalid_period_returns_400(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = r09_client.get(f"{R09}?period=bad", headers=S2S_HEADERS)
    assert response.status_code in (400, 422)


def test_invalid_branch_returns_400(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    response = r09_client.get(
        f"{R09}?{PERIOD}&branch=07", headers=S2S_HEADERS
    )
    assert response.status_code in (400, 422)


def test_happy_path_envelope_and_meta(
    r09_client: TestClient, monkeypatch
) -> None:
    _patch_s2s(monkeypatch, _request_headers(S2S_HEADERS), _validator())
    _patch_user(monkeypatch)
    use_case = MagicMock()
    use_case.execute.return_value = {
        "report": "billing-mod-breakdown",
        "reportId": "R09",
        "period": "2026-09",
        "branch": "01",
        "officiality": "operational_view",
        "officialParity": "pending",
        "anchors": [],
        "limitations": [],
        "provenance": {},
    }
    import app.interface.http.routes.financeiro.billing_mod_breakdown_router as mod

    monkeypatch.setattr(
        mod, "build_billing_mod_breakdown_use_case", lambda: use_case
    )
    response = r09_client.get(
        f"{R09}?{PERIOD}&branch=01", headers=S2S_HEADERS
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert (
        body["meta"]["operationId"]
        == "get_financeiro_billing_mod_breakdown"
    )
    assert body["data"]["officiality"] == "operational_view"
    assert body["data"]["officialParity"] == "pending"
    request_arg = use_case.execute.call_args.args[0]
    assert request_arg.period == "2026-09"
    assert request_arg.branch == "01"
    assert use_case.execute.call_args.kwargs["user_subject"] == "user-1"


# -- engine (use case over a fake repository) ---------------------------------


class _FakeRepository:
    """Row-level fake: billed map + SG1 edges + SG2 ops per product."""

    def __init__(self, *, billed=None, edges=None, ops=None):
        self._billed = billed or {}
        self._edges = edges or {}
        self._ops = ops or {}
        self.calls = []

    def fetch_billed_quantities(self, *, period_start, period_end, branch):
        self.calls.append(("billed", branch))
        return [
            {
                "product_code": code,
                "has_billing": 1,
                "billed_qty": qty,
            }
            for code, qty in self._billed.items()
        ]

    def fetch_structure_edges(self, *, parent_codes, branch):
        self.calls.append(("edges", branch, tuple(parent_codes)))
        rows = []
        for parent in parent_codes:
            for component, seq, qty in self._edges.get(parent, []):
                rows.append(
                    {
                        "parent_code": parent,
                        "component_code": component,
                        "component_seq": seq,
                        "quantity_per_unit": qty,
                    }
                )
        return rows

    def fetch_route_operations(self, *, product_codes, branch):
        self.calls.append(("ops", branch, tuple(product_codes)))
        rows = []
        for product in product_codes:
            for op in self._ops.get(product, []):
                rows.append({"product_code": product, **op})
        return rows


def _use_case(repo):
    from app.application.security.stock_inventory_scope import (
        SharedDatasetStockInventoryScopeResolver,
    )
    from app.application.use_cases.financeiro_billing_mod_breakdown.get_billing_mod_breakdown_use_case import (
        GetBillingModBreakdownUseCase,
    )

    return GetBillingModBreakdownUseCase(
        repository=repo,
        scope_resolver=SharedDatasetStockInventoryScopeResolver(
            enabled=True
        ),
    )


def _request(**overrides):
    from app.application.dto.financeiro_billing_mod_breakdown.billing_mod_breakdown_request import (
        BillingModBreakdownRequest,
    )

    params = {"period": "2026-09", "branch": "01"}
    params.update(overrides)
    return BillingModBreakdownRequest.from_query(**params)


def _op(**overrides):
    op = {
        "operation": "01",
        "operation_description": "CORTE",
        "resource": "CT-33A",
        "std_time": 14.22,
        "mod_item": "MOD393",
        "mod_description": "MAQUINA DE CORTE WL603",
        "mod_unit": "HR",
    }
    op.update(overrides)
    return op


def test_scope_unresolved_raises() -> None:
    from app.application.security.stock_inventory_scope import (
        StockInventoryScopeUnavailableError,
        UnresolvedStockInventoryScopeResolver,
    )
    from app.application.use_cases.financeiro_billing_mod_breakdown.get_billing_mod_breakdown_use_case import (
        GetBillingModBreakdownUseCase,
    )

    use_case = GetBillingModBreakdownUseCase(
        repository=_FakeRepository(),
        scope_resolver=UnresolvedStockInventoryScopeResolver(),
    )
    with pytest.raises(StockInventoryScopeUnavailableError):
        use_case.execute(_request(), user_subject="user-1")


def test_anchor_levels_and_formulas() -> None:
    """PA anchor (02) + direct component (04) + subcomponent (06); the
    proven identities hold per line: Quantidade=G2_TEMPAD,
    Horas=propagatedQty×stdTime, propagatedQty fallback to anchor qty."""
    repo = _FakeRepository(
        billed={"PA1": 0.27},
        edges={
            "PA1": [("PI1", "001", 1.0)],
            "PI1": [("PI2", "001", 2.0)],
        },
        ops={
            "PA1": [_op(std_time=14.22)],
            "PI1": [_op(operation="02", std_time=6.58)],
            "PI2": [_op(operation="03", std_time=3.24)],
        },
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    assert data["officiality"] == "operational_view"
    assert data["officialParity"] == "pending"
    anchor = data["anchors"][0]
    assert anchor["product"] == "PA1"
    assert anchor["billedQty"] == 0.27
    levels = [line["level"] for line in anchor["modLines"]]
    assert levels == ["02", "04", "06"]
    for line in anchor["modLines"]:
        qty = line["propagatedQty"]
        std = line["stdTime"]["value"]
        assert line["hours"]["value"] == pytest.approx(qty * std)
        assert line["costUnit"]["state"] == "source_missing"
        assert line["costUnit"]["value"] is None
        assert line["costTotal"]["state"] == "source_missing"
    assert "cost_rate_basis" in anchor["sourceMissing"]


def test_intermediate_own_billed_qty_wins_over_anchor_fallback() -> None:
    """BR-R09-006: when the intermediate is itself billed in the
    competence its own QTDFAT propagates, not the anchor's."""
    repo = _FakeRepository(
        billed={"PA1": 10.0, "PI1": 4.0},
        edges={"PA1": [("PI1", "001", 1.0)]},
        ops={
            "PA1": [_op(std_time=2.0)],
            "PI1": [_op(std_time=5.0)],
        },
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    lines = data["anchors"][0]["modLines"]
    l04 = next(l for l in lines if l["level"] == "04")
    assert l04["propagatedQty"] == 4.0
    assert l04["hours"]["value"] == pytest.approx(20.0)


def test_multiplicity_and_edge_dedup() -> None:
    """Same component under two different parents stays twice (L2
    path multiplicity); the identical edge (parent, comp, trt) is
    deduplicated once — the Estrut/aScan semantics."""
    repo = _FakeRepository(
        billed={"PA1": 8.0},
        edges={
            "PA1": [
                ("PI1", "001", 1.0),
                ("PI2", "002", 1.0),
                ("PI1", "001", 1.0),  # duplicate edge — dedup
            ],
            "PI1": [("X", "001", 1.0)],
            "PI2": [("X", "001", 1.0)],  # same X under other parent
        },
        ops={
            "PA1": [_op(std_time=1.0)],
            "PI1": [_op(std_time=1.0)],
            "PI2": [_op(std_time=1.0)],
            "X": [_op(std_time=1.0)],
        },
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    lines = data["anchors"][0]["modLines"]
    l04 = [l for l in lines if l["level"] == "04"]
    l06 = [l for l in lines if l["level"] == "06"]
    assert len(l04) == 2  # PI1 + PI2, duplicate edge removed
    assert len(l06) == 2  # X via PI1 and X via PI2 — paths preserved


def test_invalid_or_zero_qty_edges_are_skipped() -> None:
    """Estrut only emits edges with ExplEstr > 0 and never a
    self-referencing component (cycle guard)."""
    repo = _FakeRepository(
        billed={"PA1": 5.0},
        edges={
            "PA1": [
                ("PI1", "001", 0.0),    # qty 0 — ExplEstr skip
                ("PA1", "002", 1.0),    # self component — skip
                ("PI2", "003", 1.0),
            ],
        },
        ops={"PA1": [_op()], "PI2": [_op()]},
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    exploded = {l["explodedProduct"] for l in data["anchors"][0]["modLines"]}
    assert exploded == {"PA1", "PI2"}


def test_unmapped_mod_goes_to_diagnostics_not_lines() -> None:
    """Artifact grain is MOD lines only — an operation whose resource
    does not bridge to a MOD* item stays visible in diagnostics and
    never appears as an invented line."""
    repo = _FakeRepository(
        billed={"PA1": 3.0},
        ops={
            "PA1": [
                _op(mod_item=None, mod_description=None, mod_unit=None),
                _op(operation="02"),
            ],
        },
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    lines = data["anchors"][0]["modLines"]
    assert len(lines) == 1
    assert lines[0]["modItem"] == "MOD393"
    assert lines[0]["modItemState"] == "mapped"
    diag = data["anchors"][0]["diagnostics"]["unmappedResourceMod"]
    assert diag == [
        {
            "product": "PA1",
            "operation": "01",
            "resource": "CT-33A",
            "stdTime": 14.22,
        }
    ]
    assert "resource_mod_bridge_unmapped" in data["anchors"][0][
        "sourceMissing"
    ]


def test_product_without_route_ops_is_diagnosed_not_invented() -> None:
    repo = _FakeRepository(
        billed={"PA1": 2.0},
        edges={"PA1": [("PI1", "001", 1.0)]},
        ops={"PA1": [_op()]},  # PI1 has no SG2 ops
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    anchor = data["anchors"][0]
    assert {l["level"] for l in anchor["modLines"]} == {"02"}
    assert anchor["diagnostics"]["productsWithoutRouteOperations"] == [
        "PI1"
    ]
    assert "route_operations_missing" in anchor["sourceMissing"]


def test_missing_std_time_yields_typed_absence_not_zero() -> None:
    """SOURCE_MISSING != ZERO: hours stay absent when stdTime is
    missing, never computed over an invented quantity."""
    repo = _FakeRepository(
        billed={"PA1": 7.0},
        ops={"PA1": [_op(std_time=None)]},
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    line = data["anchors"][0]["modLines"][0]
    assert line["stdTime"]["value"] is None
    assert line["stdTime"]["state"] == "sg2_cadastral"
    assert line["hours"]["value"] is None
    assert line["hours"]["state"] == "source_missing"


def test_zero_billed_qty_is_legitimate_value() -> None:
    """A product with only tipo-'D' billing lines is an anchor with
    billedQty 0 — legitimate zero, distinct from missing."""
    repo = _FakeRepository(
        billed={"PA1": 0.0},
        ops={"PA1": [_op(std_time=2.0)]},
    )
    data = _use_case(repo).execute(_request(), user_subject="u")
    anchor = data["anchors"][0]
    assert anchor["billedQty"] == 0.0
    assert anchor["modLines"][0]["propagatedQty"] == 0.0
    assert anchor["modLines"][0]["hours"]["value"] == 0.0


def test_branch_all_expands_both_branches() -> None:
    repo = _FakeRepository(
        billed={"PA1": 1.0},
        ops={"PA1": [_op()]},
    )
    data = _use_case(repo).execute(_request(branch="all"), user_subject="u")
    assert {a["branch"] for a in data["anchors"]} == {"01", "02"}


def test_request_validates_period_and_branch() -> None:
    from app.application.dto.financeiro_billing_mod_breakdown.billing_mod_breakdown_request import (
        BillingModBreakdownRequest,
    )

    req = BillingModBreakdownRequest.from_query(
        period="2026-09", branch="02"
    )
    assert req.period_start() == "20260901"
    assert req.period_end() == "20260930"
    assert req.requested_branches() == ("02",)
    with pytest.raises(ValueError):
        BillingModBreakdownRequest.from_query(period="2026-13")
    with pytest.raises(ValueError):
        BillingModBreakdownRequest.from_query(
            period="2026-09", branch="99"
        )


# -- SQL builder ---------------------------------------------------------------


def test_billed_sql_uses_emissao_axis_tes_and_tipo_rules() -> None:
    from app.infrastructure.persistence.totvs.financeiro_billing_mod_breakdown.billing_mod_breakdown_sql import (
        billed_quantities_sql,
    )

    sql, _ = billed_quantities_sql(branch="01")
    assert "D2_EMISSAO BETWEEN ? AND ?" in sql
    assert "F4_DUPLIC = 'S'" in sql
    assert "D2_TIPO) <> 'D'" in sql
    assert "SD2010" in sql
    assert "SF4010" in sql


def test_edges_sql_is_parameterized_and_branch_scoped() -> None:
    from app.infrastructure.persistence.totvs.financeiro_billing_mod_breakdown.billing_mod_breakdown_sql import (
        structure_edges_sql,
    )

    sql, params = structure_edges_sql(
        parent_codes=["PA1", "PA2"], branch="01"
    )
    assert "SG1010" in sql
    assert "G1_FILIAL = ?" in sql
    assert "PA1" not in sql and "PA2" not in sql
    assert params[0] == "01"
    assert params[1:] == ["PA1", "PA2"]
    with pytest.raises(ValueError):
        structure_edges_sql(parent_codes=[], branch="01")


def test_ops_sql_ranks_sg2_and_bridges_mod() -> None:
    from app.infrastructure.persistence.totvs.financeiro_billing_mod_breakdown.billing_mod_breakdown_sql import (
        route_operations_sql,
    )

    sql, params = route_operations_sql(
        product_codes=["PA1"], branch="02"
    )
    assert "SG2010" in sql
    assert "ROW_NUMBER() OVER" in sql
    assert "SH1010" in sql
    assert "H1_CCUSTO" in sql
    assert "'MOD' + NULLIF(RTRIM(SH1.ccusto)" in sql
    assert "PA1" not in sql  # every value is a bound parameter
    assert params == ["02", "02", "01", "PA1", "02", "02"]
