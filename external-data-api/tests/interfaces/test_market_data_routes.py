"""HTTP contract for /v1/market-data/* (PROC-0076).

Same security posture as the frozen CNPJ route: missing/invalid/denied
S2S must fail closed before any handler logic runs. Use-case internals
are covered in test_market_data_queries.py; here we stub the names
bound inside the routes module.
"""

from __future__ import annotations

import pytest

from app.application.contracts import (
    InvalidQueryError,
    StorageUnavailableError,
    UnknownInstrumentError,
    UnknownSeriesError,
)
from app.interfaces.http.routes import market_data_routes as routes
from tests.conftest import FakeValidator


S2S = {"X-Delpi-Service-Authorization": "Bearer test-service-token"}


@pytest.fixture(autouse=True)
def _stub_queries(monkeypatch):
    monkeypatch.setattr(
        routes, "get_catalog", lambda: {"instruments": [], "meta": {}}
    )
    monkeypatch.setattr(
        routes,
        "list_metal_observations",
        lambda **kw: {"items": [], "page_info": {}, "meta": {}},
    )
    monkeypatch.setattr(
        routes,
        "list_fx_observations",
        lambda **kw: {"items": [], "page_info": {}, "meta": {}},
    )
    monkeypatch.setattr(
        routes, "get_ingestion_status", lambda: {"feeds": [], "meta": {}}
    )
    monkeypatch.setattr(
        routes,
        "list_comex_imports",
        lambda **kw: {"items": [], "page_info": {}, "meta": {}},
    )
    monkeypatch.setattr(
        routes,
        "list_producer_price_observations",
        lambda **kw: {"items": [], "page_info": {}, "meta": {}},
    )


def test_catalog_requires_s2s(client):
    response = client.get("/v1/market-data/catalog")
    assert response.status_code == 401


def test_catalog_denied_client(client, monkeypatch):
    from app.infrastructure import s2s_auth

    monkeypatch.setattr(
        s2s_auth, "_shared_validator", FakeValidator("denied")
    )
    response = client.get("/v1/market-data/catalog", headers=S2S)
    assert response.status_code == 403


def test_catalog_invalid_token(client, monkeypatch):
    from app.infrastructure import s2s_auth

    monkeypatch.setattr(
        s2s_auth, "_shared_validator", FakeValidator("invalid")
    )
    response = client.get("/v1/market-data/catalog", headers=S2S)
    assert response.status_code == 401


def test_validator_unavailable_fails_closed(client, monkeypatch):
    from app.infrastructure import s2s_auth

    monkeypatch.setattr(
        s2s_auth, "_shared_validator", FakeValidator("unavailable")
    )
    response = client.get("/v1/market-data/catalog", headers=S2S)
    assert response.status_code == 503


def test_catalog_ok(client, s2s_ok):
    response = client.get("/v1/market-data/catalog", headers=S2S)
    assert response.status_code == 200
    assert "X-Correlation-Id" in response.headers


def test_catalog_ok_sibling_route(client, s2s_ok):
    response = client.get("/v1/market-data/ingestion-status", headers=S2S)
    assert response.status_code == 200


def test_metals_observations_ok(client, s2s_ok):
    response = client.get(
        "/v1/market-data/metals/observations"
        "?instrument_code=copper&date_from=2026-01-01&date_to=2026-12-31",
        headers=S2S,
    )
    assert response.status_code == 200


def test_fx_observations_ok(client, s2s_ok):
    response = client.get(
        "/v1/market-data/fx/observations"
        "?pair=USD/BRL&rate_kind=ptax_closing_sell"
        "&date_from=2026-10-01&date_to=2026-10-31",
        headers=S2S,
    )
    assert response.status_code == 200


def test_comex_imports_ok(client, s2s_ok):
    response = client.get(
        "/v1/market-data/comex/imports"
        "?ncm_code=12345678&date_from=2026-01-01&date_to=2026-12-31",
        headers=S2S,
    )
    assert response.status_code == 200


def test_comex_imports_requires_s2s(client):
    response = client.get(
        "/v1/market-data/comex/imports"
        "?ncm_code=12345678&date_from=2026-01-01&date_to=2026-12-31"
    )
    assert response.status_code == 401


def test_producer_prices_ok(client, s2s_ok):
    response = client.get(
        "/v1/market-data/producer-prices/observations"
        "?series_id=ipp-metalurgia-index"
        "&date_from=2026-01-01&date_to=2026-12-31",
        headers=S2S,
    )
    assert response.status_code == 200


def test_unapproved_ncm_maps_404(client, s2s_ok, monkeypatch):
    def _raise(**kw):
        raise UnknownSeriesError("ncm not approved")

    monkeypatch.setattr(routes, "list_comex_imports", _raise)
    response = client.get(
        "/v1/market-data/comex/imports"
        "?ncm_code=87654321&date_from=2026-01-01&date_to=2026-12-31",
        headers=S2S,
    )
    assert response.status_code == 404
    assert response.get_json()["code"] == "EXTERNAL_DATA_UNKNOWN_SERIES"


def test_unknown_ipp_series_maps_404(client, s2s_ok, monkeypatch):
    def _raise(**kw):
        raise UnknownSeriesError("unknown series")

    monkeypatch.setattr(
        routes, "list_producer_price_observations", _raise
    )
    response = client.get(
        "/v1/market-data/producer-prices/observations"
        "?series_id=nope&date_from=2026-01-01&date_to=2026-12-31",
        headers=S2S,
    )
    assert response.status_code == 404
    assert response.get_json()["code"] == "EXTERNAL_DATA_UNKNOWN_SERIES"


def test_invalid_query_maps_400(client, s2s_ok, monkeypatch):
    def _raise(**kw):
        raise InvalidQueryError("bad range")

    monkeypatch.setattr(routes, "list_metal_observations", _raise)
    response = client.get(
        "/v1/market-data/metals/observations"
        "?instrument_code=copper&date_from=x&date_to=y",
        headers=S2S,
    )
    assert response.status_code == 400
    assert response.get_json()["code"] == "EXTERNAL_DATA_INVALID_QUERY"


def test_unknown_instrument_maps_404(client, s2s_ok, monkeypatch):
    def _raise(**kw):
        raise UnknownInstrumentError("nope")

    monkeypatch.setattr(routes, "list_metal_observations", _raise)
    response = client.get(
        "/v1/market-data/metals/observations"
        "?instrument_code=zz&date_from=2026-01-01&date_to=2026-01-31",
        headers=S2S,
    )
    assert response.status_code == 404
    assert response.get_json()["code"] == "EXTERNAL_DATA_UNKNOWN_INSTRUMENT"


def test_storage_unavailable_maps_503(client, s2s_ok, monkeypatch):
    def _raise():
        raise StorageUnavailableError("no db")

    monkeypatch.setattr(routes, "get_catalog", _raise)
    response = client.get("/v1/market-data/catalog", headers=S2S)
    assert response.status_code == 503
    assert response.get_json()["code"] == "EXTERNAL_DATA_STORAGE_UNAVAILABLE"
