"""Offline contract tests for BrasilApiCompanyRegistryProvider (S3.1).

Fixtures are synthetic payloads shaped after the documented BrasilAPI CNPJ
v1 schema (pages/docs/doc/cnpj.json) — they are not captured responses.
No network access is performed: a fake transport injects responses.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    RegistryAccessDeniedError,
    RegistryRateLimitedError,
    RegistryResponseInvalidError,
    RegistryTaxIdInvalidError,
    RegistryTaxIdNotFoundError,
)
from app.infrastructure.gateways.brasilapi_registry_provider import (
    BrasilApiCompanyRegistryProvider,
    InMemoryRegistryRateLimiter,
)

TAX_ID = "19131243000197"
NOW = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)


def _payload(**overrides):
    base = {
        "cnpj": TAX_ID,
        "razao_social": "EMPRESA TESTE LTDA",
        "nome_fantasia": "TESTE FANTASIA",
        "descricao_tipo_de_logradouro": "AVENIDA",
        "logradouro": "PAULISTA",
        "numero": "37",
        "complemento": "ANDAR 4",
        "bairro": "BELA VISTA",
        "cep": "01311902",
        "municipio": "SAO PAULO",
        "uf": "SP",
        "codigo_municipio_ibge": 3550308,
        "ddd_telefone_1": "1123851939",
        "ddd_telefone_2": "",
        "email": "contato@empresa.test",
        "descricao_situacao_cadastral": "ATIVA",
        "cnae_fiscal": 9430800,
        "cnae_fiscal_descricao": "Atividades de associacoes",
        "natureza_juridica": "Sociedade Empresaria Limitada",
        "data_inicio_atividade": "2013-10-03",
        "qsa": [{"cnpj_cpf_do_socio": "***123456**"}],
    }
    base.update(overrides)
    return base


class _Resp:
    def __init__(self, status, body=None, headers=None, json_error=False):
        self.status_code = status
        self.headers = headers or {}
        self._body = body
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("not json")
        return self._body


def _provider(body=None, status=200, headers=None, json_error=False, exc=None):
    calls: list[str] = []

    def transport(url, *, timeout):
        calls.append(url)
        if exc is not None:
            raise exc
        return _Resp(status, body=body, headers=headers, json_error=json_error)

    provider = BrasilApiCompanyRegistryProvider(
        base_url="https://brasilapi.test/api",
        timeout_seconds=3,
        transport=transport,
        clock=lambda: NOW,
    )
    return provider, calls


# --- happy path -------------------------------------------------------------


def test_fetch_maps_documented_fields():
    provider, calls = _provider(body=_payload())
    snap = provider.fetch(TAX_ID)

    assert calls == [f"https://brasilapi.test/api/cnpj/v1/{TAX_ID}"]
    assert snap.source_id == "brasilapi-cnpj-v1"
    assert snap.tax_id == TAX_ID
    assert snap.retrieved_at == NOW.isoformat()
    fields = snap.fields
    assert fields["company.tax_id"] == TAX_ID
    assert fields["company.legal_name"] == "EMPRESA TESTE LTDA"
    assert fields["company.trade_name"] == "TESTE FANTASIA"
    assert fields["address.street"] == "AVENIDA PAULISTA, 37 ANDAR 4"
    assert fields["address.district"] == "BELA VISTA"
    assert fields["address.postal_code"] == "01311902"
    assert fields["address.state"] == "SP"
    assert fields["address.city"] == "SAO PAULO"
    assert fields["address.ibge_city_code"] == "3550308"
    assert fields["contact.area_code"] == "11"
    assert fields["contact.phone"] == "23851939"
    assert fields["contact.email"] == "contato@empresa.test"
    assert fields["company.registration_status"] == "ATIVA"
    assert fields["company.main_cnae"] == "9430800 - Atividades de associacoes"
    assert fields["company.legal_nature"] == "Sociedade Empresaria Limitada"
    assert fields["company.opening_date"] == "2013-10-03"


def test_fetch_never_projects_qsa_fields():
    provider, _ = _provider(body=_payload())
    snap = provider.fetch(TAX_ID)
    assert not any("socio" in k or "qsa" in k or "cpf" in k for k in snap.fields)
    assert "***123456**" not in snap.fields.values()


def test_source_reference_masks_tax_id():
    provider, _ = _provider(body=_payload())
    snap = provider.fetch(TAX_ID)
    assert TAX_ID not in snap.source_reference
    assert snap.source_reference.endswith("0197")


# --- partial / optional fields -----------------------------------------------


def test_partial_payload_missing_optionals():
    body = {"cnpj": TAX_ID, "razao_social": "SO A RAZAO"}
    provider, _ = _provider(body=body)
    snap = provider.fetch(TAX_ID)
    assert snap.fields["company.legal_name"] == "SO A RAZAO"
    assert snap.fields["address.street"] is None
    assert snap.fields["contact.phone"] is None


def test_null_and_empty_fields_become_none():
    body = _payload(email=None, complemento="", numero="S/N", cep="01.311-902")
    provider, _ = _provider(body=body)
    snap = provider.fetch(TAX_ID)
    assert snap.fields["contact.email"] is None
    assert snap.fields["address.postal_code"] == "01311902"
    assert "S/N" not in (snap.fields["address.street"] or "")


def test_unknown_extra_fields_are_ignored():
    body = _payload(novo_campo_inesperado="x", capital_social=1000)
    provider, _ = _provider(body=body)
    snap = provider.fetch(TAX_ID)
    assert "novo_campo_inesperado" not in snap.fields
    assert "capital_social" not in snap.fields


# --- identity / schema failures -----------------------------------------------


def test_divergent_cnpj_rejected():
    provider, _ = _provider(body=_payload(cnpj="99999999000199"))
    with pytest.raises(RegistryResponseInvalidError):
        provider.fetch(TAX_ID)


def test_missing_cnpj_in_payload_rejected():
    provider, _ = _provider(body={"razao_social": "SEM CNPJ"})
    with pytest.raises(RegistryResponseInvalidError):
        provider.fetch(TAX_ID)


def test_non_object_payload_rejected():
    provider, _ = _provider(body=["not", "an", "object"])
    with pytest.raises(RegistryResponseInvalidError):
        provider.fetch(TAX_ID)


def test_invalid_json_rejected():
    provider, _ = _provider(status=200, json_error=True)
    with pytest.raises(RegistryResponseInvalidError):
        provider.fetch(TAX_ID)


def test_non_numeric_tax_id_fails_before_network():
    provider, calls = _provider(body=_payload())
    with pytest.raises(RegistryTaxIdInvalidError):
        provider.fetch("AB1234560001XX")
    assert calls == []


def test_short_tax_id_fails_before_network():
    provider, calls = _provider(body=_payload())
    with pytest.raises(RegistryTaxIdInvalidError):
        provider.fetch("12345")
    assert calls == []


# --- HTTP errors ---------------------------------------------------------------


@pytest.mark.parametrize("status", [400])
def test_http_400_invalid_tax_id(status):
    provider, _ = _provider(status=status, body={"type": "bad_request"})
    with pytest.raises(RegistryTaxIdInvalidError):
        provider.fetch(TAX_ID)


def test_http_404_not_found():
    provider, _ = _provider(status=404, body={"type": "not_found"})
    with pytest.raises(RegistryTaxIdNotFoundError):
        provider.fetch(TAX_ID)


def test_http_403_denied():
    provider, _ = _provider(status=403, body={})
    with pytest.raises(RegistryAccessDeniedError):
        provider.fetch(TAX_ID)


def test_http_429_rate_limited_with_retry_after():
    provider, _ = _provider(status=429, body={}, headers={"Retry-After": "30"})
    with pytest.raises(RegistryRateLimitedError) as err:
        provider.fetch(TAX_ID)
    assert err.value.retry_after == 30


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_http_5xx_unavailable(status):
    provider, _ = _provider(status=status, body={})
    with pytest.raises(EnrichmentSourceUnavailableError):
        provider.fetch(TAX_ID)


def test_unexpected_status_rejected():
    provider, _ = _provider(status=302, body={})
    with pytest.raises(RegistryResponseInvalidError):
        provider.fetch(TAX_ID)


def test_transport_failure_unavailable():
    provider, _ = _provider(exc=TimeoutError("timed out"))
    with pytest.raises(EnrichmentSourceUnavailableError):
        provider.fetch(TAX_ID)


def test_connection_error_unavailable():
    provider, _ = _provider(exc=ConnectionError("refused"))
    with pytest.raises(EnrichmentSourceUnavailableError):
        provider.fetch(TAX_ID)


# --- rate limiter ---------------------------------------------------------------


def test_limiter_blocks_after_cap():
    limiter = InMemoryRegistryRateLimiter(limit_per_minute=2)
    limiter.check("actor:u1")
    limiter.check("actor:u1")
    with pytest.raises(RegistryRateLimitedError) as err:
        limiter.check("actor:u1")
    assert err.value.retry_after is not None


def test_limiter_scoped_per_key():
    limiter = InMemoryRegistryRateLimiter(limit_per_minute=1)
    limiter.check("actor:u1")
    limiter.check("actor:u2")  # different key passes


def test_limiter_window_expires():
    t = [1000.0]
    limiter = InMemoryRegistryRateLimiter(limit_per_minute=1, clock=lambda: t[0])
    limiter.check("k")
    t[0] += 61
    limiter.check("k")


def test_provider_limits_repeated_cnpj_queries():
    provider, _ = _provider(body=_payload())
    limiter = InMemoryRegistryRateLimiter(limit_per_minute=1)
    provider._limiter = limiter
    provider.fetch(TAX_ID)
    with pytest.raises(RegistryRateLimitedError):
        provider.fetch(TAX_ID)


# --- provider selection ------------------------------------------------------


def test_factory_defaults_to_fail_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.gateways.supplier_enrichment_adapters import (
        UnavailableCompanyRegistryProvider,
        company_registry_provider,
    )

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "unavailable")
    assert isinstance(company_registry_provider(), UnavailableCompanyRegistryProvider)


def test_factory_selects_brasilapi(monkeypatch):
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.gateways.supplier_enrichment_adapters import (
        company_registry_provider,
    )

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "brasilapi")
    assert isinstance(
        company_registry_provider(), BrasilApiCompanyRegistryProvider
    )


def test_factory_unknown_value_fails_closed(monkeypatch):
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.gateways.supplier_enrichment_adapters import (
        UnavailableCompanyRegistryProvider,
        company_registry_provider,
    )

    monkeypatch.setattr(Settings, "COMPANY_REGISTRY_PROVIDER", "serpro")
    assert isinstance(company_registry_provider(), UnavailableCompanyRegistryProvider)
