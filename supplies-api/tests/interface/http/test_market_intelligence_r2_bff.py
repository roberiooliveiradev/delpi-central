"""HTTP BFF — market intelligence R2 sources (PROC-0076 R2).

Comex imports, IBGE producer prices and the dedicated PTAX FX route:
catalog-driven resolution (default-deny), weighted unit-value math in
Decimal, dimension filters, freshness and typed upstream failures.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
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


def _catalog() -> dict:
    return {
        "instruments": [],
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
        "import_ncms": [
            {
                "ncm_code": "74040010",
                "kind": "comex_import",
                "description": "Copper waste and scrap",
                "family_code": "copper",
                "ncm_version": "NCM2022",
                "unit": "USD/metric ton",
                "granularity": "month",
                "source_id": "mdic-comex-stat",
                "active": True,
                "display_allowed": True,
                "latest_observation_date": "2026-09-01",
            }
        ],
        "producer_price_series": [
            {
                "series_id": "ipp-metalurgia-index",
                "kind": "producer_price",
                "label": "Metalurgia — IPP número-índice",
                "activity_code": "46641",
                "activity_label": "Metalurgia",
                "variable_code": "10008",
                "variable_label": "IPP número-índice",
                "table_code": "6903",
                "metric_kind": "index",
                "unit": "index",
                "base_reference": "dez/2018=100",
                "granularity": "month",
                "source_id": "ibge-ipp-sidra",
                "active": True,
                "display_allowed": True,
                "latest_observation_date": "2026-09-01",
            },
            {
                "series_id": "ipp-metalurgia-mom",
                "kind": "producer_price",
                "label": "Metalurgia — IPP variação M/M-1",
                "activity_code": "46641",
                "activity_label": "Metalurgia",
                "variable_code": "1396",
                "variable_label": "IPP variação mensal",
                "table_code": "6903",
                "metric_kind": "monthly_variation",
                "unit": "%",
                "base_reference": "dez/2018=100",
                "granularity": "month",
                "source_id": "ibge-ipp-sidra",
                "active": True,
                "display_allowed": True,
                "latest_observation_date": "2026-09-01",
            },
        ],
        "sources": [],
        "meta": {"schema_version": "v1"},
    }


def _gateway() -> MagicMock:
    gateway = MagicMock()
    gateway.catalog.return_value = _catalog()
    gateway.ingestion_status.return_value = {"feeds": []}
    gateway.comex_imports.return_value = [
        {
            "ncm_code": "74040010",
            "reference_month": "2026-08-01",
            "dimensions": {"country_code": "160", "state_code": "SC"},
            "fob_usd_total": "1000.00",
            "net_weight_kg_total": "500.000",
            "unit_value_usd_per_t": "2000.000000",
            "contributing_rows": 3,
            "quality": "validated",
            "source": {"source_id": "mdic-comex-stat"},
        },
        {
            "ncm_code": "74040010",
            "reference_month": "2026-08-01",
            "dimensions": {"country_code": "249", "state_code": "MG"},
            "fob_usd_total": "3000.00",
            "net_weight_kg_total": "1500.000",
            "unit_value_usd_per_t": "2000.000000",
            "contributing_rows": 2,
            "quality": "validated",
            "source": {"source_id": "mdic-comex-stat"},
        },
        {
            "ncm_code": "74040010",
            "reference_month": "2026-09-01",
            "dimensions": {"country_code": "160", "state_code": "SC"},
            "fob_usd_total": "2100.00",
            "net_weight_kg_total": "1000.000",
            "unit_value_usd_per_t": "2100.000000",
            "contributing_rows": 4,
            "quality": "validated",
            "source": {"source_id": "mdic-comex-stat"},
        },
    ]
    gateway.producer_price_observations.return_value = [
        {
            "series_id": "ipp-metalurgia-index",
            "reference_month": "2026-08-01",
            "value": "182.50",
            "quality": "validated",
            "source": {"source_id": "ibge-ipp-sidra"},
        },
        {
            "series_id": "ipp-metalurgia-index",
            "reference_month": "2026-09-01",
            "value": "184.02",
            "quality": "validated",
            "source": {"source_id": "ibge-ipp-sidra"},
        },
    ]
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
    ]
    return gateway


def _client(gateway: MagicMock):
    client = create_app().test_client()
    return client, patch(_GATEWAY, return_value=gateway)


# --- imports/series ----------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_import_series_aggregates_dimensions(mock_resolve, mock_validate):
    """Sibling countries/states in one month sum into a single monthly
    point; unit value comes from aggregate totals (fob×1000/weight)."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/imports/series"
            "?ncm=74040010&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["series"]["metric_kind"] == "import_fob_unit_value"
    points = {p["period"]: p for p in payload["points"]}
    aug = points["2026-08"]
    # 1000+3000 USD over 500+1500 kg → 2000 USD/t.
    assert aug["fob_usd_total"] == "4000.0"
    assert aug["net_weight_kg_total"] == "2000.0"
    assert aug["unit_value_usd_per_t"] == "2000.0"
    assert aug["contributing_rows"] == 5
    assert points["2026-09"]["unit_value_usd_per_t"] == "2100.0"
    assert payload["meta"]["method_version"]["unit_value"].startswith(
        "sum_fob_usd"
    )


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_import_series_dimension_filters_forwarded(
    mock_resolve, mock_validate
):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/imports/series"
            "?ncm=74040010&date_from=2026-08-01&date_to=2026-09-30"
            "&country_code=160&state_code=SC",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    _, kwargs = gateway.comex_imports.call_args
    assert kwargs["country_code"] == "160"
    assert kwargs["state_code"] == "SC"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_import_series_unknown_ncm_404(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/imports/series"
            "?ncm=00000000&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404
    assert response.get_json()["code"] == "not_found"
    gateway.comex_imports.assert_not_called()


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_import_series_invalid_granularity_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/imports/series"
            "?ncm=74040010&date_from=2026-08-01&date_to=2026-09-30"
            "&granularity=day",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


# --- producer-prices/series ----------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_ipp_series_semantics_preserved(mock_resolve, mock_validate):
    """The index passes through as an index — never coerced to a
    monetary unit or metal quote."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/producer-prices/series"
            "?series_id=ipp-metalurgia-index"
            "&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    series = payload["series"]
    assert series["metric_kind"] == "index"
    assert series["table_code"] == "6903"
    assert series["activity_code"] == "46641"
    assert series["base_reference"] == "dez/2018=100"
    points = {p["period"]: p for p in payload["points"]}
    assert points["2026-09"]["value"] == "184.02"
    assert payload["meta"]["source_id"] == "ibge-ipp-sidra"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_ipp_series_unknown_series_404(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/producer-prices/series"
            "?series_id=nope&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 404


# --- fx/series -----------------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_fx_series_buy_sell_distinct(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/fx/series"
            "?fx_kind=ptax_closing_sell"
            "&date_from=2026-10-01&date_to=2026-10-31"
            "&granularity=day",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["series"]["rate_kind"] == "ptax_closing_sell"
    assert payload["series"]["unit"] == "BRL per USD"
    assert len(payload["points"]) == 2
    assert payload["points"][0]["value"] == "5.4"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_fx_series_invalid_kind_422(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/fx/series"
            "?fx_kind=opening"
            "&date_from=2026-10-01&date_to=2026-10-31",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 422


# --- filters + negatives ---------------------------------------------------------


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_include_r2_sections(mock_resolve, mock_validate):
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
    payload = response.get_json()
    assert payload["import_ncms"][0]["ncm_code"] == "74040010"
    assert payload["import_ncms"][0]["selectable"] is True
    assert len(payload["producer_price_series"]) == 2
    assert (
        payload["producer_price_series"][0]["series_id"]
        == "ipp-metalurgia-index"
    )


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_filters_default_deny_r2(mock_resolve, mock_validate):
    """display_allowed absent/False → not selectable (same posture as
    the legacy instruments)."""
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    catalog = _catalog()
    catalog["import_ncms"][0].pop("display_allowed")
    catalog["producer_price_series"][0]["display_allowed"] = False
    gateway = _gateway()
    gateway.catalog.return_value = catalog
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/filters",
            headers={"Authorization": "Bearer tok"},
        )
    payload = response.get_json()
    assert payload["import_ncms"][0]["selectable"] is False
    assert payload["producer_price_series"][0]["selectable"] is False


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_unavailable_503(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    gateway.comex_imports.side_effect = MarketDataGatewayError(
        "upstream down", status_code=503, code="upstream_unavailable"
    )
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/imports/series"
            "?ncm=74040010&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 503
    assert response.get_json()["code"] == "external_data_unavailable"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_upstream_contract_not_ready_503(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user()
    gateway = _gateway()
    gateway.comex_imports.side_effect = MarketDataGatewayError(
        "contract not ready",
        status_code=503,
        code="EXTERNAL_DATA_CONTRACT_NOT_READY",
    )
    client, ctx = _client(gateway)
    with ctx:
        response = client.get(
            "/market-intelligence/imports/series"
            "?ncm=74040010&date_from=2026-08-01&date_to=2026-09-30",
            headers={"Authorization": "Bearer tok"},
        )
    assert response.status_code == 503
    assert response.get_json()["code"] == "contract_not_ready"


@patch(_JWT)
@patch(_AUTH_MIDDLEWARE)
def test_new_routes_require_access(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="viewer@delpi.com.br",
        name="Viewer",
        permissions={"supplies.manage"},
        is_superadmin=False,
        keycloak_sub="x",
        access_token="token",
    )
    client = create_app().test_client()
    for path in (
        "/market-intelligence/imports/series",
        "/market-intelligence/producer-prices/series",
        "/market-intelligence/fx/series",
    ):
        response = client.get(
            path, headers={"Authorization": "Bearer tok"}
        )
        assert response.status_code == 403, path
