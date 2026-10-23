"""Application orchestration — supplier creation preview (X4.UX-R1.S1)."""

from __future__ import annotations

import pytest

from app.application.services.supplier_creation_preview.preview_service import (
    SupplierCreationPreviewService,
)
from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    RegistryTaxIdNotFoundError,
)
from app.domain.supplier_enrichment.models import ExternalRegistrySnapshot
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError

TAX_ID = "00000000000191"


def _snapshot(fields: dict) -> ExternalRegistrySnapshot:
    return ExternalRegistrySnapshot(
        tax_id=TAX_ID,
        source_id="brasilapi-cnpj-v1",
        retrieved_at="2026-10-23T12:00:00Z",
        fields=fields,
    )


class _FakeRegistry:
    def __init__(self, snapshot=None, error=None):
        self._snapshot = snapshot
        self._error = error

    def fetch(self, tax_id: str):
        if self._error:
            raise self._error
        return self._snapshot


class _FakeDuplicateSearch:
    def __init__(self, items=(), total=0, error=None):
        self._items = list(items)
        self._total = total
        self._error = error
        self.calls = []

    def search_by_tax_id(self, tax_id, *, access_token=""):
        self.calls.append((tax_id, access_token))
        if self._error:
            raise self._error
        return self._items, self._total


def _service(registry, duplicate_search):
    return SupplierCreationPreviewService(
        registry_provider=registry,
        duplicate_search=duplicate_search,
    )


_FIELDS = {
    "company.legal_name": "EMPRESA EXEMPLO LTDA",
    "company.trade_name": "EXEMPLO",
    "address.street": "RUA A, 10",
    "address.district": "CENTRO",
    "address.postal_code": "89012000",
    "address.state": "SC",
    "address.city": "BLUMENAU",
    "address.ibge_city_code": "00024",
}


class TestPreview:
    def test_full_response_shape(self):
        svc = _service(_FakeRegistry(_snapshot(_FIELDS)), _FakeDuplicateSearch())
        body = svc.preview(TAX_ID, access_token="user-jwt")

        assert body["tax_id_masked"] == "00.***.***/0001-**"
        assert body["person_type"] == "J"
        assert body["write_enabled"] is False
        assert body["duplicate_check"] == {
            "status": "CLEAR",
            "matches": [],
            "total": 0,
        }

        by_key = {s["field_key"]: s for s in body["suggestions"]}
        assert by_key["supplier_name"]["suggested_value"] == "EMPRESA EXEMPLO LTDA"
        assert by_key["supplier_name"]["source"] == {
            "provider_id": "brasilapi-cnpj-v1",
            "retrieved_at": "2026-10-23T12:00:00Z",
        }
        assert by_key["supplier_name"]["applicable"] is True
        assert by_key["supplier_short_name"]["applicable"] is False

    def test_internal_fields_listed_unavailable_never_suggested(self):
        svc = _service(_FakeRegistry(_snapshot(_FIELDS)), _FakeDuplicateSearch())
        body = svc.preview(TAX_ID)
        assert set(body["unavailable_fields"]) >= {
            "payment_condition_code",
            "accounting_account",
            "financial_nature_code",
            "supplier_store",
            "payment_method_code",
            "rohs_indicator",
        }
        assert "supplier_name" not in body["unavailable_fields"]
        assert "tax_id" not in body["unavailable_fields"]
        assert "person_type" not in body["unavailable_fields"]

    def test_possible_match_returns_minimal_identification(self):
        items = [
            {
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "EXISTENTE LTDA",
                "state": "SC",
                "blocked": False,
                "tax_id": TAX_ID,
            }
        ]
        svc = _service(
            _FakeRegistry(_snapshot(_FIELDS)),
            _FakeDuplicateSearch(items=items, total=1),
        )
        dup = svc.preview(TAX_ID)["duplicate_check"]
        assert dup["status"] == "POSSIBLE_MATCH"
        assert dup["matches"] == [
            {
                "supplier_code": "000001",
                "supplier_store": "01",
                "supplier_name": "EXISTENTE LTDA",
                "state": "SC",
                "blocked": False,
            }
        ]

    def test_duplicate_search_failure_is_inconclusive_never_clear(self):
        svc = _service(
            _FakeRegistry(_snapshot(_FIELDS)),
            _FakeDuplicateSearch(
                error=DelpiApiGatewayError("down", status_code=500)
            ),
        )
        dup = svc.preview(TAX_ID)["duplicate_check"]
        assert dup == {
            "status": "INCONCLUSIVE",
            "matches": [],
            "total": None,
        }

    def test_registry_errors_propagate(self):
        svc = _service(
            _FakeRegistry(error=RegistryTaxIdNotFoundError("not found")),
            _FakeDuplicateSearch(),
        )
        with pytest.raises(RegistryTaxIdNotFoundError):
            svc.preview(TAX_ID)

    def test_source_unavailable_propagates(self):
        svc = _service(
            _FakeRegistry(
                error=EnrichmentSourceUnavailableError("no provider")
            ),
            _FakeDuplicateSearch(),
        )
        with pytest.raises(EnrichmentSourceUnavailableError):
            svc.preview(TAX_ID)
