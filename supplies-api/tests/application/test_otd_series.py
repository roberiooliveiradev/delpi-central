from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.otd_series_service import OtdSeriesService
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


def test_otd_series_positive_single_branch():
    reads = MagicMock()
    reads.get_purchase_order_otd_series.return_value = {
        "granularity": "month",
        "points": [
            {
                "periodo": "2026-08",
                "sort_key": "2026-08",
                "otd_filial_01": 90.0,
                "otd_filial_02": 80.0,
            },
            {
                "periodo": "2026-09",
                "sort_key": "2026-09",
                "otd_filial_01": 95.0,
                "otd_filial_02": 85.0,
            },
        ],
    }
    result = OtdSeriesService(delpi_reads=reads).compose(
        _user(permissions={"supplies.analytics.access", "supplies.unit.filial-01"}),
        branch="01",
        start_date="2026-08-01",
        end_date="2026-09-30",
    )
    assert result["scope"]["mode"] == "single"
    assert result["scope"]["branches"] == ["01"]
    assert result["granularity"] == "month"
    assert len(result["points"]) == 2
    assert result["points"][0]["period"] == "2026-08"
    assert result["points"][0]["otdPct"] == 90.0
    assert result["points"][1]["otdPct"] == 95.0
    assert result["partialFailures"] == []


def test_otd_series_sibling_consolidated_averages_filials():
    reads = MagicMock()
    reads.get_purchase_order_otd_series.return_value = {
        "points": [
            {
                "periodo": "2026-09",
                "otd_filial_01": 90.0,
                "otd_filial_02": 80.0,
            }
        ]
    }
    result = OtdSeriesService(delpi_reads=reads).compose(
        _user(
            permissions={
                "supplies.analytics.access",
                "supplies.unit.filial-01",
                "supplies.unit.filial-02",
            }
        ),
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-30",
    )
    assert result["scope"]["mode"] == "consolidated"
    assert result["points"][0]["otdPct"] == 85.0


def test_otd_series_unit_cross_forbidden():
    try:
        OtdSeriesService(delpi_reads=MagicMock()).compose(
            _user(permissions={"supplies.analytics.access", "supplies.unit.filial-01"}),
            branch="02",
        )
        assert False, "expected AuthorizationError"
    except Exception as exc:
        assert exc.__class__.__name__ == "AuthorizationError"


def test_otd_series_partial_when_delpi_down():
    reads = MagicMock()
    reads.get_purchase_order_otd_series.side_effect = DelpiApiGatewayError("timeout")
    result = OtdSeriesService(delpi_reads=reads).compose(
        _user(permissions={"supplies.analytics.access", "supplies.unit.filial-01"}),
        branch="01",
    )
    assert result["points"] == []
    assert len(result["partialFailures"]) == 1


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_otd_series_forbidden_without_analytics(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.portal.access"})
    client = create_app().test_client()
    response = client.get(
        "/analytics/otd/series",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_otd_series_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={"supplies.analytics.access", "supplies.unit.filial-01"}
    )
    reads = MagicMock()
    reads.get_purchase_order_otd_series.return_value = {
        "points": [{"periodo": "2026-09", "otd_filial_01": 91.0, "otd_filial_02": None}]
    }
    with patch(
        "app.interfaces.http.routes.analytics_routes.OtdSeriesService",
        return_value=OtdSeriesService(delpi_reads=reads),
    ):
        client = create_app().test_client()
        response = client.get(
            "/analytics/otd/series?branch=01&from=2026-09-01&to=2026-09-30",
            headers={"Authorization": "Bearer good-token"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert body["points"][0]["otdPct"] == 91.0
    assert body["scope"]["branches"] == ["01"]
