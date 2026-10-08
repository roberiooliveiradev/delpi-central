"""OpenAPI capability provider — ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-
ORCHESTRATION-01 (ledger §6.130).

Proves the OpenAPI family projects declared semantic capabilities into
the provider-neutral surface, READ characters are invocable end-to-end
through the HTTP invoker, and every other character stays
discoverable-but-UNKNOWN (never invocable).
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.capability_provision.openapi_provider import (
    OpenApiCapabilityProvider,
    OpenApiCapabilitySource,
)
from app.domain.capability_catalog.model import OperationCharacter
from app.domain.specialist_interop.model import SpecialistOperationClass
from app.infrastructure.openapi.capability_catalog_adapter import (
    CapabilityDeclaration,
    project_openapi_document,
)
from app.infrastructure.openapi.http_invoker import HttpOpenApiInvoker


def _document():
    return {
        "openapi": "3.0.0",
        "info": {"title": "DELPI", "version": "1.0.0"},
        "paths": {
            "/api/products": {
                "get": {
                    "operationId": "list_products",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/products/{product_id}": {
                "get": {
                    "operationId": "get_product",
                    "parameters": [
                        {
                            "name": "product_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "detail",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            },
                        }
                    },
                },
                "put": {
                    "operationId": "update_product",
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            },
                        }
                    },
                },
            },
        },
    }


DECLARATIONS = (
    CapabilityDeclaration(
        operation_id="list_products",
        capability_id="delpi.list_products",
        semantic_name="Listar produtos DELPI",
        operation_character=OperationCharacter.READ,
    ),
    CapabilityDeclaration(
        operation_id="get_product",
        capability_id="delpi.get_product",
        semantic_name="Consultar produto",
        operation_character=OperationCharacter.READ,
    ),
    CapabilityDeclaration(
        operation_id="update_product",
        capability_id="delpi.update_product",
        semantic_name="Atualizar produto",
        operation_character=OperationCharacter.ACT,
    ),
)


def _source(invoker):
    def projector(timeout_seconds=None):
        return project_openapi_document(
            _document(),
            source_owner="DELPI",
            source_contract_id="delpi-api",
            declarations=DECLARATIONS,
        ).capabilities

    return OpenApiCapabilitySource(
        source_id="delpi",
        owner_ref="DELPI",
        display_name="DELPI API",
        projector=projector,
        invoker=invoker,
    )


# --- provider discovery --------------------------------------------------


def test_provider_projects_declared_capabilities():
    provider = OpenApiCapabilityProvider([_source(lambda c, a, t=None: None)])
    surface = provider.list_groups(correlation_id="c")
    assert len(surface.groups) == 1
    group = surface.groups[0]
    assert group.provider_id == "openapi"
    assert group.group_id == "delpi"
    names = {c.remote_name for c in group.capabilities}
    assert names == {
        "delpi.list_products",
        "delpi.get_product",
        "delpi.update_product",
    }


def test_read_capabilities_invocable_writes_unknown():
    """READ projections are invocable; the declared ACT capability is
    discoverable but UNKNOWN — never invocable in this phase."""
    provider = OpenApiCapabilityProvider([_source(lambda c, a, t=None: None)])
    group = provider.list_groups(correlation_id="c").groups[0]
    by_name = {c.remote_name: c for c in group.capabilities}
    assert (
        by_name["delpi.list_products"].operation_class
        is SpecialistOperationClass.READ
    )
    assert (
        by_name["delpi.update_product"].operation_class
        is SpecialistOperationClass.UNKNOWN
    )


def test_projection_requires_declarations():
    """No declaration -> no capability: undeclared operations are
    rejected by the governed projection, never inferred from HTTP
    mechanics."""
    projection = project_openapi_document(
        _document(),
        source_owner="DELPI",
        source_contract_id="delpi-api",
        declarations=(),
    )
    assert projection.capabilities == ()
    assert len(projection.rejected) == 3


def test_projector_failure_is_truthful():
    def bad(timeout_seconds=None):
        raise CapabilityProviderError("openapi_document_unavailable")

    provider = OpenApiCapabilityProvider(
        [_source(lambda c, a, t=None: None)]
    )
    source = list(provider._source_by_group.values())[0]
    broken = OpenApiCapabilitySource(
        source_id="broken",
        owner_ref="X",
        display_name="X",
        projector=bad,
        invoker=lambda c, a, t=None: None,
    )
    provider = OpenApiCapabilityProvider([broken])
    surface = provider.list_groups(correlation_id="c")
    assert surface.groups == ()
    assert surface.failures == ("openapi_document_unavailable",)


# --- invocation ----------------------------------------------------------


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"ok": True}
        import json

        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload


def test_invoker_renders_path_and_query():
    calls = []

    def http_get(url, headers=None, timeout=None):
        calls.append((url, dict(headers or {})))
        return FakeResponse(200, {"product": "X1"})

    invoker = HttpOpenApiInvoker(
        "http://api-delpi:8000",
        source_id="delpi",
        subject_bearer_getter=lambda: "tok-subject",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    group = provider.list_groups(correlation_id="c").groups[0]
    cap = next(
        c for c in group.capabilities
        if c.remote_name == "delpi.get_product"
    )
    outcome = provider.invoke(
        cap, {"product_id": "X1", "detail": "full"}, correlation_id="c"
    )
    url, headers = calls[0]
    assert url == "http://api-delpi:8000/api/products/X1?detail=full"
    assert headers["Authorization"] == "Bearer tok-subject"
    assert outcome.structured == {"product": "X1"}
    assert outcome.provenance.specialist_id == "delpi"
    assert outcome.provenance.protocol.value == "HTTP"


def test_invoker_drops_undeclared_arguments():
    """Arguments not declared as OpenAPI inputs never reach the wire."""
    calls = []

    def http_get(url, headers=None, timeout=None):
        calls.append(url)
        return FakeResponse()

    invoker = HttpOpenApiInvoker(
        "http://h", source_id="delpi",
        subject_bearer_getter=lambda: "t", http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    group = provider.list_groups(correlation_id="c").groups[0]
    cap = next(
        c for c in group.capabilities
        if c.remote_name == "delpi.list_products"
    )
    provider.invoke(cap, {"evil_param": "x"}, correlation_id="c")
    assert "evil_param" not in calls[0]


def test_invoker_refuses_non_get():
    invoker = HttpOpenApiInvoker(
        "http://h", source_id="delpi",
        subject_bearer_getter=lambda: "t", http_get=lambda *a, **k: None,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    group = provider.list_groups(correlation_id="c").groups[0]
    cap = next(
        c for c in group.capabilities
        if c.remote_name == "delpi.update_product"
    )
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(cap, {}, correlation_id="c")
    assert exc.value.code == "openapi_write_not_authorized"


def test_invoker_denied_maps_authorization():
    def http_get(url, headers=None, timeout=None):
        return FakeResponse(403)

    invoker = HttpOpenApiInvoker(
        "http://h", source_id="delpi",
        subject_bearer_getter=lambda: "t", http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    group = provider.list_groups(correlation_id="c").groups[0]
    cap = group.capabilities[0]
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(cap, {}, correlation_id="c")
    assert exc.value.code == "mcp_authorization_denied"


def test_missing_bearer_fails_closed():
    invoker = HttpOpenApiInvoker(
        "http://h", source_id="delpi",
        subject_bearer_getter=lambda: None,
        http_get=lambda *a, **k: FakeResponse(),
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    group = provider.list_groups(correlation_id="c").groups[0]
    cap = group.capabilities[0]
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(cap, {}, correlation_id="c")
    assert exc.value.code == "mcp_authentication_failed"


def test_invoke_stamps_turn_correlation_id():
    """LOOP-03R1 (D09): the turn correlation id is runtime authority —
    an invoker outcome carrying a foreign/absent correlation is
    re-stamped so every outcome joins the request-scoped trace."""
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )

    def invoker(capability, arguments, timeout_seconds=None):
        return SpecialistOutcome(
            status=SpecialistResultStatus.COMPLETED,
            provenance=SpecialistResultProvenance(
                specialist_id="delpi",
                remote_name=capability.remote_name,
                protocol=InteropProtocol.HTTP,
                correlation_id="foreign-or-absent",
                observed_at="2026-01-01T00:00:00+00:00",
            ),
            content_text="ok",
            is_complete=True,
        )

    provider = OpenApiCapabilityProvider([_source(invoker)])
    group = provider.list_groups(correlation_id="turn-1").groups[0]
    cap = next(
        c for c in group.capabilities
        if c.remote_name == "delpi.get_product"
    )
    outcome = provider.invoke(cap, {}, correlation_id="turn-1")
    assert outcome.provenance.correlation_id == "turn-1"


# --- R1: provider-neutral timeout contract ------------------------------------


def test_r1_list_groups_forwards_bounded_timeout_to_projector():
    """LOOP-03R2A-R1: the caller's remaining budget reaches the
    provider-owned projection closure — reduction-only."""
    received = []

    def projector(timeout_seconds=None):
        received.append(timeout_seconds)
        return ()

    source = OpenApiCapabilitySource(
        source_id="delpi",
        owner_ref="DELPI",
        display_name="DELPI API",
        projector=projector,
        invoker=lambda c, a, t=None: None,
    )
    provider = OpenApiCapabilityProvider([source])
    provider.list_groups(correlation_id="c", timeout_seconds=0.5)
    assert len(received) == 1
    assert received[0] == pytest.approx(0.5, abs=0.05)


def test_r1_list_groups_no_bound_passes_none():
    """Without a caller bound the projector receives None — its own
    configured stage max applies (legacy behavior unchanged)."""
    received = []

    def projector(timeout_seconds=None):
        received.append(timeout_seconds)
        return ()

    source = OpenApiCapabilitySource(
        source_id="delpi",
        owner_ref="DELPI",
        display_name="DELPI API",
        projector=projector,
        invoker=lambda c, a, t=None: None,
    )
    OpenApiCapabilityProvider([source]).list_groups(correlation_id="c")
    assert received == [None]


def test_r1_invoker_shortens_never_lengthens_http_timeout():
    """The per-turn bound shortens the configured stage max; a larger
    bound never widens it."""
    timeouts = []

    def http_get(url, headers=None, timeout=None):
        timeouts.append(timeout)
        return FakeResponse(200, {"product": "X1"})

    invoker = HttpOpenApiInvoker(
        "http://api-delpi:8000",
        source_id="delpi",
        subject_bearer_getter=lambda: "tok",
        http_get=http_get,
        timeout_seconds=15.0,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    cap = next(
        c
        for c in provider.list_groups(correlation_id="c").groups[
            0
        ].capabilities
        if c.remote_name == "delpi.get_product"
    )
    provider.invoke(
        cap, {"product_id": "X1"}, correlation_id="c",
        timeout_seconds=0.25,
    )
    provider.invoke(
        cap, {"product_id": "X1"}, correlation_id="c",
        timeout_seconds=99.0,
    )
    provider.invoke(cap, {"product_id": "X1"}, correlation_id="c")
    assert timeouts == [0.25, 15.0, 15.0]
