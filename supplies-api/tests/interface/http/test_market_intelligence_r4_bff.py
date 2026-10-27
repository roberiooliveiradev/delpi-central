"""HTTP BFF — market intelligence R4 quotes contracts (PROC-0076 R4).

Multi-instrument ``quotes/series`` + ``quotes/compare`` for the Metais
perspective, the ``week`` granularity on daily series and the D-04
split between ``selectable_in_ui`` and ``data_access_allowed``.
Quarantined instruments keep catalog identity and availability
metadata but never yield protected values — the producer is not even
called for them.
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


def _metal(code, label, *, display_allowed, latest="2026-09-01"):
    return {
        "instrument_code": code,
        "kind": "metal",
        "metal_code": code,
        "label": label,
        "market": "lme_via_world_bank_pink_sheet",
        "quote_basis": "monthly_average",
        "currency": "USD",
        "unit_code": "metric_ton",
        "unit": "USD/metric ton",
        "granularity": "month",
        "supported_granularities": ["month", "year"],
        "source_id": "world-bank-pink-sheet",
        "active": True,
        "display_allowed": display_allowed,
        "selectable_in_ui": True,
        "data_access_allowed": display_allowed,
        "latest_observation_date": latest if display_allowed else None,
    }


def _catalog() -> dict:
    return {
        "instruments": [
            _metal("copper", "Cobre", display_allowed=True),
            _metal("aluminum", "Alumínio", display_allowed=True),
            _metal("zinc", "Zinco", display_allowed=False, latest=None),
        ],
        "fx_series": [
            {
                "instrument_code": "usd-brl",
                "kind": "fx",
                "label": "Dólar / Real",
                "pair": "USD/BRL",
                "rate_kinds": ["ptax_closing_sell", "ptax_closing_buy"],
                "currency": "BRL",
                "unit": "R$/US$",
                "granularity": "day",
                "supported_granularities": [
                    "day",
                    "week",
                    "month",
                    "year",
                ],
                "source_id": "bcb-ptax",
                "latest_observation_date": "2026-10-26",
                "display_allowed": True,
                "selectable_in_ui": True,
                "data_access_allowed": True,
            }
        ],
        "import_ncms": [],
        "producer_price_series": [],
        "sources": [],
        "meta": {"schema_version": "v1"},
    }


def _obs(code, price):
    return {
        "instrument_code": code,
        "observation_date": "2026-09-01",
        "price": price,
        "currency": "USD",
        "unit": "USD/metric ton",
        "quote_basis": "monthly_average",
        "quality": "validated",
        "source": {"source_id": "world-bank-pink-sheet"},
    }


def _gateway() -> MagicMock:
    gateway = MagicMock()
    gateway.catalog.return_value = _catalog()
    gateway.ingestion_status.return_value = {"feeds": []}
    prices = {"copper": "9500.0", "aluminum": "2400.0"}
    gateway.metal_observations.side_effect = (
        lambda code, start, end: [_obs(code, prices[code])]
        if code in prices
        else []
    )
    gateway.fx_observations.return_value = [
        {
            "pair": "USD/BRL",
            "rate_kind": "ptax_closing_sell",
            "reference_date": "2026-10-23",
            "value": "5.40",
            "quality": "validated",
            "source": {"source_id": "bcb-ptax"},
        },
        {
            "pair": "USD/BRL",
            "rate_kind": "ptax_closing_sell",
            "reference_date": "2026-10-24",
            "value": "5.42",
            "quality": "validated",
            "source": {"source_id": "bcb-ptax"},
        },
        {
            "pair": "USD/BRL",
            "rate_kind": "ptax_closing_sell",
            "reference_date": "2026-10-26",
            "value": "5.44",
            "quality": "validated",
            "source": {"source_id": "bcb-ptax"},
        },
    ]
    return gateway


def _client(gateway: MagicMock):
    client = create_app().test_client()
    return client, patch(_GATEWAY, return_value=gateway)


# --- quotes/series -----------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_authorized_instrument(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=copper&date_from=2026-08-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["series"]) == 1
    entry = payload["series"][0]
    assert entry["instrument"]["code"] == "copper"
    assert entry["availability"]["data_access_allowed"] is True
    assert entry["availability"]["selectable_in_ui"] is True
    sept = {p["period"]: p for p in entry["points"]}["2026-09"]
    assert sept["value"] == "9500.0"
    assert entry["summary"]["latest"]["value"] == "9500.0"
    assert entry["summary"]["observed"] == 1


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_quarantined_never_fetches(mock_resolve, mock_validate):
    """D-04: card exists in the UI, but no producer call and no values
    for a source without ``display_allowed``."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=zinc&date_from=2026-08-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    entry = response.get_json()["series"][0]
    assert entry["instrument"]["code"] == "zinc"
    assert entry["availability"]["selectable_in_ui"] is True
    assert entry["availability"]["data_access_allowed"] is False
    assert (
        entry["availability"]["unavailable_reason"]
        == "source_use_pending"
    )
    assert entry["points"] == []
    assert entry["summary"] is None
    gateway.metal_observations.assert_not_called()


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_mixed_selection(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=copper,zinc&date_from=2026-08-01"
            "&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    entries = {
        s["instrument"]["code"]: s
        for s in response.get_json()["series"]
    }
    assert entries["copper"]["summary"]["observed"] == 1
    assert entries["zinc"]["points"] == []
    # Only the authorized instrument reached the producer.
    calls = {c.args[0] for c in gateway.metal_observations.call_args_list}
    assert calls == {"copper"}


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_unknown_instrument_404(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=unobtanium&date_from=2026-08-01"
            "&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_requires_instruments(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?date_from=2026-08-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_rejects_non_metal(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    catalog = gateway.catalog.return_value
    catalog["fx_series"] = [
        {
            "instrument_code": "usd-brl",
            "kind": "fx",
            "label": "Dólar / Real",
            "display_allowed": True,
        }
    ]
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/series"
            "?instruments=usd-brl&date_from=2026-08-01"
            "&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_series_invalid_granularity_422(mock_resolve, mock_validate):
    """Weekly/daily is never fabricated from a monthly metal series."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        for granularity in ("day", "week"):
            response = client.get(
                "/market-intelligence/quotes/series"
                f"?instruments=copper&granularity={granularity}"
                "&date_from=2026-08-01&date_to=2026-10-31",
                headers={"Authorization": "Bearer tok"},
            )
            assert response.status_code == 422


# --- quotes/compare ----------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_compare_aligned(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/compare"
            "?instruments=copper,aluminum&date_from=2026-08-01"
            "&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["comparison"]["comparable"] is True
    assert payload["comparison"]["unit"] == "USD/metric ton"
    assert payload["comparison"]["method"].startswith("period_outer_join")
    series = {
        s["instrument"]["code"]: s for s in payload["series"]
    }
    idx = payload["periods"].index("2026-09")
    assert series["copper"]["values"][idx] == "9500.0"
    assert series["aluminum"]["values"][idx] == "2400.0"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_quote_compare_insufficient_authorized(mock_resolve, mock_validate):
    """Only one display-allowed series → comparison explained, not run."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/quotes/compare"
            "?instruments=copper,zinc&date_from=2026-08-01"
            "&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["comparison"]["comparable"] is False
    assert (
        payload["comparison"]["reason"]
        == "insufficient_authorized_series"
    )
    series = {
        s["instrument"]["code"]: s for s in payload["series"]
    }
    assert series["zinc"]["values"] is None
    assert series["copper"]["values"] is not None


# --- week granularity (daily series) ------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_fx_week_buckets_iso_weeks(mock_resolve, mock_validate):
    """2026-10-23/24 (W43) and 2026-10-26 (W44) → two weekly points with
    the mean of valid daily bulletins each."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/fx/series"
            "?fx_kind=ptax_closing_sell&granularity=week"
            "&date_from=2026-10-12&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["granularity"] == "week"
    points = {p["period"]: p for p in payload["points"]}
    assert points["2026-W43"]["value"] == "5.41"
    assert points["2026-W43"]["observation_count"] == 2
    assert points["2026-W44"]["value"] == "5.44"
    # The untouched W42 window exists as an honest empty bucket.
    assert points["2026-W42"]["value"] is None
    assert points["2026-W42"]["observation_count"] == 0


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_emit_d04_availability_fields(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    instruments = {
        i["code"]: i for i in response.get_json()["instruments"]
    }
    assert instruments["zinc"]["selectable_in_ui"] is True
    assert instruments["zinc"]["data_access_allowed"] is False
    assert instruments["zinc"]["selectable"] is False
    assert instruments["copper"]["data_access_allowed"] is True
    assert instruments["copper"]["granularities"] == ["month", "year"]
