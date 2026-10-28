"""OpenAPI capability provider — ARCH-DRIFT-DELIA-PROVIDER-NEUTRAL-
ORCHESTRATION-01 (ledger §6.130).

Proves the OpenAPI family projects declared semantic capabilities into
the provider-neutral surface, READ characters are invocable end-to-end
through the HTTP invoker, and every other character stays
discoverable-but-UNKNOWN (never invocable).
"""

from __future__ import annotations

import pytest
from pathlib import Path

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

    def http_get(url, headers=None, timeout=None, stream=None):
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


def _product_capability(provider):
    group = provider.list_groups(correlation_id="c").groups[0]
    return next(
        c for c in group.capabilities
        if c.remote_name == "delpi.get_product"
    )


def test_owner_not_found_envelope_is_not_a_dead_source():
    """HTTP 404 with the owner not-found envelope is absence."""

    def http_get(url, headers=None, timeout=None, stream=None):
        return FakeResponse(
            404,
            {
                "success": False,
                "message": "Produto ZZ-SMOKE-0000 não encontrado",
                "data": None,
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "recoverable": False,
                },
            },
        )

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(
            _product_capability(provider),
            {"product_id": "ZZ-SMOKE-0000"},
            correlation_id="c",
        )
    assert exc.value.code == "owner_record_not_found"
    assert exc.value.owner_hint == "Produto ZZ-SMOKE-0000 não encontrado"
    assert "tente novamente" not in (exc.value.owner_hint or "").lower()


def test_bare_404_stays_invocation_failure():
    """A 404 without the owner envelope is not record absence."""

    def http_get(url, headers=None, timeout=None, stream=None):
        return FakeResponse(404, {"detail": "Not Found"})

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(
            _product_capability(provider),
            {"product_id": "missing"},
            correlation_id="c",
        )
    assert exc.value.code == "openapi_invocation_failed"
    assert exc.value.owner_hint is None


def test_recoverable_404_stays_invocation_failure():
    """Recoverable 404 is not the owner's terminal absence."""

    def http_get(url, headers=None, timeout=None, stream=None):
        return FakeResponse(
            404,
            {
                "success": False,
                "message": "tente novamente",
                "error": {"code": "TEMPORARY", "recoverable": True},
            },
        )

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(
            _product_capability(provider),
            {"product_id": "x"},
            correlation_id="c",
        )
    assert exc.value.code == "openapi_invocation_failed"


def test_not_found_envelope_on_500_stays_invocation_failure():
    """The same envelope on HTTP 500 remains a source failure."""

    def http_get(url, headers=None, timeout=None, stream=None):
        return FakeResponse(
            500,
            {
                "success": False,
                "message": "Produto ausente",
                "error": {"code": "PRODUCT_NOT_FOUND", "recoverable": False},
            },
        )

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(
            _product_capability(provider),
            {"product_id": "x"},
            correlation_id="c",
        )
    assert exc.value.code == "openapi_invocation_failed"


def _invoke_for_status(status, body):
    def http_get(url, headers=None, timeout=None, stream=None):
        return FakeResponse(status, body)

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(
            _product_capability(provider),
            {"product_id": "x"},
            correlation_id="c",
        )
    return exc.value


def test_declared_recoverable_400_is_owner_argument_rejection():
    """HTTP 400 whose shared envelope explicitly declares
    ``error.recoverable: true`` is an owner argument rejection —
    the bounded message becomes a sanitized hint for repair."""
    err = _invoke_for_status(
        400,
        {
            "success": False,
            "message": "product_type inválido: use códigos de 2 caracteres (ex.: MP,PI,PA).",
            "data": None,
            "error": {"code": "VALIDATION_ERROR", "recoverable": True},
        },
    )
    assert err.code == "owner_argument_rejected"
    assert err.owner_hint is not None
    assert "2 caracteres" in err.owner_hint


def test_typed_validation_code_400_is_owner_argument_rejection():
    """An owner-published argument-validation code authorizes
    repair even without an explicit recoverable flag (typed
    classification, never message matching)."""
    err = _invoke_for_status(
        400,
        {
            "success": False,
            "message": "invalid field combination",
            "error": {"code": "VALIDATION_ERROR"},
        },
    )
    assert err.code == "owner_argument_rejected"
    assert err.owner_hint == "invalid field combination"


def test_typed_validation_code_422_is_owner_argument_rejection():
    """The typed argument-validation contract applies to 422."""
    err = _invoke_for_status(
        422,
        {
            "success": False,
            "message": "unprocessable arguments",
            "error": {"code": "VALIDATION_ERROR", "recoverable": True},
        },
    )
    assert err.code == "owner_argument_rejected"


def test_undeclared_400_envelope_stays_invocation_failure():
    """REWORK contract: a 400 shared envelope WITHOUT any
    recoverability declaration is NOT repairable — absence of
    ``recoverable:false`` never implies ``recoverable:true``."""
    err = _invoke_for_status(
        400,
        {
            "success": False,
            "message": "product_type inválido: use códigos de 2 caracteres (ex.: MP,PI,PA).",
            "data": None,
            "error": None,
        },
    )
    assert err.code == "openapi_invocation_failed"
    assert err.owner_hint is None


def test_untyped_error_block_400_stays_invocation_failure():
    """An error block with a non-validation code and no
    recoverable flag stays terminal."""
    err = _invoke_for_status(
        400,
        {
            "success": False,
            "message": "business rule violated",
            "error": {"code": "BUSINESS_RULE"},
        },
    )
    assert err.code == "openapi_invocation_failed"
    assert err.owner_hint is None


def test_explicit_non_recoverable_400_stays_invocation_failure():
    """An owner-declared non-recoverable rejection is terminal —
    it never reaches the contract-repair path."""
    err = _invoke_for_status(
        400,
        {
            "success": False,
            "message": "rejected permanently",
            "error": {"code": "BUSINESS", "recoverable": False},
        },
    )
    assert err.code == "openapi_invocation_failed"
    assert err.owner_hint is None


def test_non_recoverable_flag_overrides_validation_code():
    """``recoverable:false`` wins over a typed validation code —
    the owner's negation is authoritative."""
    err = _invoke_for_status(
        400,
        {
            "success": False,
            "message": "denied",
            "error": {"code": "VALIDATION_ERROR", "recoverable": False},
        },
    )
    assert err.code == "openapi_invocation_failed"
    assert err.owner_hint is None


def test_bare_422_without_contract_stays_invocation_failure():
    """A 422 without the shared envelope classification fails
    closed."""
    err = _invoke_for_status(
        422,
        {"success": False, "message": "unprocessable", "error": None},
    )
    assert err.code == "openapi_invocation_failed"


def test_bare_400_without_envelope_stays_invocation_failure():
    """A 400 without the shared envelope is not an owner
    argument rejection — transport-shaped failure stays plain."""
    err = _invoke_for_status(400, {"detail": "Bad Request"})
    assert err.code == "openapi_invocation_failed"
    assert err.owner_hint is None


def test_invoker_drops_undeclared_arguments():
    """Arguments not declared as OpenAPI inputs never reach the wire."""
    calls = []

    def http_get(url, headers=None, timeout=None, stream=None):
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
    def http_get(url, headers=None, timeout=None, stream=None):
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

    def http_get(url, headers=None, timeout=None, stream=None):
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
    # bounded_request sends (connect, read-slice) — the total bound is
    # the connect leg; read slices are tightened to the remaining
    # wall-clock by the drain loop.
    assert [t[0] for t in timeouts] == [0.25, 15.0, 15.0]


# --- LOOP-03R2A-R2: total wall-clock on OpenAPI remote calls --------------
#
# requests.get(timeout=N) alone is per-recv inactivity semantics — a
# server that trickles bytes keeps the call alive forever. R2 routes
# both the document fetch and the capability GET through the shared
# infrastructure wall-clock bound; these tests use a REAL local
# socket + real requests so the trickle cannot be faked.


def _trickle_server(trickle_paths=(), chunk_delay=0.05):
    """HTTP server: trickle paths emit 1-byte chunks forever; other
    paths answer the canned OpenAPI document immediately."""
    import http.server
    import json as _json
    import threading
    import time as _time

    document = _document()

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.split("?")[0]
            if path in trickle_paths or (
                not trickle_paths and path != "/openapi.json"
            ):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                while True:
                    try:
                        self.wfile.write(b"x")
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    _time.sleep(chunk_delay)
                return
            if path == "/openapi.json" and "/openapi.json" in trickle_paths:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                while True:
                    try:
                        self.wfile.write(b"x")
                        self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        return
                    _time.sleep(chunk_delay)
                return
            body = _json.dumps(document).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def test_r2_openapi_document_trickle_bounded():
    """R2-04: a document that trickles bytes forever cannot outlive
    the caller bound — truthful unavailable, elapsed near the bound."""
    import time as _time

    from app.infrastructure.http.deadline_transport import (
        deadline_http_get,
    )
    from app.infrastructure.openapi.http_invoker import (
        fetch_openapi_document,
    )

    server = _trickle_server(trickle_paths=("/openapi.json",))
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        started = _time.monotonic()
        with pytest.raises(CapabilityProviderError) as exc:
            fetch_openapi_document(
                base, http_get=deadline_http_get, timeout_seconds=0.4
            )
        assert exc.value.code == "openapi_document_unavailable"
        assert _time.monotonic() - started < 2.0
    finally:
        server.shutdown()


def test_r2_openapi_invoke_trickle_bounded():
    """R2-04: the capability GET shares the same total wall-clock
    bound — document fast, capability endpoint trickles forever."""
    import time as _time

    from app.infrastructure.http.deadline_transport import (
        deadline_http_get,
    )

    server = _trickle_server(trickle_paths=("/api/products",))
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        invoker = HttpOpenApiInvoker(
            base,
            source_id="delpi",
            subject_bearer_getter=lambda: "tok",
            http_get=deadline_http_get,
            timeout_seconds=30.0,
        )
        provider = OpenApiCapabilityProvider([_source(invoker)])
        cap = next(
            c
            for c in provider.list_groups(correlation_id="c").groups[
                0
            ].capabilities
            if c.remote_name == "delpi.list_products"
        )
        started = _time.monotonic()
        with pytest.raises(CapabilityProviderError) as exc:
            provider.invoke(
                cap, {}, correlation_id="c", timeout_seconds=0.4
            )
        assert exc.value.code == "openapi_invocation_failed"
        assert _time.monotonic() - started < 2.0
    finally:
        server.shutdown()


def test_r2_openapi_explicit_nonpositive_fail_fast():
    """R2-03: timeout_seconds <= 0 fails fast with zero wire calls —
    never a fresh configured window — on both OpenAPI seams."""
    calls: list = []

    def http_get(url, headers=None, timeout=None, stream=None):
        calls.append(url)
        return FakeResponse(200, {"ok": True})

    from app.infrastructure.openapi.http_invoker import (
        fetch_openapi_document,
    )

    for bound in (0.0, -2.0):
        with pytest.raises(CapabilityProviderError) as exc:
            fetch_openapi_document(
                "http://h", http_get=http_get, timeout_seconds=bound
            )
        assert exc.value.code == "openapi_document_unavailable"

    invoker = HttpOpenApiInvoker(
        "http://h",
        source_id="delpi",
        subject_bearer_getter=lambda: "t",
        http_get=http_get,
    )
    provider = OpenApiCapabilityProvider([_source(invoker)])
    cap = next(
        c
        for c in provider.list_groups(correlation_id="c").groups[
            0
        ].capabilities
        if c.remote_name == "delpi.list_products"
    )
    with pytest.raises(CapabilityProviderError) as exc:
        provider.invoke(cap, {}, correlation_id="c", timeout_seconds=0.0)
    assert exc.value.code == "openapi_invocation_failed"
    assert calls == []


# ---------------------------------------------------------------------------
# Direct DELPI boundary removal (task
# DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-AND-DEPLOY-01): the DELPI OpenAPI
# source binding is eliminated entirely. Product decision: capabilities
# without a DAVI substitute are legitimately unavailable — never served
# through a direct DELIA -> API DELPI path.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DELPI_DECLARATIONS_FILE = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "openapi_declarations.delpi.json"
)


def test_no_direct_delpi_declarations_file():
    assert not _DELPI_DECLARATIONS_FILE.exists()


def test_no_governed_declarations_expose_direct_delpi_capabilities():
    import json

    config_dir = Path(__file__).resolve().parent.parent / "config"
    direct_ids = set()
    for f in config_dir.glob("openapi_declarations*.json"):
        payload = json.loads(f.read_text(encoding="utf-8"))
        for d in payload.get("declarations", []):
            cid = str(d.get("capability_id", ""))
            if cid.startswith("delpi."):
                direct_ids.add(cid)
    assert direct_ids == set()


def test_composer_has_no_direct_delpi_source():
    composer = (
        Path(__file__).resolve().parent.parent
        / "app"
        / "composition"
        / "root_composer.py"
    ).read_text(encoding="utf-8")
    assert 'source_id="delpi"' not in composer
    assert "_wire_openapi_provider" not in composer
    assert "openapi_delpi_" not in composer


def test_infra_and_env_carry_no_direct_delpi_wiring():
    files = [
        _REPO_ROOT / "infra" / "docker-compose.yml",
        _REPO_ROOT / "infra" / "docker-compose.dev.yml",
        _REPO_ROOT / "delia-api" / "env.example",
    ]
    offenders = [
        str(f)
        for f in files
        if f.exists() and "DELIA_OPENAPI_DELPI" in f.read_text(encoding="utf-8")
    ]
    assert offenders == []
