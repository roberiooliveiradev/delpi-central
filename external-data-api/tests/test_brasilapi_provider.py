"""BrasilAPI provider adapter — transport, error mapping, factory."""

from __future__ import annotations

import pytest

from app.application.contracts import (
    InvalidResponseError,
    InvalidTaxIdError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitedError,
    TaxIdNotFoundError,
)
from app.infrastructure.providers.brasilapi_cnpj_provider import (
    BrasilApiCnpjProvider,
    UnavailableCnpjProvider,
    build_cnpj_provider,
)
from tests.conftest import BRASILAPI_PAYLOAD, fake_transport

TAX_ID = "19131243000197"


def _provider(**kwargs):
    return BrasilApiCnpjProvider(base_url="https://example.test/api", **kwargs)


def test_200_returns_normalized_dto():
    provider = _provider(transport=fake_transport(200, BRASILAPI_PAYLOAD))
    dto = provider.fetch(TAX_ID, correlation_id="c1")
    assert dto["tax_id"] == TAX_ID
    assert dto["legal_name"] == "OPEN KNOWLEDGE BRASIL"
    assert dto["source"]["provider_id"] == "brasilapi-cnpj-v1"
    assert dto["source"]["correlation_id"] == "c1"


def test_400_invalid_tax_id():
    provider = _provider(transport=fake_transport(400, {"message": "bad"}))
    with pytest.raises(InvalidTaxIdError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_404_not_found():
    provider = _provider(transport=fake_transport(404, {"message": "nf"}))
    with pytest.raises(TaxIdNotFoundError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_403_unavailable():
    provider = _provider(transport=fake_transport(403, {}))
    with pytest.raises(ProviderUnavailableError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_429_rate_limited_with_retry_after():
    provider = _provider(
        transport=fake_transport(429, {}, {"Retry-After": "42"})
    )
    with pytest.raises(RateLimitedError) as exc_info:
        provider.fetch(TAX_ID, correlation_id="c")
    assert exc_info.value.retry_after == 42


@pytest.mark.parametrize("status", [500, 502, 503])
def test_5xx_unavailable(status):
    provider = _provider(transport=fake_transport(status, {}))
    with pytest.raises(ProviderUnavailableError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_unexpected_status_invalid_response():
    provider = _provider(transport=fake_transport(418, {}))
    with pytest.raises(InvalidResponseError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_non_json_payload_invalid_response():
    provider = _provider(
        transport=fake_transport(200, ValueError("no json"))
    )
    with pytest.raises(InvalidResponseError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_transport_error_unavailable():
    def boom(url, *, timeout):
        raise ConnectionError("down")

    provider = _provider(transport=boom)
    with pytest.raises(ProviderUnavailableError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_timeout_maps_504():
    import requests

    def slow(url, *, timeout):
        raise requests.Timeout("timed out")

    provider = _provider(transport=slow)
    with pytest.raises(ProviderTimeoutError):
        provider.fetch(TAX_ID, correlation_id="c")


def test_url_composition():
    calls = []

    def transport(url, *, timeout):
        calls.append(url)
        return fake_transport(200, BRASILAPI_PAYLOAD)(url, timeout=timeout)

    provider = _provider(transport=transport)
    provider.fetch(TAX_ID, correlation_id="c")
    assert calls == [f"https://example.test/api/cnpj/v1/{TAX_ID}"]


def test_unavailable_provider_fails_closed():
    provider = UnavailableCnpjProvider()
    with pytest.raises(ProviderUnavailableError):
        provider.fetch(TAX_ID, correlation_id="c")


# --- factory ---------------------------------------------------------------

def test_factory_defaults_unavailable(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "unavailable")
    assert isinstance(build_cnpj_provider(), UnavailableCnpjProvider)


def test_factory_selects_brasilapi(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "brasilapi")
    assert isinstance(build_cnpj_provider(), BrasilApiCnpjProvider)


def test_factory_unknown_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings

    monkeypatch.setattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "serpro")
    assert isinstance(build_cnpj_provider(), UnavailableCnpjProvider)
