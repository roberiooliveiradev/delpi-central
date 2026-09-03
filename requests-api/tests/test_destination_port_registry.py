from __future__ import annotations

from uuid import uuid4

import pytest

from requests_app.composition.destination_registry import (
    DestinationAdapterRegistry,
    UnknownDestinationAdapterError,
)
from requests_app.domain.entities import Request
from requests_app.infrastructure.gateways.api_delpi_adapter import ApiDelpiAdapter
from requests_app.infrastructure.gateways.commercial_adapter import CommercialAdapter


def test_registry_resolves_api_delpi_and_commercial():
    registry = DestinationAdapterRegistry()
    assert set(registry.known_adapters()) == {"api_delpi", "commercial"}
    api = registry.resolve_from_config({"adapter": "api_delpi", "capabilities": ["lookups"]})
    commercial = registry.resolve("commercial")
    assert isinstance(api, ApiDelpiAdapter)
    assert isinstance(commercial, CommercialAdapter)
    assert api.adapter_name == "api_delpi"
    assert commercial.adapter_name == "commercial"


def test_registry_unknown_adapter():
    registry = DestinationAdapterRegistry()
    with pytest.raises(UnknownDestinationAdapterError):
        registry.resolve("unknown")


def test_commercial_stub_deliver():
    adapter = CommercialAdapter()
    assert adapter.health().ok is True
    result = adapter.deliver(
        request=Request(
            id=uuid4(),
            request_number="REQ-1",
            request_type_id=uuid4(),
            type_code="invoice-issuance",
            status="submitted",
            created_by_user_id="u1",
            created_by_name="Criador",
            payload={},
            branch_code="01",
            version=1,
        ),
        event_type="request.created",
        payload={"x": 1},
    )
    assert result.ok is True
    assert "deliver" in result.detail.lower() or "stub" in result.detail.lower() or "acknowledged" in result.detail.lower()


def test_api_delpi_deliver_stub_without_http():
    adapter = ApiDelpiAdapter(base_url="http://example.invalid")
    result = adapter.deliver(
        request=Request(
            id=uuid4(),
            request_number="REQ-2",
            request_type_id=uuid4(),
            type_code="invoice-issuance",
            status="submitted",
            created_by_user_id="u1",
            created_by_name="Criador",
            payload={},
            branch_code="01",
            version=1,
        ),
        event_type="noop",
        payload={"a": True},
    )
    assert result.ok is True
    assert result.meta["payload_keys"] == ["a"]
