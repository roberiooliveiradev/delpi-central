"""X2 consumer adapter tests — HTTP/S2S call to the shared external-data-api.

The transport callable is always injected; no real HTTP or BrasilAPI call
ever happens. The fake S2S token provider stands in for
``ClientCredentialsTokenProvider`` so no Keycloak is needed.
"""

from __future__ import annotations

import importlib

import pytest

from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    RegistryLimiterUnavailableError,
    RegistryRateLimitedError,
    RegistryResponseInvalidError,
    RegistryTaxIdInvalidError,
    RegistryTaxIdNotFoundError,
)
from app.infrastructure.gateways.external_data_company_registry_provider import (
    ExternalDataApiCompanyRegistryProvider,
)
from app.infrastructure.gateways import supplier_enrichment_adapters
from app.infrastructure.gateways.brasilapi_registry_provider import (
    BrasilApiCompanyRegistryProvider,
)

TAX_ID = "19131243000197"


def _dto(**overrides):
    """Synthetic DTO v1 exactly as external-data-api X1 returns it."""
    dto = {
        "tax_id": "19.131.243/0001-97",
        "legal_name": "OPEN KNOWLEDGE BRASIL",
        "trade_name": None,
        "address": {
            "street": "ALAMEDA FRANCA, 243",
            "number": "243",
            "complement": "APT 34",
            "district": "SAO PAULO",
            "postal_code": "01422-030",
            "city": "SAO PAULO",
            "state": "SP",
            "ibge_city_code": "3550308",
        },
        "contact": {"area_code": None, "phone": None, "email": None},
        "registration": {
            "status": "ATIVA",
            "main_cnae": "6201-5/00",
            "legal_nature": "206-2",
            "opening_date": "2013-10-03",
        },
        "source": {
            "provider_id": "brasilapi-cnpj-v1",
            "source_type": "THIRD_PARTY_API",
            "retrieved_at": "2026-10-22T12:00:00Z",
            "correlation_id": "corr-123",
            "schema_version": "v1",
        },
    }
    for key, value in overrides.items():
        dto[key] = value
    return dto


class _Resp:
    def __init__(self, status=200, payload=None, headers=None, json_ok=True):
        self.status_code = status
        self._payload = payload
        self.headers = headers or {}
        self._json_ok = json_ok

    def json(self):
        if not self._json_ok:
            raise ValueError("not json")
        return self._payload


class _Provider:
    def get_token(self):
        return "s2s-token-abc"


def _provider(
    *, response=None, raise_exc=None, token_provider=None, calls=None
):
    def transport(url, *, headers, timeout):
        if calls is not None:
            calls.append({"url": url, "headers": dict(headers)})
        if raise_exc is not None:
            raise raise_exc
        return response or _Resp(payload=_dto())

    return ExternalDataApiCompanyRegistryProvider(
        base_url="http://external-data-api:8000",
        timeout_seconds=10,
        transport=transport,
        token_provider=token_provider or _Provider(),
    )


class TestHappyPath:
    def test_snapshot_fields_and_metadata(self):
        snapshot = _provider().fetch(TAX_ID)
        assert snapshot.tax_id == TAX_ID
        assert snapshot.source_id == "brasilapi-cnpj-v1"
        assert snapshot.retrieved_at == "2026-10-22T12:00:00Z"
        assert snapshot.source_reference == "brasilapi-cnpj-v1:cnpj-…0197"
        fields = snapshot.fields
        assert fields["company.tax_id"] == TAX_ID
        assert fields["company.legal_name"] == "OPEN KNOWLEDGE BRASIL"
        assert (
            fields["address.street"] == "ALAMEDA FRANCA, 243 APT 34"
        )  # number already embedded, complement appended
        assert fields["address.postal_code"] == "01422030"
        assert fields["address.ibge_city_code"] == "3550308"
        assert fields["company.registration_status"] == "ATIVA"
        # X1 LGPD restriction: contacts are null by contract.
        assert fields["contact.area_code"] is None
        assert fields["contact.phone"] is None
        assert fields["contact.email"] is None

    def test_sends_s2s_header_and_never_user_jwt(self):
        calls = []
        _provider(calls=calls).fetch(TAX_ID)
        (call,) = calls
        assert call["headers"]["X-Delpi-Service-Authorization"] == (
            "Bearer s2s-token-abc"
        )
        assert "Authorization" not in call["headers"]
        assert call["url"].endswith(f"/v1/cnpj/{TAX_ID}")

    def test_contacts_dropped_even_when_upstream_sends_them(self):
        # Upstream contract violation / future un-authorized payload must
        # still yield null contact fields — minimization is enforced
        # consumer-side, never trusted to the response content.
        dto = _dto()
        dto["contact"] = {
            "area_code": "11",
            "phone": "32223344",
            "email": "contato@acme.example",
        }
        snapshot = _provider(response=_Resp(payload=dto)).fetch(TAX_ID)
        assert snapshot.fields["contact.area_code"] is None
        assert snapshot.fields["contact.phone"] is None
        assert snapshot.fields["contact.email"] is None
        # Every other field is preserved.
        assert snapshot.fields["company.legal_name"] == "OPEN KNOWLEDGE BRASIL"
        assert snapshot.fields["address.street"] == (
            "ALAMEDA FRANCA, 243 APT 34"
        )

    def test_rejects_divergent_tax_id(self):
        response = _Resp(payload=_dto(tax_id="12.345.678/0001-90"))
        with pytest.raises(RegistryResponseInvalidError):
            _provider(response=response).fetch(TAX_ID)

    def test_rejects_invalid_input_tax_id(self):
        with pytest.raises(RegistryTaxIdInvalidError):
            _provider().fetch("123")
        with pytest.raises(RegistryTaxIdInvalidError):
            _provider().fetch("1913124300019A")

    def test_rejects_non_third_party_source(self):
        dto = _dto()
        dto["source"]["source_type"] = "GOVERNMENT_API"
        with pytest.raises(RegistryResponseInvalidError):
            _provider(response=_Resp(payload=dto)).fetch(TAX_ID)

    def test_rejects_missing_source_metadata(self):
        dto = _dto()
        dto.pop("source")
        with pytest.raises(RegistryResponseInvalidError):
            _provider(response=_Resp(payload=dto)).fetch(TAX_ID)

    def test_rejects_non_json_payload(self):
        with pytest.raises(RegistryResponseInvalidError):
            _provider(response=_Resp(json_ok=False)).fetch(TAX_ID)


class TestErrorMapping:
    @pytest.mark.parametrize(
        "status,code,expected",
        [
            (400, "EXTERNAL_DATA_INVALID_TAX_ID", RegistryTaxIdInvalidError),
            (404, "EXTERNAL_DATA_TAX_ID_NOT_FOUND", RegistryTaxIdNotFoundError),
            (
                502,
                "EXTERNAL_DATA_INVALID_RESPONSE",
                RegistryResponseInvalidError,
            ),
            (
                503,
                "EXTERNAL_DATA_PROVIDER_UNAVAILABLE",
                EnrichmentSourceUnavailableError,
            ),
            (
                503,
                "EXTERNAL_DATA_LIMITER_UNAVAILABLE",
                RegistryLimiterUnavailableError,
            ),
            (
                504,
                "EXTERNAL_DATA_PROVIDER_TIMEOUT",
                EnrichmentSourceUnavailableError,
            ),
        ],
    )
    def test_status_mapping(self, status, code, expected):
        response = _Resp(
            status=status, payload={"detail": "x", "code": code}
        )
        with pytest.raises(expected):
            _provider(response=response).fetch(TAX_ID)

    @pytest.mark.parametrize("status", [401, 403])
    def test_s2s_denial_maps_to_source_unavailable_not_permission(self, status):
        with pytest.raises(EnrichmentSourceUnavailableError):
            _provider(response=_Resp(status=status)).fetch(TAX_ID)

    def test_rate_limited_preserves_retry_after(self):
        response = _Resp(
            status=429,
            payload={"detail": "x", "code": "EXTERNAL_DATA_RATE_LIMITED"},
            headers={"Retry-After": "42"},
        )
        with pytest.raises(RegistryRateLimitedError) as err:
            _provider(response=response).fetch(TAX_ID)
        assert err.value.retry_after == 42

    def test_transport_failure_fail_closed(self):
        with pytest.raises(EnrichmentSourceUnavailableError):
            _provider(raise_exc=Exception("connection refused")).fetch(TAX_ID)

    def test_token_failure_fail_closed(self):
        from delpi_auth.service_errors import ServiceAuthError

        class _Broken:
            def get_token(self):
                raise ServiceAuthError("service auth unavailable")

        with pytest.raises(EnrichmentSourceUnavailableError):
            _provider(token_provider=_Broken()).fetch(TAX_ID)


class TestFactory:
    def test_external_data_api_value_selects_new_adapter(self, monkeypatch):
        from app.infrastructure.config import settings

        monkeypatch.setattr(
            settings.Settings, "COMPANY_REGISTRY_PROVIDER", "external-data-api"
        )
        provider = supplier_enrichment_adapters.company_registry_provider()
        assert isinstance(provider, ExternalDataApiCompanyRegistryProvider)

    def test_existing_modes_unchanged(self, monkeypatch):
        from app.infrastructure.config import settings

        monkeypatch.setattr(
            settings.Settings, "COMPANY_REGISTRY_PROVIDER", "brasilapi"
        )
        assert isinstance(
            supplier_enrichment_adapters.company_registry_provider(),
            BrasilApiCompanyRegistryProvider,
        )
        for value in ("unavailable", "bogus"):
            monkeypatch.setattr(
                settings.Settings, "COMPANY_REGISTRY_PROVIDER", value
            )
            provider = supplier_enrichment_adapters.company_registry_provider()
            assert provider.__class__.__name__ == (
                "UnavailableCompanyRegistryProvider"
            )


class TestSmoke:
    def test_module_import(self):
        module = importlib.import_module(
            "app.infrastructure.gateways."
            "external_data_company_registry_provider"
        )
        assert hasattr(module, "ExternalDataApiCompanyRegistryProvider")
