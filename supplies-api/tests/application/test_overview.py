from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.overview_composition_service import OverviewCompositionService
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="analyst@delpi.com.br",
        name="Analyst",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="analyst@delpi.com.br",
        name="Analyst",
    )


def _stub_reads():
    reads = MagicMock()
    reads.get_otd.return_value = {"otd_percentage": 95.0, "goal_value": 98.0}
    reads.get_stock_value.return_value = {"total_stock_value": 1000.0}
    reads.get_inventory_turnover.return_value = {"inventory_turnover_times": 2.5}
    reads.get_cpv.return_value = {"cpv_percentage": 40.0}
    reads.get_negotiation_savings.return_value = {"total_savings": 500.0}
    reads.get_safety_stock_summary.return_value = {"below_safety_stock": 3}
    return reads


def test_overview_positive_seven_kpis():
    reads = _stub_reads()
    pr = MagicMock()
    pr.count_open_requests.return_value = 12
    si = MagicMock()
    si.metrics_by_kpi.return_value = {
        "KPI-OTD": {"goal": 98.0, "score": 6.57},
    }

    service = OverviewCompositionService(
        delpi_reads=reads,
        purchase_requests=pr,
        strategic_indicators=si,
    )
    result = service.compose(
        _user(
            permissions={
                "supplies.analytics.access",
                "supplies.unit.filial-01",
            }
        ),
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )

    assert result["scope"]["mode"] == "single"
    assert result["scope"]["branches"] == ["01"]
    assert len(result["kpis"]) == 7
    ids = [kpi["id"] for kpi in result["kpis"]]
    assert ids == [
        "KPI-OTD",
        "KPI-STOCK-VALUE",
        "KPI-TURNOVER",
        "KPI-CPV",
        "KPI-SAVINGS",
        "KPI-SC-OPEN",
        "KPI-CRITICAL-MP",
    ]
    assert all(kpi["status"] == "available" for kpi in result["kpis"])
    otd = next(k for k in result["kpis"] if k["id"] == "KPI-OTD")
    assert otd["value"] == 95.0
    assert next(k for k in result["kpis"] if k["id"] == "KPI-SC-OPEN")["value"] == 12.0
    assert otd["meta"] == 98.0
    assert otd["iddScore"] == 6.57
    assert otd["temporalNature"] == "interval"
    assert next(k for k in result["kpis"] if k["id"] == "KPI-CRITICAL-MP")["temporalNature"] == (
        "snapshot"
    )


def test_overview_sibling_consolidated_two_units():
    reads = _stub_reads()
    reads.get_stock_value.side_effect = [
        {"total_stock_value": 100.0},
        {"total_stock_value": 200.0},
    ]
    pr = MagicMock()
    pr.count_open_requests.side_effect = [5, 7]
    si = MagicMock()
    si.metrics_by_kpi.return_value = {}

    result = OverviewCompositionService(
        delpi_reads=reads,
        purchase_requests=pr,
        strategic_indicators=si,
    ).compose(
        _user(
            permissions={
                "supplies.analytics.access",
                "supplies.unit.filial-01",
                "supplies.unit.filial-02",
            }
        ),
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-08",
    )

    assert result["scope"]["mode"] == "consolidated"
    assert result["scope"]["branches"] == ["01", "02"]
    stock = next(k for k in result["kpis"] if k["id"] == "KPI-STOCK-VALUE")
    assert stock["value"] == 300.0
    sc = next(k for k in result["kpis"] if k["id"] == "KPI-SC-OPEN")
    assert sc["value"] == 12.0


def test_overview_unit_cross_forbidden():
    service = OverviewCompositionService(
        delpi_reads=_stub_reads(),
        purchase_requests=MagicMock(),
        strategic_indicators=MagicMock(),
    )
    try:
        service.compose(
            _user(
                permissions={
                    "supplies.analytics.access",
                    "supplies.unit.filial-01",
                }
            ),
            branch="02",
        )
        assert False, "expected AuthorizationError"
    except Exception as exc:
        assert exc.__class__.__name__ == "AuthorizationError"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_overview_forbidden_without_analytics(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})
    client = create_app().test_client()
    response = client.get(
        "/analytics/overview",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_overview_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.analytics.access",
            "supplies.unit.filial-01",
        }
    )

    reads = _stub_reads()
    pr = MagicMock()
    pr.count_open_requests.return_value = 1
    si = MagicMock()
    si.metrics_by_kpi.return_value = {}

    with patch(
        "app.interfaces.http.routes.analytics_routes.OverviewCompositionService",
        return_value=OverviewCompositionService(
            delpi_reads=reads,
            purchase_requests=pr,
            strategic_indicators=si,
        ),
    ):
        client = create_app().test_client()
        response = client.get(
            "/analytics/overview?branch=01&from=2026-09-01&to=2026-09-08",
            headers={"Authorization": "Bearer good-token"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["kpis"]) == 7
    assert "partialFailures" in body
