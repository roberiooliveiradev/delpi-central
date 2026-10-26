"""HTTP BFF — market intelligence (PROC-0076).

AuthZ, envelope and downstream error mapping: Core effective
``supplies.access`` gates the routes; upstream S2S negatives are
technical faults and never become a user-facing 403.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.domain.exceptions import CoreApiUnavailableError
from app.infrastructure.gateways.market_data_gateway import (
    MarketDataGatewayError,
)

_AUTH_MIDDLEWARE = (
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
_JWT = "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate"
_GATEWAY = (
    "app.application.services.market_intelligence_service.MarketDataGateway"
)


def _user(*, permissions: set[str]) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions=permissions,
        is_superadmin=False,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="buyer@delpi.com.br",
        name="Buyer",
    )


def _catalog() -> dict:
    return {
        "instruments": [
            {
                "instrument_code": "copper",
                "kind": "metal",
                "metal_code": "copper",
                "label": "Cobre",
                "market": "world_bank_pink_sheet",
                "quote_basis": "monthly_average",
                "currency": "USD",
                "unit_code": "metric_ton",
                "unit": "USD/metric ton",
                "granularity": "month",
                "source_id": "world-bank-pink-sheet",
                "latest_observation_date": "2026-09-01",
                "display_allowed": True,
            }
        ],
        "fx_series": [
            {
                "instrument_code": "usd-brl",
                "kind": "fx",
                "label": "Dólar / Real",
                "pair": "USD/BRL",
                "rate_kinds": ["ptax_closing_sell", "ptax_closing_buy"],
                "currency": "BRL",
                "unit": "BRL per USD",
                "granularity": "day",
                "source_id": "bcb-ptax",
                "latest_observation_date": "2026-10-24",
                "display_allowed": True,
            }
        ],
        "sources": [
            {
                "source_id": "world-bank-pink-sheet",
                "provider_id": "world-bank-pink-sheet",
                "attribution": "World Bank — Pink Sheet",
                "license_reference": "CC BY 4.0",
            }
        ],
        "meta": {"schema_version": "v1"},
    }


def _gateway():
    gateway = MagicMock()
    gateway.catalog.return_value = _catalog()
    gateway.ingestion_status.return_value = {
        "feeds": [
            {"feed": "fx-daily", "last_successful_at": "2026-10-24T20:00:00Z"}
        ]
    }
    gateway.metal_observations.return_value = [
        {
            "instrument_code": "copper",
            "observation_date": "2026-08-01",
            "price": "9000.0",
            "currency": "USD",
            "unit": "USD/metric ton",
            "quote_basis": "monthly_average",
            "quality": "validated",
            "source": {"source_id": "world-bank-pink-sheet"},
        },
        {
            "instrument_code": "copper",
            "observation_date": "2026-09-01",
            "price": "9500.5",
            "currency": "USD",
            "unit": "USD/metric ton",
            "quote_basis": "monthly_average",
            "quality": "validated",
            "source": {"source_id": "world-bank-pink-sheet"},
        },
    ]
    gateway.fx_observations.return_value = [
        {
            "pair": "USD/BRL",
            "rate_kind": "ptax_closing_sell",
            "reference_date": "2026-08-03",
            "value": "5.0",
            "quality": "validated",
            "source": {"source_id": "bcb-ptax"},
        },
        {
            "pair": "USD/BRL",
            "rate_kind": "ptax_closing_sell",
            "reference_date": "2026-09-02",
            "value": "6.0",
            "quality": "validated",
            "source": {"source_id": "bcb-ptax"},
        },
    ]
    return gateway


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_anonymous_401(mock_resolve, mock_validate):
    mock_validate.side_effect = Exception("no token")
    client = create_app().test_client()
    assert client.get("/market-intelligence/filters").status_code == 401


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_forbidden_without_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.manage"})
    client = create_app().test_client()
    response = client.get(
        "/market-intelligence/filters",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code == 403


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_core_unavailable_fail_closed(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.side_effect = CoreApiUnavailableError("Core down")
    client = create_app().test_client()
    response = client.get(
        "/market-intelligence/filters",
        headers={"Authorization": "Bearer tok"},
    )
    assert response.status_code in (401, 403, 503)


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_200(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["instruments"][0]["code"] == "copper"
    assert payload["instruments"][1]["code"] == "usd-brl"
    assert payload["default_fx_kind"] == "ptax_closing_sell"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_summary_200_usd(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/summary?instrument=copper"
            "&currency=USD&date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["last_quote"]["value"] == "9500.5"
    assert payload["last_quote"]["currency"] == "USD"
    assert payload["period_average"]["valid_observations"] == 2
    assert payload["period_variation"]["percent"] is not None
    assert payload["fx_reference"]["value"] == "6.0"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_summary_200_brl_conversion(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/summary?instrument=copper"
            "&currency=BRL&date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    # 9500.5 USD × 6.0 BRL/USD (Sept PTAX monthly avg) = 57003.0
    assert payload["last_quote"]["value"] == "57003.0"
    assert payload["meta"]["method_version"]["fx_conversion"] is not None


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_series_200_monthly(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/series?instrument=copper"
            "&currency=USD&granularity=month"
            "&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    points = payload["points"]
    assert [p["period"] for p in points] == ["2026-08", "2026-09"]
    assert points[0]["value"] == "9000.0"
    # Completeness dimension only — "stale" is reported via
    # meta.freshness.status, never as data_status (R1.1).
    assert payload["meta"]["data_status"] in {
        "ok",
        "partial",
    }


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_series_404_unknown_instrument(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/series?instrument=iridium"
            "&currency=USD&granularity=month"
            "&date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
    assert response.get_json()["code"] == "not_found"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_series_422_bad_granularity(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/series?instrument=copper"
            "&currency=USD&granularity=day"
            "&date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422
    assert response.get_json()["code"] == "unprocessable"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_series_422_fx_in_usd(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/series?instrument=usd-brl"
            "&currency=USD&granularity=day"
            "&date_from=2026-10-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_monthly_averages_200(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/monthly-averages?instrument=copper"
            "&currency=BRL&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    rows = payload["items"]
    assert rows[0]["average"] == "45000.0"  # 9000 × 5.0
    assert rows[0]["fx_rate"] == "5.0"
    assert rows[1]["average"] == "57003.0"  # 9500.5 × 6.0


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_monthly_averages_fx_missing_null_not_zero(
    mock_resolve, mock_validate
):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.fx_observations.return_value = []  # no FX at all
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/monthly-averages?instrument=copper"
            "&currency=BRL&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["items"][0]["average"] is None
    assert payload["items"][0]["coverage"] == "fx_missing"
    assert payload["meta"]["partial_reason"] == "fx_missing_months:2026-08,2026-09"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_no_data_is_empty_not_zero(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.metal_observations.return_value = []
    gateway.fx_observations.return_value = []
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/summary?instrument=copper"
            "&currency=USD&date_from=2025-01-01&date_to=2025-03-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["last_quote"] is None
    assert payload["period_average"]["value"] is None
    assert payload["meta"]["data_status"] == "no_data"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_401_is_technical_503_not_user_403(
    mock_resolve, mock_validate
):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.catalog.side_effect = MarketDataGatewayError(
        "s2s denied", status_code=403, code="forbidden"
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 503
    assert response.get_json()["code"] == "external_data_unavailable"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_429_retry_after(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.catalog.side_effect = MarketDataGatewayError(
        "limited", status_code=429, code="rate_limited", retry_after=30
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "30"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_timeout_504(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.catalog.side_effect = MarketDataGatewayError(
        "slow", status_code=504, code="upstream_timeout"
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 504


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_502(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.catalog.side_effect = MarketDataGatewayError(
        "bad", status_code=502, code="upstream_error"
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 503


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_use_not_approved_is_dedicated_code_not_user_403(
    mock_resolve, mock_validate
):
    """AC-R1.2-09/15: producer license quarantine surfaces as a distinct
    unavailability code — never as a user-facing 403 and never as
    generic upstream failure."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.metal_observations.side_effect = MarketDataGatewayError(
        "use not approved",
        status_code=403,
        code="EXTERNAL_DATA_USE_NOT_APPROVED",
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/summary?instrument=copper"
            "&currency=USD&date_from=2026-01-01&date_to=2026-12-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 503
    payload = response.get_json()
    assert payload["code"] == "source_use_not_approved"
    assert "9500" not in str(payload)  # zero price leakage


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_mark_non_selectable_and_pick_displayable_default(
    mock_resolve, mock_validate
):
    """AC-R1.2-14: an instrument whose source lacks the display grant is
    flagged non-selectable and never chosen as the default."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    catalog = _catalog()
    catalog["instruments"][0]["display_allowed"] = False
    catalog["fx_series"][0]["display_allowed"] = True
    gateway.catalog.return_value = catalog
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    by_code = {i["code"]: i for i in payload["instruments"]}
    assert by_code["copper"]["selectable"] is False
    assert by_code["usd-brl"]["selectable"] is True
    assert payload["default_instrument"] == "usd-brl"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
@pytest.mark.parametrize(
    "display_allowed",
    [pytest.param("ABSENT", id="absent"), None, "yes", 1],
)
def test_filters_default_deny_without_explicit_display_allowed(
    mock_resolve, mock_validate, display_allowed
):
    """AC-R1.3-11/12/13: absent, null or invalid display_allowed is
    never a grant — the instrument is not selectable and never chosen
    as the default."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    catalog = _catalog()
    if display_allowed == "ABSENT":
        catalog["instruments"][0].pop("display_allowed", None)
        catalog["fx_series"][0].pop("display_allowed", None)
    else:
        catalog["instruments"][0]["display_allowed"] = display_allowed
        catalog["fx_series"][0]["display_allowed"] = display_allowed
    gateway.catalog.return_value = catalog
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert all(
        i["selectable"] is False for i in payload["instruments"]
    )
    assert payload["default_instrument"] is None


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_contract_not_ready_maps_to_technical_unavailable(
    mock_resolve, mock_validate
):
    """AC-R1.3-14: producer contract-not-ready is technical
    unavailability — never a user permission 403."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.access"})
    gateway = _gateway()
    gateway.catalog.side_effect = MarketDataGatewayError(
        "contract not ready",
        status_code=503,
        code="EXTERNAL_DATA_CONTRACT_NOT_READY",
    )
    client = create_app().test_client()
    with patch(_GATEWAY, return_value=gateway):
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 503
    assert response.get_json()["code"] == "contract_not_ready"
