"""HTTP contract — S2S auth, error envelope, correlation, rate limit."""

from __future__ import annotations

import pytest

from app.application.contracts import (
    InvalidTaxIdError,
    LimiterUnavailableError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    TaxIdNotFoundError,
)
from app.infrastructure import s2s_auth
from app.infrastructure.config.settings import Settings
from app.infrastructure.providers.brasilapi_cnpj_provider import (
    BrasilApiCnpjProvider,
)
from app.infrastructure.rate_limits import reset_rate_limiter
from tests.conftest import BRASILAPI_PAYLOAD, FakeValidator, fake_transport

TAX_ID = "19131243000197"
URL = f"/v1/cnpj/{TAX_ID}"
S2S_HEADERS = {"X-Delpi-Service-Authorization": "Bearer fake-jwt"}


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "brasilapi")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", True)
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE", 1000)
    reset_rate_limiter()
    yield
    reset_rate_limiter()


def _use_validator(monkeypatch, outcome="ok", client_id="supplies-api"):
    monkeypatch.setattr(
        s2s_auth, "_shared_validator", FakeValidator(outcome, client_id)
    )


def _make_client(app, monkeypatch, transport=None):
    """Build a client whose provider uses the given transport."""
    from app.interfaces.http.routes import cnpj_routes

    provider = BrasilApiCnpjProvider(
        base_url="https://example.test/api",
        transport=transport or fake_transport(200, BRASILAPI_PAYLOAD),
    )
    monkeypatch.setattr(cnpj_routes, "build_cnpj_provider", lambda: provider)
    return app.test_client()


# --- S2S security -----------------------------------------------------------


def test_no_token_401(client):
    resp = client.get(URL)
    assert resp.status_code == 401
    assert resp.get_json()["code"] == "unauthorized"


def test_invalid_token_401(client, monkeypatch):
    _use_validator(monkeypatch, "invalid")
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 401
    assert resp.get_json()["code"] == "unauthorized"


def test_denied_client_403(client, monkeypatch):
    _use_validator(monkeypatch, "denied")
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 403
    assert resp.get_json()["code"] == "forbidden"


def test_validator_unavailable_fails_closed(client, monkeypatch):
    _use_validator(monkeypatch, "unavailable")
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 503


def test_config_missing_fails_closed(client, monkeypatch):
    _use_validator(monkeypatch, "config")
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 503


def test_no_upstream_call_before_authorization(app, monkeypatch):
    calls = []
    _use_validator(monkeypatch, "denied")

    def transport(url, *, timeout):
        calls.append(url)
        return fake_transport(200, BRASILAPI_PAYLOAD)(url, timeout=timeout)

    client = _make_client(app, monkeypatch, transport)
    client.get(URL, headers=S2S_HEADERS)
    assert calls == []


def test_spoofed_identity_headers_ignored(app, monkeypatch):
    _use_validator(monkeypatch, "ok", client_id="supplies-api")
    client = _make_client(app, monkeypatch)
    resp = client.get(
        URL,
        headers={
            **S2S_HEADERS,
            "X-User-Id": "admin",
            "X-Forwarded-User": "root",
            "Authorization": "Bearer user-jwt-irrelevant",
        },
    )
    assert resp.status_code == 200


# --- happy path + contract ---------------------------------------------------


def test_get_cnpj_200_contract(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    client = _make_client(app, monkeypatch)
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["tax_id"] == TAX_ID
    assert body["legal_name"] == "OPEN KNOWLEDGE BRASIL"
    assert body["source"]["provider_id"] == "brasilapi-cnpj-v1"
    assert body["source"]["source_type"] == "THIRD_PARTY_API"
    assert body["source"]["schema_version"] == "v1"
    assert body["contact"] == {
        "area_code": None, "phone": None, "email": None
    }
    assert "qsa" not in str(body).lower()
    assert resp.headers.get("X-Correlation-Id")


def test_correlation_id_propagated(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    client = _make_client(app, monkeypatch)
    resp = client.get(
        URL, headers={**S2S_HEADERS, "X-Correlation-Id": "corr-xyz"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["source"]["correlation_id"] == "corr-xyz"
    assert resp.headers["X-Correlation-Id"] == "corr-xyz"


# --- typed errors ------------------------------------------------------------


def test_invalid_cnpj_400(client, monkeypatch):
    _use_validator(monkeypatch, "ok")
    resp = client.get("/v1/cnpj/12A4", headers=S2S_HEADERS)
    assert resp.status_code == 400
    assert resp.get_json()["code"] == "EXTERNAL_DATA_INVALID_TAX_ID"


def test_alphanumeric_cnpj_400(client, monkeypatch):
    _use_validator(monkeypatch, "ok")
    resp = client.get("/v1/cnpj/1913124300019A", headers=S2S_HEADERS)
    assert resp.status_code == 400


def test_not_found_404(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    from app.interfaces.http.routes import cnpj_routes

    class _NF:
        def fetch(self, tax_id, *, correlation_id):
            raise TaxIdNotFoundError("nf")

    monkeypatch.setattr(cnpj_routes, "build_cnpj_provider", lambda: _NF())
    resp = app.test_client().get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 404
    assert resp.get_json()["code"] == "EXTERNAL_DATA_TAX_ID_NOT_FOUND"


def test_provider_unavailable_503(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    from app.interfaces.http.routes import cnpj_routes

    class _Down:
        def fetch(self, tax_id, *, correlation_id):
            raise ProviderUnavailableError("down")

    monkeypatch.setattr(cnpj_routes, "build_cnpj_provider", lambda: _Down())
    resp = app.test_client().get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 503
    assert resp.get_json()["code"] == "EXTERNAL_DATA_PROVIDER_UNAVAILABLE"


def test_provider_timeout_504(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    from app.interfaces.http.routes import cnpj_routes

    class _Slow:
        def fetch(self, tax_id, *, correlation_id):
            raise ProviderTimeoutError("slow")

    monkeypatch.setattr(cnpj_routes, "build_cnpj_provider", lambda: _Slow())
    resp = app.test_client().get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 504
    assert resp.get_json()["code"] == "EXTERNAL_DATA_PROVIDER_TIMEOUT"


def test_rate_limited_429_with_retry_after(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE", 1)
    reset_rate_limiter()
    client = _make_client(app, monkeypatch)
    assert client.get(URL, headers=S2S_HEADERS).status_code == 200
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 429
    assert resp.get_json()["code"] == "EXTERNAL_DATA_RATE_LIMITED"
    assert resp.headers.get("Retry-After")


def test_limiter_unavailable_503(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "distributed")
    monkeypatch.setattr(Settings, "REDIS_URL", "")
    reset_rate_limiter()
    client = _make_client(app, monkeypatch)
    resp = client.get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 503
    assert resp.get_json()["code"] == "EXTERNAL_DATA_LIMITER_UNAVAILABLE"


def test_provider_disabled_by_default(app, monkeypatch):
    _use_validator(monkeypatch, "ok")
    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "unavailable")
    monkeypatch.setattr(
        Settings, "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", False
    )
    reset_rate_limiter()
    resp = app.test_client().get(URL, headers=S2S_HEADERS)
    assert resp.status_code == 503
    assert resp.get_json()["code"] == "EXTERNAL_DATA_PROVIDER_UNAVAILABLE"


def test_health_200_without_s2s(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
