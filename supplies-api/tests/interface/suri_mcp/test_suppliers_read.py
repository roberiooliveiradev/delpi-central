"""SURI semantic suppliers/postal reads — parity + AuthZ (rev.4).

Covers the G1 surface: ``read(entity=suppliers)`` actions
(search/get/catalogs/search_by_tax_id/existing/operations/
integration_status), ``read(entity=postal_codes, action=lookup)`` and
``analyze(analysis=supplier_creation_preview)`` — positive, sibling and
negative cases against the canonical BFF contracts, never new rules.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from suri_mcp.suri_fixtures import FakeGateway, make_context, make_user_ns

from app.application.services.supplier_enrichment.contracts import (
    EnrichmentSourceUnavailableError,
    RegistryRateLimitedError,
)
from app.domain.supplier_enrichment.models import ExternalRegistrySnapshot
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.mcp import tool_bridge


def _call(*args):
    try:
        return args[0](*args[1:])
    except Exception as exc:
        return tool_bridge.handle_tool_error(exc)


def _payload(result) -> dict:
    return json.loads(result.content[0].text)


def _envelope(data) -> dict:
    return {"success": True, "data": data}


@pytest.fixture()
def s2s_gateway(monkeypatch):
    def _install(payload=None, error=None) -> FakeGateway:
        gw = FakeGateway(payload=payload, error=error)
        monkeypatch.setattr(tool_bridge, "_S2S_GATEWAY", gw)
        return gw

    return _install


@pytest.fixture()
def manage_context(monkeypatch):
    def _install():
        monkeypatch.setattr(
            tool_bridge,
            "require_mcp_context",
            lambda: make_context(
                make_user_ns(
                    permissions=["supplies.access", "supplies.manage"]
                )
            ),
        )

    return _install


@pytest.fixture()
def fake_dup_search(monkeypatch):
    def _install(items=None, total=0):
        class _Fake:
            def __init__(self):
                self.calls = []

            def search_by_tax_id(self, tax_id, *, access_token="", page=1, page_size=20):
                self.calls.append(
                    {
                        "tax_id": tax_id,
                        "access_token": access_token,
                        "page": page,
                        "page_size": page_size,
                    }
                )
                return items or [], total

        fake = _Fake()
        monkeypatch.setattr(
            tool_bridge, "DelpiSupplierDuplicateSearch", lambda *a, **k: fake
        )
        return fake

    return _install


@pytest.fixture()
def fake_preview(monkeypatch):
    """Fake registry provider + rate limiter for preview analysis."""

    def _install(provider=None, limiter_error=None):
        class _FakeLimiter:
            def __init__(self):
                self.calls = []

            def acquire(self, scope, key):
                self.calls.append((scope, key))
                if limiter_error is not None:
                    raise limiter_error

        limiter = _FakeLimiter()
        monkeypatch.setattr(
            tool_bridge, "registry_rate_limiter", lambda: limiter
        )
        if provider is not None:
            monkeypatch.setattr(
                tool_bridge, "company_registry_provider", lambda: provider
            )
        return limiter

    return _install


def _snapshot() -> ExternalRegistrySnapshot:
    return ExternalRegistrySnapshot(
        tax_id="04688277000100",
        source_id="brasilapi",
        retrieved_at="2026-10-30T12:00:00Z",
        fields={
            "company_name": "ACME LTDA",
            "address.street": "Rua X",
            "address.postal_code": "13000000",
            "address.state": "SP",
        },
    )


class _FakeProvider:
    def __init__(self, snapshot=None, error=None):
        self._snapshot = snapshot
        self._error = error
        self.calls = []

    def fetch(self, tax_id):
        self.calls.append(tax_id)
        if self._error is not None:
            raise self._error
        return self._snapshot


CNPJ = "04688277000100"
OP_ID = "123e4567-e89b-12d3-a456-426614174000"


class TestSupplierSearch:
    def test_positive_forwards_filters_and_projects(
        self, access_context, s2s_gateway
    ):
        access_context()
        gw = s2s_gateway(
            _envelope(
                {
                    "items": [{"supplier_code": "F01", "supplier_name": "X"}],
                    "page": 1,
                    "total": 1,
                }
            )
        )
        result = tool_bridge.tool_read(
            "suppliers",
            "search",
            filters={"query": "acme", "state": "SP", "blocked": True, "page": 2},
        )
        data = _payload(result)["data"]
        assert data["items"]
        call = gw.calls[0]
        assert call["path"] == "/supplies/suppliers"
        assert call["params"]["query"] == "acme"
        assert call["params"]["blocked"] == "true"
        assert call["params"]["page"] == "2"
        assert call["access_token"] == "token-abc"

    def test_negative_unknown_filter(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "suppliers", "search", filters={"sql": "1=1"}
        )
        body = _payload(result)
        assert body["success"] is False
        assert body["status_code"] == 422

    def test_negative_identity_on_search(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "suppliers", "search", identity={"supplier_code": "1"}
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_no_access(self, no_access_context, s2s_gateway):
        gw = s2s_gateway(_envelope({"items": []}))
        result = _call(
            tool_bridge.tool_read, "suppliers", "search", {"query": "x"}, None
        )
        body = _payload(result)
        assert body["status_code"] == 403
        assert gw.calls == []

    def test_negative_anonymous(self, anonymous_context):
        result = _call(
            tool_bridge.tool_read, "suppliers", "search", {"query": "x"}, None
        )
        assert _payload(result)["status_code"] == 401


class TestSupplierGet:
    def test_positive_identity_path(self, access_context, s2s_gateway):
        access_context()
        gw = s2s_gateway(_envelope({"supplier_code": "000001", "name": "X"}))
        result = tool_bridge.tool_read(
            "suppliers",
            "get",
            identity={"supplier_code": "1", "supplier_store": "1"},
        )
        assert _payload(result)["success"] is True
        assert (
            gw.calls[0]["path"]
            == "/integrations/protheus/suppliers/00000101"
        )

    def test_negative_invalid_identity(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "suppliers",
            "get",
            identity={"supplier_code": "1234567", "supplier_store": "01"},
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_filters_on_get(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "suppliers", "get", filters={"query": "x"}
        )
        assert _payload(result)["status_code"] == 422


class TestSupplierCatalogs:
    def test_positive_kind_allowlist(self, access_context, s2s_gateway):
        access_context()
        gw = s2s_gateway(_envelope({"items": [{"code": "SP"}]}))
        result = tool_bridge.tool_read(
            "suppliers", "catalogs", filters={"kind": "states", "limit": 10}
        )
        assert _payload(result)["success"] is True
        call = gw.calls[0]
        assert call["path"] == "/supplies/supplier-catalogs/states"
        assert call["params"]["limit"] == "10"

    def test_negative_kind_outside_allowlist(self, access_context, s2s_gateway):
        access_context()
        gw = s2s_gateway(_envelope({}))
        result = tool_bridge.tool_read(
            "suppliers", "catalogs", filters={"kind": "sa2_raw"}
        )
        body = _payload(result)
        assert body["status_code"] == 422
        assert gw.calls == []

    def test_limit_clamped_to_500(self, access_context, s2s_gateway):
        access_context()
        gw = s2s_gateway(_envelope({"items": []}))
        tool_bridge.tool_read(
            "suppliers", "catalogs", filters={"kind": "states", "limit": 9999}
        )
        assert gw.calls[0]["params"]["limit"] == "500"


class TestSupplierTaxId:
    def test_positive_search_by_tax_id(
        self, access_context, fake_dup_search
    ):
        access_context()
        fake = fake_dup_search(
            items=[
                {
                    "supplier_code": "000001",
                    "supplier_store": "01",
                    "supplier_name": "ACME",
                    "state": "SP",
                    "blocked": False,
                    "internal_field": "redacted",
                }
            ],
            total=1,
        )
        result = tool_bridge.tool_read(
            "suppliers", "search_by_tax_id", filters={"tax_id": CNPJ}
        )
        data = _payload(result)["data"]
        assert data["total"] == 1
        assert data["items"][0]["supplier_code"] == "000001"
        assert "internal_field" not in data["items"][0]
        assert fake.calls[0]["tax_id"] == CNPJ

    def test_positive_existing_verdict(
        self, access_context, fake_dup_search
    ):
        access_context()
        fake_dup_search(items=[{"supplier_code": "1"}], total=1)
        result = tool_bridge.tool_read(
            "suppliers", "existing", filters={"tax_id": CNPJ}
        )
        data = _payload(result)["data"]
        assert data["exists"] is True
        assert data["total"] == 1

    def test_existing_absent(self, access_context, fake_dup_search):
        access_context()
        fake_dup_search(items=[], total=0)
        result = tool_bridge.tool_read(
            "suppliers", "existing", filters={"tax_id": CNPJ}
        )
        data = _payload(result)["data"]
        assert data["exists"] is False

    def test_negative_invalid_cnpj(self, access_context, fake_dup_search):
        access_context()
        fake = fake_dup_search(items=[])
        result = tool_bridge.tool_read(
            "suppliers", "existing", filters={"tax_id": "123"}
        )
        body = _payload(result)
        assert body["status_code"] == 422
        assert fake.calls == []

    def test_page_size_capped_50(self, access_context, fake_dup_search):
        access_context()
        fake = fake_dup_search(items=[])
        tool_bridge.tool_read(
            "suppliers",
            "search_by_tax_id",
            filters={"tax_id": CNPJ, "page_size": 500},
        )
        assert fake.calls[0]["page_size"] == 50


class TestSupplierOperations:
    def test_positive_operation_lookup(self, access_context, s2s_gateway):
        access_context()
        gw = s2s_gateway(
            _envelope(
                {
                    "operation_id": OP_ID,
                    "status": "CONFIRMED",
                    "correlation_id": "corr-1",
                }
            )
        )
        result = tool_bridge.tool_read(
            "suppliers", "operations", identity={"operation_id": OP_ID}
        )
        data = _payload(result)["data"]
        assert data["status"] == "CONFIRMED"
        assert data["persistence_proven"] is True
        assert (
            gw.calls[0]["path"] == f"/integrations/operations/{OP_ID}"
        )

    def test_negative_invalid_operation_id(self, access_context):
        access_context()
        result = tool_bridge.tool_read(
            "suppliers", "operations", identity={"operation_id": "abc"}
        )
        assert _payload(result)["status_code"] == 422


class TestIntegrationStatus:
    def test_positive_manage_only(self, manage_context, s2s_gateway):
        manage_context()
        s2s_gateway(
            _envelope({"overall": "ok", "authentication_http_status": 200})
        )
        result = tool_bridge.tool_read("suppliers", "integration_status")
        data = _payload(result)["data"]
        assert data["overall"] == "ok"

    def test_negative_access_only_forbidden(
        self, access_context, s2s_gateway
    ):
        access_context()
        gw = s2s_gateway(_envelope({}))
        result = _call(
            tool_bridge.tool_read, "suppliers", "integration_status", None, None
        )
        body = _payload(result)
        assert body["status_code"] == 403
        assert gw.calls == []

    def test_negative_params_rejected(self, manage_context):
        manage_context()
        result = tool_bridge.tool_read(
            "suppliers", "integration_status", filters={"x": 1}
        )
        assert _payload(result)["status_code"] == 422


class TestPostalCodeLookup:
    def test_positive_projection(self, access_context, s2s_gateway):
        access_context()
        s2s_gateway(
            _envelope(
                {
                    "postal_code": "13000000",
                    "street": "Rua X",
                    "district": "Centro",
                    "city": "Campinas",
                    "state": "SP",
                    "found": True,
                }
            )
        )
        result = tool_bridge.tool_read(
            "postal_codes", "lookup", identity={"postal_code": "13000-000"}
        )
        data = _payload(result)["data"]
        assert data["found"] is True
        assert data["city"] == "Campinas"

    def test_negative_invalid_cep(self, access_context, s2s_gateway):
        access_context()
        gw = s2s_gateway(_envelope({}))
        result = tool_bridge.tool_read(
            "postal_codes", "lookup", identity={"postal_code": "123"}
        )
        assert _payload(result)["status_code"] == 422
        assert gw.calls == []

    def test_provider_unreachable_504(self, access_context, s2s_gateway):
        access_context()
        s2s_gateway(error=DelpiApiGatewayError("timeout", status_code=None))
        result = tool_bridge.tool_read(
            "postal_codes", "lookup", identity={"postal_code": "13000000"}
        )
        body = _payload(result)
        assert body["status_code"] == 504
        assert body["data"]["error_code"] == "provider_unreachable"

    def test_provider_error_502(self, access_context, s2s_gateway):
        access_context()
        s2s_gateway(error=DelpiApiGatewayError("boom", status_code=500))
        result = tool_bridge.tool_read(
            "postal_codes", "lookup", identity={"postal_code": "13000000"}
        )
        body = _payload(result)
        assert body["status_code"] == 502
        assert body["data"]["error_code"] == "provider_error"


class TestSupplierCreationPreview:
    def test_positive_read_only_preview(
        self, access_context, fake_dup_search, fake_preview
    ):
        access_context()
        fake_dup_search(items=[], total=0)
        provider = _FakeProvider(snapshot=_snapshot())
        limiter = fake_preview(provider=provider)
        result = tool_bridge.tool_analyze(
            "supplier_creation_preview", filters={"tax_id": CNPJ}
        )
        body = _payload(result)
        assert body["success"] is True
        data = body["data"]
        assert data["write_enabled"] is False
        assert data["duplicate_check"]["status"] == "CLEAR"
        assert isinstance(data["suggestions"], list)
        assert "unavailable_fields" in data
        assert provider.calls == [CNPJ]
        assert limiter.calls == [("actor", "user-1")]

    def test_provider_unavailable_honest_state(
        self, access_context, fake_preview
    ):
        access_context()
        provider = _FakeProvider(error=EnrichmentSourceUnavailableError("off"))
        fake_preview(provider=provider)
        result = tool_bridge.tool_analyze(
            "supplier_creation_preview", filters={"tax_id": CNPJ}
        )
        body = _payload(result)
        assert body["success"] is False
        assert body["status_code"] == 503
        assert (
            body["data"]["error_code"] == "ENRICHMENT_SOURCE_UNAVAILABLE"
        )

    def test_rate_limited_maps_429(
        self, access_context, fake_preview
    ):
        access_context()
        provider = _FakeProvider(snapshot=_snapshot())
        fake_preview(
            provider=provider,
            limiter_error=RegistryRateLimitedError("cap", retry_after=30),
        )
        result = _call(
            tool_bridge.tool_analyze,
            "supplier_creation_preview",
            {"tax_id": CNPJ},
            50,
        )
        body = _payload(result)
        assert body["status_code"] == 429
        assert body["data"]["error_code"] == "ENRICHMENT_RATE_LIMITED"
        assert body["data"]["retry_after"] == 30

    def test_negative_invalid_tax_id(self, access_context, fake_preview):
        access_context()
        fake_preview(provider=_FakeProvider())
        result = tool_bridge.tool_analyze(
            "supplier_creation_preview", filters={"tax_id": "999"}
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_unknown_filter(self, access_context, fake_preview):
        access_context()
        fake_preview(provider=_FakeProvider())
        result = tool_bridge.tool_analyze(
            "supplier_creation_preview",
            filters={"tax_id": CNPJ, "url": "http://evil"},
        )
        assert _payload(result)["status_code"] == 422

    def test_negative_no_access(self, no_access_context):
        result = _call(
            tool_bridge.tool_analyze,
            "supplier_creation_preview",
            {"tax_id": CNPJ},
            50,
        )
        assert _payload(result)["status_code"] == 403


class TestDispatchClosed:
    def test_unknown_entity(self, access_context):
        access_context()
        result = tool_bridge.tool_read("products", "search")
        assert _payload(result)["status_code"] == 422

    def test_action_not_allowed_for_entity(self, access_context):
        access_context()
        result = tool_bridge.tool_read("suppliers", "lookup")
        assert _payload(result)["status_code"] == 422
        result = tool_bridge.tool_read("postal_codes", "search")
        assert _payload(result)["status_code"] == 422

    def test_unknown_analysis(self, access_context):
        access_context()
        result = tool_bridge.tool_analyze("invented_analysis")
        assert _payload(result)["status_code"] == 422
