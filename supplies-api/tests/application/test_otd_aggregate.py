from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.otd_aggregate_service import OtdAggregateService
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


def test_otd_aggregate_positive_single_branch():
    reads = MagicMock()
    reads.get_otd.return_value = {"otd_percentage": 92.5, "on_time_count": 10, "total_count": 12}
    si = MagicMock()
    si.goals_by_kpi.return_value = {"KPI-OTD": 98.0}

    result = OtdAggregateService(delpi_reads=reads, strategic_indicators=si).compose(
        _user(permissions={"supplies.analytics.access", "supplies.unit.filial-01"}),
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-30",
    )
    assert result["scope"]["mode"] == "single"
    assert result["otdPct"] == 92.5
    assert result["goal"] == 98.0
    assert result["byBranch"]["01"]["otdPct"] == 92.5
    assert result["partialFailures"] == []


def test_otd_aggregate_sibling_consolidated_averages():
    reads = MagicMock()
    reads.get_otd.side_effect = [
        {"otd_percentage": 90.0},
        {"otd_percentage": 80.0},
    ]
    si = MagicMock()
    si.goals_by_kpi.return_value = {"KPI-OTD": 98.0}

    result = OtdAggregateService(delpi_reads=reads, strategic_indicators=si).compose(
        _user(
            permissions={
                "supplies.analytics.access",
                "supplies.unit.filial-01",
                "supplies.unit.filial-02",
            }
        ),
        branch=None,
    )
    assert result["scope"]["mode"] == "consolidated"
    assert result["otdPct"] == 85.0
    assert set(result["byBranch"].keys()) == {"01", "02"}


def test_otd_aggregate_unit_cross_forbidden():
    try:
        OtdAggregateService(
            delpi_reads=MagicMock(),
            strategic_indicators=MagicMock(),
        ).compose(
            _user(permissions={"supplies.analytics.access", "supplies.unit.filial-01"}),
            branch="02",
        )
        assert False, "expected AuthorizationError"
    except Exception as exc:
        assert exc.__class__.__name__ == "AuthorizationError"


def test_otd_aggregate_partial_when_delpi_down():
    reads = MagicMock()
    reads.get_otd.side_effect = DelpiApiGatewayError("timeout")
    si = MagicMock()
    si.goals_by_kpi.return_value = {"KPI-OTD": 98.0}
    result = OtdAggregateService(delpi_reads=reads, strategic_indicators=si).compose(
        _user(permissions={"supplies.analytics.access", "supplies.unit.filial-01"}),
        branch="01",
    )
    assert result["otdPct"] is None
    assert len(result["partialFailures"]) == 1


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_otd_forbidden_without_analytics(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})
    client = create_app().test_client()
    response = client.get(
        "/analytics/otd",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_otd_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.analytics.access", "supplies.unit.filial-01"}
    )
    reads = MagicMock()
    reads.get_otd.return_value = {"otd_percentage": 91.0}
    si = MagicMock()
    si.goals_by_kpi.return_value = {"KPI-OTD": 98.0}
    with patch(
        "app.interfaces.http.routes.analytics_routes.OtdAggregateService",
        return_value=OtdAggregateService(delpi_reads=reads, strategic_indicators=si),
    ):
        client = create_app().test_client()
        response = client.get(
            "/analytics/otd?branch=01&from=2026-09-01&to=2026-09-30",
            headers={"Authorization": "Bearer good-token"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["otdPct"] == 91.0
    assert body["goal"] == 98.0
