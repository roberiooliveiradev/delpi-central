from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from requests_app.application.errors import ApplicationError
from requests_app.application.services.payload_validator_registry import (
    PayloadValidatorRegistry,
)
from requests_app.application.use_cases.invoice_issuance_lookup_use_cases import (
    InvoiceIssuanceLookupUseCases,
)
from requests_app.application.use_cases.request_use_cases import CreateRequestUseCase
from requests_app.domain.services.invoice_issuance_payload_validator import (
    InvoiceIssuancePayloadValidator,
)
from requests_app.domain.services.request_type_registry import RequestTypeRegistry
from requests_app.infrastructure.gateways.api_delpi_adapter import (
    InMemoryOperationalLookupAdapter,
)
from requests_app.infrastructure.persistence.repositories.memory_repositories import (
    InMemoryIdempotencyRepository,
    InMemoryRequestRepository,
    InMemoryRequestTypeRepository,
)


def _type():
    return RequestTypeRegistry.from_workflow_content(
        code="invoice-issuance",
        name="Emissão NF",
        workflow_name="invoice_issuance",
        permission_prefix="my-requests.invoice-issuance",
        branch_scope="required",
    )


def _user():
    return SimpleNamespace(
        id="u1",
        name="Solicitante",
        permissions=[
            "my-requests.access",
            "my-requests.invoice-issuance.create",
            "my-requests.view.filial-01",
        ],
        access_token="Bearer test",
    )


def _valid_payload() -> dict:
    return {
        "party_type": "customer",
        "party_code": "C001",
        "party_store": "01",
        "party_name": "Cliente Teste",
        "invoice_type": "sale",
        "freight_mode": "cif",
        "weight_kg": 1.5,
        "volume_count": 2,
        "items": [
            {
                "product_code": "P001",
                "product_description": "Item",
                "quantity": 1,
                "unit_price": 10,
            }
        ],
    }


def test_validator_rejects_empty_items():
    validator = InvoiceIssuancePayloadValidator()
    with pytest.raises(ApplicationError) as exc:
        validator.validate({**_valid_payload(), "items": []})
    assert exc.value.status_code == 422


def test_validator_normalizes_payload():
    out = InvoiceIssuancePayloadValidator().validate(_valid_payload())
    assert out["freight_mode"] == "cif"
    assert out["items"][0]["product_code"] == "P001"
    assert out["weight_kg"] == "1.5"


def test_lookups_return_api_delpi_shape():
    types = InMemoryRequestTypeRepository([_type()])
    lookups = InMemoryOperationalLookupAdapter()
    uc = InvoiceIssuanceLookupUseCases(types, lookups)
    parties = uc.search_parties(user=_user(), party_type="customer", query="cli")
    assert "items" in parties
    assert parties["items"][0]["party_code"] == "C001"
    products = uc.search_products(user=_user(), query="prod")
    assert products["items"][0]["product_code"] == "P001"
    carriers = uc.search_carriers(user=_user(), query="trans")
    assert carriers["items"][0]["carrier_code"] == "T01"
    orders = uc.list_open_sales_orders(
        user=_user(), branch="01", party_code="C001", party_store="01"
    )
    assert orders["orders_count"] == 0
    balance = uc.warehouse_balance(user=_user(), product_code="P001", branch="01")
    assert balance["warehouse"] == "01"
    assert balance["balance"] == 10.0


def test_create_request_uses_invoice_validator():
    types = InMemoryRequestTypeRepository([_type()])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    registry = PayloadValidatorRegistry()
    registry.register(InvoiceIssuancePayloadValidator())
    created = CreateRequestUseCase(
        types, requests, idem, validators=registry
    ).execute(
        user=_user(),
        type_code="invoice-issuance",
        branch_code="01",
        payload=_valid_payload(),
        idempotency_key=str(uuid4()),
    )
    assert created["type_code"] == "invoice-issuance"
    assert created["payload"]["items"][0]["product_code"] == "P001"


def test_create_request_rejects_invalid_invoice_payload():
    types = InMemoryRequestTypeRepository([_type()])
    requests = InMemoryRequestRepository()
    idem = InMemoryIdempotencyRepository()
    registry = PayloadValidatorRegistry()
    registry.register(InvoiceIssuancePayloadValidator())
    with pytest.raises(ApplicationError):
        CreateRequestUseCase(types, requests, idem, validators=registry).execute(
            user=_user(),
            type_code="invoice-issuance",
            branch_code="01",
            payload={"party_type": "customer"},
            idempotency_key=str(uuid4()),
        )
