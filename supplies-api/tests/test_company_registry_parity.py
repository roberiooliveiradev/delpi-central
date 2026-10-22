"""X2 parity — local BrasilAPI adapter vs shared external-data-api adapter.

The same synthetic BrasilAPI record feeds both paths:

- local: raw BrasilAPI payload → BrasilApiCompanyRegistryProvider
- shared: X1 DTO v1 (what external-data-api would emit) →
  ExternalDataApiCompanyRegistryProvider

Expected: identical S1 field values for every non-contact key, identical
source_id/identity semantics, and identical S1 comparison outcomes.
Contact fields are an INTENTIONAL_DIFFERENCE (X1 LGPD restriction) and
asserted as such, never silently equated.
"""

from __future__ import annotations

import pytest

from app.infrastructure.gateways.brasilapi_registry_provider import (
    BrasilApiCompanyRegistryProvider,
)
from app.infrastructure.gateways.external_data_company_registry_provider import (
    ExternalDataApiCompanyRegistryProvider,
)
from app.infrastructure.gateways.registry_rate_limits import (
    InMemoryRegistryRateLimiter,
)
from app.domain.supplier_enrichment.comparison import (
    compare_supplier_snapshots,
)

TAX_ID = "19131243000197"

BRASILAPI_PAYLOAD = {
    "cnpj": "19.131.243/0001-97",
    "razao_social": "OPEN KNOWLEDGE BRASIL",
    "nome_fantasia": None,
    "descricao_tipo_de_logradouro": "ALAMEDA",
    "logradouro": "FRANCA",
    "numero": "243",
    "complemento": "APT 34",
    "bairro": "SAO PAULO",
    "cep": "01422-030",
    "municipio": "SAO PAULO",
    "uf": "SP",
    "codigo_municipio_ibge": 3550308,
    "ddd_telefone_1": "1132223344",
    "ddd_telefone_2": "11999887766",
    "email": "contato@acme.example",
    "descricao_situacao_cadastral": "ATIVA",
    "cnae_fiscal_descricao": "6201-5/00",
    "natureza_juridica": "206-2",
    "data_inicio_atividade": "2013-10-03",
    "qsa": [{"nome_socio": "PERSON", "cpf_cnpj_socio": "***.***.***-**"}],
}

X1_DTO = {
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
        "correlation_id": "corr-parity-1",
        "schema_version": "v1",
    },
}

CONTACT_KEYS = ("contact.area_code", "contact.phone", "contact.email")


class _Resp:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload
        self.headers = {}

    def json(self):
        return self._payload


class _TokenProvider:
    def get_token(self):
        return "s2s-token-abc"


def _local_snapshot():
    provider = BrasilApiCompanyRegistryProvider(
        base_url="https://brasilapi.example/api",
        timeout_seconds=6,
        rate_limiter=InMemoryRegistryRateLimiter(limit_per_minute=1000),
        transport=lambda url, timeout: _Resp(BRASILAPI_PAYLOAD),
    )
    return provider.fetch(TAX_ID)


def _shared_snapshot():
    provider = ExternalDataApiCompanyRegistryProvider(
        base_url="http://external-data-api:8000",
        timeout_seconds=10,
        transport=lambda url, *, headers, timeout: _Resp(X1_DTO),
        token_provider=_TokenProvider(),
    )
    return provider.fetch(TAX_ID)


class TestSnapshotParity:
    def test_non_contact_fields_equivalent(self):
        local = _local_snapshot()
        shared = _shared_snapshot()
        assert local.tax_id == shared.tax_id == TAX_ID
        assert local.source_id == shared.source_id == "brasilapi-cnpj-v1"
        for key in set(local.fields) | set(shared.fields):
            if key in CONTACT_KEYS:
                continue
            assert shared.fields.get(key) == local.fields.get(key), key

    def test_contact_fields_intentional_difference(self):
        local = _local_snapshot()
        shared = _shared_snapshot()
        # Local adapter projected contacts; the shared API withholds them
        # by contract (LGPD). Shared snapshot carries the keys as null.
        assert local.fields.get("contact.area_code") == "11"
        assert local.fields.get("contact.phone") == "32223344"
        assert local.fields.get("contact.email") == "contato@acme.example"
        assert all(shared.fields.get(k) is None for k in CONTACT_KEYS)

    def test_source_reference_traceable(self):
        shared = _shared_snapshot()
        assert shared.source_reference == "brasilapi-cnpj-v1:cnpj-…0197"
        assert TAX_ID[-4:] in shared.source_reference

    def test_s1_comparison_equivalent_outside_contacts(self):
        from tests.test_supplier_enrichment_comparison import canonical

        def canonical_tax_matched():
            c = canonical()
            return c.__class__(
                supplier=c.supplier,
                tax_id=TAX_ID,
                person_type=c.person_type,
                fields=c.fields,
                baseline_reference=c.baseline_reference,
            )

        local_review = compare_supplier_snapshots(
            canonical_tax_matched(), _local_snapshot()
        )
        shared_review = compare_supplier_snapshots(
            canonical_tax_matched(), _shared_snapshot()
        )
        non_contact_proposals = lambda r: {
            p.field_key
            for p in r.comparison.proposals
            if not any(k.endswith(p.field_key) for k in CONTACT_KEYS)
            and p.field_key not in ("area_code", "phone", "email")
        }
        assert non_contact_proposals(shared_review) == non_contact_proposals(
            local_review
        )

    def test_no_qsa_or_cpf_leaks(self):
        shared = _shared_snapshot()
        assert all("qsa" not in k for k in shared.fields)
        assert all("cpf" not in k for k in shared.fields)
        assert all("socio" not in k for k in shared.fields)
