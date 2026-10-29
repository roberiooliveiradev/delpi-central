"""HTTP BFF — market intelligence R5.S1 daily metal granularity.

MetalCharts-bound instruments are day-native: ``quotes/series`` must
serve ``day`` and ``week`` buckets derived from real daily closes, and
``month`` must be the mean of daily observations — never the last close
of the month. Mixed requests keep an honest per-instrument state: a
monthly-native instrument in a daily query is reported as
``granularity_not_supported`` instead of fabricating points.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser

_AUTH_MIDDLEWARE = (
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
_JWT = "app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate"
_GATEWAY = (
    "app.application.services.market_intelligence_service.MarketDataGateway"
)


def _user() -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="buyer@delpi.com.br",
        name="Buyer",
        permissions={"supplies.access"},
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


def _metal(code, label, *, granularities, unit_code, unit, source_id):
    return {
        "instrument_code": code,
        "kind": "metal",
        "metal_code": code,
        "label": label,
        "market": "metalcharts",
        "quote_basis": "daily_close",
        "currency": "USD",
        "unit_code": unit_code,
        "unit": unit,
        "granularity": granularities[0],
        "supported_granularities": granularities,
        "source_id": source_id,
        "active": True,
        "display_allowed": True,
        "selectable_in_ui": True,
        "data_access_allowed": True,
        "latest_observation_date": "2026-10-27",
    }


def _catalog() -> dict:
    return {
        "instruments": [
            _metal(
                "copper",
                "Cobre",
                granularities=["day", "week", "month", "year"],
                unit_code="usd_per_pound",
                unit="US$/lb",
                source_id="metalcharts",
            ),
            _metal(
                "zinc",
                "Zinco",
                granularities=["day", "week", "month", "year"],
                unit_code="usd_per_metric_ton",
                unit="US$/t",
                source_id="metalcharts",
            ),
            _metal(
                "lead",
                "Chumbo",
                granularities=["day", "week", "month", "year"],
                unit_code="usd_per_metric_ton",
                unit="US$/t",
                source_id="metalcharts",
            ),
            _metal(
                "tin",
                "Estanho",
                granularities=["month", "year"],
                unit_code="metric_ton",
                unit="US$/t",
                source_id="world-bank-pink-sheet",
            ),
        ],
        "fx_series": [],
        "import_ncms": [],
        "producer_price_series": [],
        "sources": [],
        "meta": {"schema_version": "v1"},
    }


def _obs(code, day, price):
    return {
        "instrument_code": code,
        "observation_date": day,
        "price": price,
        "currency": "USD",
        "unit": "US$/t",
        "quote_basis": "daily_close",
        "quality": "validated",
        "source": {"source_id": "metalcharts"},
    }


# 2026-10-19 (Mon, W43) → 2026-10-23 (Fri, W43) and 2026-10-26 (Mon, W44).
_DAILY = {
    "copper": [
        ("2026-10-19", "4.60"),
        ("2026-10-20", "4.70"),
        ("2026-10-26", "4.90"),
    ],
    "zinc": [
        ("2026-10-19", "3000.0"),
        ("2026-10-20", "3100.0"),
        ("2026-10-26", "3300.0"),
    ],
    "lead": [
        ("2026-10-19", "2000.0"),
        ("2026-10-26", "2100.0"),
    ],
    "tin": [
        ("2026-10-01", "35000.0"),
    ],
}


def _gateway() -> MagicMock:
    gateway = MagicMock()
    gateway.catalog.return_value = _catalog()
    gateway.ingestion_status.return_value = {"feeds": []}
    gateway.metal_observations.side_effect = (
        lambda code, start, end: [
            _obs(code, day, price)
            for day, price in _DAILY.get(code, [])
            if start.isoformat() <= day <= end.isoformat()
        ]
    )
    gateway.fx_observations.return_value = []
    return gateway


def _client(gateway: MagicMock):
    client = create_app().test_client()
    return client, patch(_GATEWAY, return_value=gateway)


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_metal_day_granularity_returns_daily_closes(
    mock_resolve, mock_validate
):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=copper&granularity=day"
            "&date_from=2026-10-19&date_to=2026-10-27",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    series = payload["series"][0]
    assert payload["granularity"] == "day"
    assert series["availability"]["data_access_allowed"] is True
    points = {p["period"]: p for p in series["points"]}
    assert points["2026-10-19"]["value"] == "4.6"
    assert points["2026-10-20"]["value"] == "4.7"
    assert points["2026-10-26"]["value"] == "4.9"
    # Non-publication days never become fabricated null buckets.
    assert "2026-10-21" not in points


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_metal_day_series_surfaces_last_quote_basis(
    mock_resolve, mock_validate
):
    """R11 — a /v1/prices same-day refresh lands as a ``*_last`` row and
    stays labelled as such through points and the summary read model;
    historical close rows keep their canonical basis."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()

    def obs(code, start, end):
        rows = [
            _obs(code, day, price)
            for day, price in _DAILY.get(code, [])
            if start.isoformat() <= day <= end.isoformat()
        ]
        if code == "copper" and end.isoformat() >= "2026-10-26":
            rows.append(
                {
                    "instrument_code": code,
                    "observation_date": "2026-10-27",
                    "price": "4.95",
                    "currency": "USD",
                    "unit": "US$/lb",
                    "quote_basis": "comex_futures_last",
                    "observation_timestamp": "2026-10-27T17:30:00+00:00",
                    "quality": "validated",
                    "source": {"source_id": "metalcharts"},
                }
            )
        return rows

    gateway.metal_observations.side_effect = obs
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=copper&granularity=day"
            "&date_from=2026-10-19&date_to=2026-10-27",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    series = response.get_json()["series"][0]
    points = {p["period"]: p for p in series["points"]}
    assert points["2026-10-27"]["quote_basis"] == "comex_futures_last"
    assert (
        points["2026-10-27"]["observation_timestamp"]
        == "2026-10-27T17:30:00+00:00"
    )
    assert points["2026-10-26"]["quote_basis"] == "daily_close"
    latest = series["summary"]["latest"]
    assert latest["quote_basis"] == "comex_futures_last"
    assert latest["observation_timestamp"] == (
        "2026-10-27T17:30:00+00:00"
    )


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_metal_week_granularity_iso_week_mean(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=zinc&granularity=week"
            "&date_from=2026-10-19&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    points = {
        p["period"]: p for p in response.get_json()["series"][0]["points"]
    }
    assert points["2026-W43"]["value"] == "3050.0"
    assert points["2026-W43"]["observation_count"] == 2
    assert points["2026-W44"]["value"] == "3300.0"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_metal_month_is_mean_of_daily_closes(mock_resolve, mock_validate):
    """Monthly value on a daily source is the mean of valid closes —
    the pre-R5 monthly pipeline would have kept only the last close."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=zinc&granularity=month"
            "&date_from=2026-10-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    point = response.get_json()["series"][0]["points"][0]
    assert point["period"] == "2026-10"
    assert point["value"] == "3133.333333"
    assert point["observation_count"] == 3


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_mixed_granularity_marks_unsupported_instrument(
    mock_resolve, mock_validate
):
    """copper (day-native) + tin (month-native) at day granularity:
    copper carries points; tin keeps an honest unavailable state."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=copper,tin&granularity=day"
            "&date_from=2026-10-19&date_to=2026-10-27",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    series = {
        s["instrument"]["code"]: s
        for s in response.get_json()["series"]
    }
    assert len(series["copper"]["points"]) == 3
    tin = series["tin"]
    assert tin["points"] == []
    assert tin["availability"]["data_access_allowed"] is False
    assert (
        tin["availability"]["unavailable_reason"]
        == "granularity_not_supported"
    )


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_day_granularity_422_when_no_instrument_supports(
    mock_resolve, mock_validate
):
    """Daily is never fabricated from monthly-native instruments."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=tin&granularity=day"
            "&date_from=2026-10-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_compare_same_unit_daily_metals(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/compare"
            "?instruments=zinc,lead&granularity=day"
            "&date_from=2026-10-19&date_to=2026-10-27",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["comparison"]["comparable"] is True
    assert payload["comparison"]["unit"] == "US$/t"
    assert "2026-10-19" in payload["periods"]


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_compare_incompatible_units_stays_honest(
    mock_resolve, mock_validate
):
    """USD/lb copper vs USD/t zinc must not be aligned — units differ."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/compare"
            "?instruments=copper,zinc&granularity=day"
            "&date_from=2026-10-19&date_to=2026-10-27",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["comparison"]["comparable"] is False
    assert payload["comparison"]["reason"] == "incompatible_units"
