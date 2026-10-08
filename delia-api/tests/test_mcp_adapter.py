"""MCP adapter + transport tests — C3-MCP-INTEROP-01.

Mock transport + fake HTTP: proves the second fail-closed boundary
(invocation re-check), profile gating (not configured / disabled / no
delegated credential), error normalization, size bound, timeout mapping,
session echo, and bounded outcome mapping. No real network.
"""

from __future__ import annotations

import json
import time
from typing import Any, Mapping

import pytest

from app.application.specialist_interop.errors import (
    CAPABILITY_NOT_ALLOWED_IN_PHASE,
    MCP_AUTHENTICATION_FAILED,
    MCP_AUTHORIZATION_DENIED,
    MCP_INVALID_RESPONSE,
    MCP_PROTOCOL_ERROR,
    MCP_RESULT_TOO_LARGE,
    MCP_TIMEOUT,
    MCP_UNAVAILABLE,
    SPECIALIST_DISABLED,
    SPECIALIST_NOT_CONFIGURED,
    UNKNOWN_CAPABILITY,
    SpecialistInteropError,
)
from app.domain.specialist_interop.model import SpecialistRef
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)
from app.infrastructure.interoperability.mcp.adapter import McpSpecialistAdapter
from app.infrastructure.interoperability.mcp.transport import DelpiMcpTransport


DAVI = SpecialistRef(
    specialist_id="davi", display_name="DAVI", owner_ref="api-delpi"
)

TOKEN = "unit-test-delegated-token"
DAVI_RESOURCE = "https://minhadelpi.com.br/apps/api-delpi/mcp"


def _profile(**overrides):
    values = {
        "endpoint": "http://svc:8000/mcp",
        "enabled": True,
        "timeout_seconds": 5.0,
        "exchange_audience": "mcp-api-delpi",
        "resource_audience": DAVI_RESOURCE,
    }
    values.update(overrides)
    return SpecialistConnectionProfile(**values)


class FakeCredentialProvider:
    """Deterministic delegated-credential stub — no exchange I/O."""

    def __init__(self, token: str = TOKEN, error: Exception | None = None):
        self.token = token
        self.error = error
        self.requests: list[str] = []
        self.credential_timeouts: list[float | None] = []
        self.invalidated: list[str] = []

    def credential_for(self, profile, *, timeout_seconds=None) -> str:
        self.requests.append(profile.resource_audience)
        self.credential_timeouts.append(timeout_seconds)
        if self.error is not None:
            raise self.error
        return self.token

    def invalidate(self, profile) -> None:
        self.invalidated.append(profile.resource_audience)


class FakeTransport:
    """Records calls; scripted results."""

    instances: list["FakeTransport"] = []

    def __init__(self, profile, bearer_token=None, tools=(), call_result=None):
        self.profile = profile
        self.bearer_token = bearer_token
        self.tools = tools
        self.call_result = call_result or {"content": []}
        self.initialized = False
        self.calls: list[tuple] = []
        FakeTransport.instances.append(self)

    def initialize(self, timeout_seconds=None):
        self.initialized = True
        self.init_timeout = timeout_seconds

    def list_tools(self, timeout_seconds=None):
        self.list_timeouts = getattr(self, 'list_timeouts', [])
        self.list_timeouts.append(timeout_seconds)
        return self.tools

    def call_tool(self, name, arguments, timeout_seconds=None):
        self.calls.append((name, dict(arguments)))
        self.call_timeout = timeout_seconds
        return self.call_result


def _adapter(tools=(), call_result=None, credential_provider=None, **profile_overrides):
    def factory(profile, bearer_token):
        return FakeTransport(
            profile, bearer_token=bearer_token, tools=tools, call_result=call_result
        )

    return McpSpecialistAdapter(
        {"davi": _profile(**profile_overrides)},
        credential_provider=(
            credential_provider
            if credential_provider is not None
            else FakeCredentialProvider()
        ),
        transport_factory=factory,
    )


def test_list_remote_tools_maps_wire_metadata():
    FakeTransport.instances.clear()
    adapter = _adapter(
        tools=(
            {
                "name": "discover_delpi_information",
                "description": "d",
                "inputSchema": {"type": "object"},
                "_meta": {"delpi/toolClass": "DISCOVERY"},
            },
            {
                "name": "execute_delpi_information",
                "_meta": {"delpi/toolClass": "READ"},
            },
        )
    )
    tools = adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert [t.remote_name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert tools[0].input_schema == {"type": "object"}
    assert tools[0].operation_class == "DISCOVERY"
    assert tools[1].operation_class == "READ"
    assert FakeTransport.instances[0].initialized is True


def test_specialist_not_configured():
    adapter = McpSpecialistAdapter({"davi": _profile(endpoint="")})
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == SPECIALIST_NOT_CONFIGURED


def test_specialist_disabled():
    adapter = _adapter(enabled=False)
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == SPECIALIST_DISABLED


def test_missing_delegated_token_fails_closed_before_wire():
    FakeTransport.instances.clear()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=None,
        transport_factory=lambda p, t: FakeTransport(p),
    )
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert FakeTransport.instances == []


def test_delegated_token_reaches_transport():
    FakeTransport.instances.clear()
    adapter = _adapter()
    adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert FakeTransport.instances[0].bearer_token == TOKEN


def test_auth_failure_invalidates_cached_credential():
    FakeTransport.instances.clear()

    class FailingTransport(FakeTransport):
        def initialize(self, timeout_seconds=None):
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED, "rejected"
            )

    provider = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=provider,
        transport_factory=lambda p, t: FailingTransport(p),
    )
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert provider.invalidated == [DAVI_RESOURCE]


_DISCOVERY_TOOL = {
    "name": "discover_delpi_information",
    "_meta": {"delpi/toolClass": "DISCOVERY"},
}
_READ_TOOL = {
    "name": "execute_delpi_information",
    "_meta": {"delpi/toolClass": "READ"},
}


def _adapter_with_failing_op(op: str):
    """Transport that raises MCP_AUTHENTICATION_FAILED on `op`."""

    class Failing(FakeTransport):
        def list_tools(self, timeout_seconds=None):
            if op == "list_tools":
                raise SpecialistInteropError(
                    MCP_AUTHENTICATION_FAILED, "401"
                )
            return (_DISCOVERY_TOOL,)

        def call_tool(self, name, arguments, timeout_seconds=None):
            if op == "call_tool":
                raise SpecialistInteropError(
                    MCP_AUTHENTICATION_FAILED, "401"
                )
            return super().call_tool(name, arguments, timeout_seconds=timeout_seconds)

    provider = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=provider,
        transport_factory=lambda p, t: Failing(p),
    )
    return adapter, provider


def test_tools_list_401_invalidates_credential():
    adapter, provider = _adapter_with_failing_op("list_tools")
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert provider.invalidated == [DAVI_RESOURCE]


def test_tools_call_401_invalidates_credential():
    adapter, provider = _adapter_with_failing_op("call_tool")
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.call_remote_tool(
            DAVI,
            "discover_delpi_information",
            {"query": "q"},
            correlation_id="c",
            timeout_seconds=5.0,
        )
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    # LOOP-03R1: a non-mutating call gets ONE bounded same-call retry
    # after invalidation — each failed attempt invalidates once.
    assert provider.invalidated == [DAVI_RESOURCE, DAVI_RESOURCE]


def test_tools_call_401_retries_once_for_non_mutating():
    """Sibling: the bounded re-exchange recovers a read whose cached
    token expired mid-call — exactly one retry, fresh transport."""

    class FlakyTransport(FakeTransport):
        calls_made = 0

        def list_tools(self, timeout_seconds=None):
            return (_DISCOVERY_TOOL,)

        def call_tool(self, name, arguments, timeout_seconds=None):
            FlakyTransport.calls_made += 1
            if FlakyTransport.calls_made == 1:
                raise SpecialistInteropError(
                    MCP_AUTHENTICATION_FAILED, "401 expired"
                )
            return {"content": [{"type": "text", "text": "ok"}]}

    FlakyTransport.calls_made = 0
    provider = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=provider,
        transport_factory=lambda p, t: FlakyTransport(p),
    )
    outcome = adapter.call_remote_tool(
        DAVI,
        "discover_delpi_information",
        {"query": "q"},
        correlation_id="c",
        timeout_seconds=5.0,
    )
    assert FlakyTransport.calls_made == 2
    assert provider.invalidated == [DAVI_RESOURCE]
    assert outcome.is_error is False


def test_tools_call_401_never_retries_mutating():
    """Negative: a PREPARE-class call gets zero material retries —
    the 401 invalidates and propagates immediately."""

    class FailingPrepare(FakeTransport):
        calls_made = 0

        def list_tools(self, timeout_seconds=None):
            return (
                {
                    "name": "prepare_change",
                    "_meta": {"delpi/toolClass": "PREPARE"},
                },
            )

        def call_tool(self, name, arguments, timeout_seconds=None):
            FailingPrepare.calls_made += 1
            raise SpecialistInteropError(
                MCP_AUTHENTICATION_FAILED, "401"
            )

    FailingPrepare.calls_made = 0
    provider = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=provider,
        transport_factory=lambda p, t: FailingPrepare(p),
    )
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.call_remote_tool(
            DAVI,
            "prepare_change",
            {"query": "q"},
            correlation_id="c",
            timeout_seconds=5.0,
        )
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert FailingPrepare.calls_made == 1
    assert provider.invalidated == [DAVI_RESOURCE]


def test_non_auth_wire_error_does_not_invalidate():
    class TimeoutTransport(FakeTransport):
        def list_tools(self, timeout_seconds=None):
            raise SpecialistInteropError(MCP_TIMEOUT, "slow")

    provider = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=provider,
        transport_factory=lambda p, t: TimeoutTransport(p),
    )
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == MCP_TIMEOUT
    assert provider.invalidated == []


def test_call_rechecks_policy_before_tools_call():
    """Second boundary: the owner class is re-read from a fresh
    tools/list on the same transport — connect+list may happen, but
    tools/call is never reached for an unadvertised name. Every
    owner-typed known class is eligible at this boundary (§6.126);
    write governance lives upstream."""
    FakeTransport.instances.clear()
    adapter = _adapter(
        tools=(
            _DISCOVERY_TOOL,
            _READ_TOOL,
            {"name": "commit_proposal", "_meta": {"delpi/toolClass": "ACT"}},
        )
    )
    for name, code in (
        ("commit_proposal_evil", UNKNOWN_CAPABILITY),
        ("prepare_x", UNKNOWN_CAPABILITY),
    ):
        with pytest.raises(SpecialistInteropError) as exc:
            adapter.call_remote_tool(
                DAVI, name, {}, correlation_id="c", timeout_seconds=5.0
            )
        assert exc.value.code == code
    assert all(not t.calls for t in FakeTransport.instances)
    # READ and owner-typed ACT are both eligible at this boundary.
    adapter.call_remote_tool(
        DAVI, "execute_delpi_information", {"candidate_token": "t"},
        correlation_id="c2", timeout_seconds=5.0,
    )
    adapter.call_remote_tool(
        DAVI, "commit_proposal", {"proposal_handle": "h"},
        correlation_id="c3", timeout_seconds=5.0,
    )
    wire = [n for t in FakeTransport.instances for n, _ in t.calls]
    assert "execute_delpi_information" in wire
    assert "commit_proposal" in wire


def test_call_write_class_reaches_wire_when_owner_typed():
    """Owner-typed ACT is eligible at the adapter boundary (§6.126) —
    governed-write confirmation/AuthZ is enforced upstream; the owner
    still revalidates live AuthZ at ACT time."""
    adapter = McpSpecialistAdapter(
        {"teo": _profile()},
        credential_provider=FakeCredentialProvider(),
        transport_factory=lambda p, t: FakeTransport(
            p,
            tools=(
                {"name": "commit_proposal", "_meta": {"delpi/toolClass": "ACT"}},
            ),
        ),
    )
    teo = SpecialistRef(
        specialist_id="teo", display_name="TEO", owner_ref="transformometro-api"
    )
    outcome = adapter.call_remote_tool(
        teo, "commit_proposal", {"proposal_handle": "h"},
        correlation_id="c", timeout_seconds=5.0,
    )
    assert outcome.is_error is False


def test_call_reclassified_capability_follows_fresh_owner_class():
    """Owner retypes a capability READ->PREPARE on the wire — the fresh
    classification is honored (the call is treated as a write-class
    invocation, never a stale read grant). Retyping to an
    unclassifiable/absent class still fails closed."""
    adapter = _adapter(
        tools=(
            {
                "name": "execute_delpi_information",
                "_meta": {"delpi/toolClass": "PREPARE"},
            },
        )
    )
    outcome = adapter.call_remote_tool(
        DAVI,
        "execute_delpi_information",
        {},
        correlation_id="c",
        timeout_seconds=5.0,
    )
    assert outcome.is_error is False
    assert any(
        "execute_delpi_information" in [n for n, _ in t.calls]
        for t in FakeTransport.instances
    )

    adapter2 = _adapter(
        tools=(
            {"name": "execute_delpi_information", "_meta": {}},
        )
    )
    with pytest.raises(SpecialistInteropError) as exc:
        adapter2.call_remote_tool(
            DAVI,
            "execute_delpi_information",
            {},
            correlation_id="c",
            timeout_seconds=5.0,
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_call_untyped_capability_not_invocable():
    adapter = _adapter(tools=({"name": "mystery_tool"},))
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.call_remote_tool(
            DAVI, "mystery_tool", {}, correlation_id="c", timeout_seconds=5.0
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED_IN_PHASE


def test_call_maps_bounded_outcome():
    adapter = _adapter(
        tools=(_DISCOVERY_TOOL,),
        call_result={
            "content": [{"type": "text", "text": "hello"}],
            "structuredContent": {"candidates": []},
            "isError": False,
        },
    )
    outcome = adapter.call_remote_tool(
        DAVI,
        "discover_delpi_information",
        {"query": "q"},
        correlation_id="c",
        timeout_seconds=5.0,
    )
    assert outcome.content_text == "hello"
    assert outcome.structured == {"candidates": []}
    assert outcome.is_error is False


def test_call_propagates_remote_is_error():
    adapter = _adapter(
        tools=(_DISCOVERY_TOOL,),
        call_result={
            "content": [{"type": "text", "text": "denied"}],
            "isError": True,
        },
    )
    outcome = adapter.call_remote_tool(
        DAVI,
        "discover_delpi_information",
        {"query": "q"},
        correlation_id="c",
        timeout_seconds=5.0,
    )
    assert outcome.is_error is True


# --- DelpiMcpTransport ---------------------------------------------------


class FakeResponse:
    def __init__(self, status=200, body=b"{}", headers=None):
        self.status_code = status
        self.content = body
        self.headers = headers or {"Content-Type": "application/json"}


def _rpc_result(request_id: int, result: Mapping[str, Any]) -> bytes:
    return json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "result": result}
    ).encode()


def _transport(canned):
    posts: list[tuple] = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append((url, dict(headers or {}), data))
        body, headers_, status = canned[len(posts) - 1]
        return FakeResponse(status=status, body=body, headers=headers_)

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=2.0,
        bearer_token=TOKEN,
        http_post=http_post,
    )
    return transport, posts


def test_transport_initialize_lists_and_calls():
    canned = [
        (
            _rpc_result(1, {"serverInfo": {"name": "davi"}}),
            {"Content-Type": "application/json", "mcp-session-id": "s1"},
            200,
        ),
        (b"", {"Content-Type": "application/json"}, 202),
        (
            _rpc_result(2, {"tools": [{"name": "get_catalog"}]}),
            {"Content-Type": "application/json"},
            200,
        ),
        (
            _rpc_result(3, {"content": [{"type": "text", "text": "ok"}]}),
            {"Content-Type": "application/json"},
            200,
        ),
    ]
    transport, posts = _transport(canned)
    transport.initialize()
    tools = transport.list_tools()
    assert tools[0]["name"] == "get_catalog"
    result = transport.call_tool("get_catalog", {})
    assert result["content"][0]["text"] == "ok"
    assert posts[0][1]["Authorization"] == f"Bearer {TOKEN}"
    # session id echoed after initialize
    assert posts[2][1]["mcp-session-id"] == "s1"
    # notification sent without id
    assert '"id"' not in posts[1][2]


def test_transport_auth_failures():
    transport, _ = _transport([(b"{}", {}, 401)])
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_AUTHENTICATION_FAILED

    transport, _ = _transport([(b"{}", {}, 403)])
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_AUTHORIZATION_DENIED


def test_transport_unavailable_and_protocol_error():
    transport, _ = _transport([(b"{}", {}, 503)])
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_UNAVAILABLE

    transport, _ = _transport(
        [
            (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "error": {"code": -32601, "message": "no method"},
                    }
                ).encode(),
                {},
                200,
            )
        ]
    )
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_PROTOCOL_ERROR


def test_transport_invalid_response_and_size_bound():
    transport, _ = _transport([(b"not json", {}, 200)])
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_INVALID_RESPONSE

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=2.0,
        bearer_token=TOKEN,
        http_post=lambda *a, **k: FakeResponse(body=b"x" * 100),
        max_response_bytes=10,
    )
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_RESULT_TOO_LARGE


def test_transport_timeout_maps_semantic():
    import requests

    def raising(*a, **k):
        raise requests.exceptions.ConnectTimeout("slow")

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=2.0,
        bearer_token=TOKEN,
        http_post=raising,
    )
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_TIMEOUT


def test_transport_sse_response_parsed():
    sse = b'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"serverInfo":{"name":"vista"}}}\n\n'
    transport, _ = _transport(
        [
            (sse, {"Content-Type": "text/event-stream"}, 200),
            (b"", {"Content-Type": "application/json"}, 202),
        ]
    )
    transport.initialize()


def test_transport_rejects_id_mismatch():
    canned = [
        (
            _rpc_result(99, {"serverInfo": {"name": "x"}}),
            {"Content-Type": "application/json"},
            200,
        )
    ]
    transport, _ = _transport(canned)
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize()
    assert exc.value.code == MCP_INVALID_RESPONSE


# --- C3-MCP-INTEROP-01R1C: host override trust boundary --------------


def test_transport_sends_host_header_only_when_configured():
    transport, posts = _transport(
        [
            (
                _rpc_result(1, {"serverInfo": {"name": "davi"}}),
                {"Content-Type": "application/json"},
                200,
            ),
            (b"", {"Content-Type": "application/json"}, 202),
        ]
    )
    transport.initialize()
    assert "Host" not in posts[0][1]

    posts.clear()

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append((url, dict(headers or {}), data))
        return FakeResponse(
            status=200,
            body=_rpc_result(1, {"serverInfo": {"name": "davi"}}),
            headers={"Content-Type": "application/json"},
        )

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=2.0,
        bearer_token=TOKEN,
        http_post=http_post,
        host_header="public.example",
    )
    transport.initialize()
    assert posts[0][1]["Host"] == "public.example"


def test_arguments_cannot_influence_transport_headers():
    """tools/call arguments are body data only — they can never steer
    transport-level headers such as Host or Authorization."""
    transport, posts = _transport(
        [
            (
                _rpc_result(1, {"serverInfo": {"name": "davi"}}),
                {"Content-Type": "application/json"},
                200,
            ),
            (b"", {"Content-Type": "application/json"}, 202),
            (
                _rpc_result(2, {"content": []}),
                {"Content-Type": "application/json"},
                200,
            ),
        ]
    )
    transport.initialize()
    transport.call_tool(
        "discover_delpi_information",
        {"host": "evil.example", "authorization": "Bearer x", "query": "q"},
    )
    call_headers = posts[2][1]
    assert "Host" not in call_headers
    assert call_headers["Authorization"] == f"Bearer {TOKEN}"


# --- R1: per-call bounded timeout reaches the wire -----------------------------


def test_r1_transport_per_call_timeout_shortens_never_lengthens():
    """LOOP-03R2A-R1: the bounded per-call timeout reaches
    requests.post — a smaller bound wins, a larger bound never
    widens the configured transport max."""
    canned = [
        (
            _rpc_result(1, {"serverInfo": {"name": "davi"}}),
            {"Content-Type": "application/json"},
            200,
        ),
        (b"", {"Content-Type": "application/json"}, 202),
        (
            _rpc_result(2, {"tools": []}),
            {"Content-Type": "application/json"},
            200,
        ),
        (
            _rpc_result(3, {"tools": []}),
            {"Content-Type": "application/json"},
            200,
        ),
    ]
    timeouts: list[float] = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        timeouts.append(timeout)
        body, headers_, status = canned[len(timeouts) - 1]
        return FakeResponse(status=status, body=body, headers=headers_)

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=2.0,
        bearer_token=TOKEN,
        http_post=http_post,
    )
    transport.initialize(timeout_seconds=0.5)
    transport.list_tools(timeout_seconds=0.25)
    transport.list_tools(timeout_seconds=99.0)
    # bounded_request passes (connect, read-slice) tuples — the
    # connect leg carries the operation bound: initialize rpc at 0.5,
    # notify at the REMAINDER (<0.5 after the rpc), then 0.25, then
    # the configured 2.0 max — never the requested 99.
    connect_timeouts = [t[0] for t in timeouts]
    assert connect_timeouts[0] == 0.5
    assert 0 < connect_timeouts[1] <= 0.5
    assert connect_timeouts[2] == 0.25
    assert connect_timeouts[3] == 2.0


def test_r1_transport_nonpositive_budget_fails_truthfully():
    """A non-positive per-call remainder is a bounded mcp_timeout —
    never a fresh full window on the wire."""
    canned = [
        (
            _rpc_result(1, {"serverInfo": {"name": "davi"}}),
            {"Content-Type": "application/json"},
            200,
        ),
        (b"", {"Content-Type": "application/json"}, 202),
    ]
    timeouts: list[float] = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        timeouts.append(timeout)
        body, headers_, status = canned[len(timeouts) - 1]
        return FakeResponse(status=status, body=body, headers=headers_)

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=2.0,
        bearer_token=TOKEN,
        http_post=http_post,
    )
    transport.initialize()
    with pytest.raises(SpecialistInteropError) as exc:
        transport.list_tools(timeout_seconds=0.0)
    assert exc.value.code == MCP_TIMEOUT
    assert len(timeouts) == 2


def test_r1_adapter_call_timeout_reaches_transport():
    """The port-level bound reaches every wire leg — connect,
    revalidation list and call share one shrinking budget."""
    FakeTransport.instances.clear()
    adapter = _adapter(
        tools=(
            {
                'name': 'get_catalog',
                '_meta': {'delpi/toolClass': 'READ'},
            },
        )
    )
    adapter.call_remote_tool(
        DAVI, 'get_catalog', {}, correlation_id='c1',
        timeout_seconds=2.5,
    )
    transport = FakeTransport.instances[-1]
    assert 0 < transport.init_timeout <= 2.5
    assert 0 < transport.list_timeouts[0] <= 2.5
    assert 0 < transport.call_timeout <= 2.5
    # legs share one shrinking budget — later legs never get more
    assert transport.call_timeout <= transport.list_timeouts[0]


# --- LOOP-03R2A-R2: shared operation clock / total wall-clock -------------


def test_r2_credential_bound_reaches_exchange():
    """R2-01: the port-level bound reaches credential_for — a cache
    miss may only consume the remaining share of the operation."""
    FakeTransport.instances.clear()
    creds = FakeCredentialProvider()
    adapter = _adapter(credential_provider=creds)
    adapter.list_remote_tools(DAVI, timeout_seconds=3.0)
    assert len(creds.credential_timeouts) == 1
    assert 0 < creds.credential_timeouts[0] <= 3.0


def test_r2_initialize_notification_only_gets_remainder():
    """R2-02: initialize rpc + initialized notification share ONE
    clock — the notification receives only the remainder."""
    canned = [
        (
            _rpc_result(1, {"serverInfo": {"name": "davi"}}),
            {"Content-Type": "application/json"},
            200,
        ),
        (b"", {"Content-Type": "application/json"}, 202),
    ]
    seen: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        seen.append(timeout)
        time.sleep(0.4)
        body, headers_, status = canned[len(seen) - 1]
        return FakeResponse(status=status, body=body, headers=headers_)

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=30.0,
        bearer_token=TOKEN,
        http_post=http_post,
    )
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize(timeout_seconds=0.5)
    assert exc.value.code == MCP_TIMEOUT
    # rpc consumed ~0.4 of 0.5 — the notification got only ~0.1,
    # never a fresh 0.5 window.
    assert len(seen) == 2
    assert seen[0][0] == 0.5
    assert 0 < seen[1][0] < 0.2


def test_r2_initialize_rpc_exhaustion_zero_notify_posts():
    """R2-02 negative: if the rpc leg consumes the whole bound the
    notification fails fast with zero wire calls."""
    seen: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        seen.append(timeout)
        time.sleep(0.6)
        body = _rpc_result(1, {"serverInfo": {"name": "davi"}})
        return FakeResponse(
            status=200,
            body=body,
            headers={"Content-Type": "application/json"},
        )

    transport = DelpiMcpTransport(
        "http://svc:8000/mcp",
        timeout_seconds=30.0,
        bearer_token=TOKEN,
        http_post=http_post,
    )
    with pytest.raises(SpecialistInteropError) as exc:
        transport.initialize(timeout_seconds=0.5)
    assert exc.value.code == MCP_TIMEOUT
    assert len(seen) == 1


def test_r2_auth_retry_shares_original_clock():
    """R2: 401 → invalidate → re-exchange → retry — all inside the
    SAME operation bound; the retry only gets the remainder."""

    class FlakyTransport(FakeTransport):
        calls_made = 0

        def list_tools(self, timeout_seconds=None):
            self.list_timeouts = getattr(self, "list_timeouts", [])
            self.list_timeouts.append(timeout_seconds)
            return (_DISCOVERY_TOOL,)

        def call_tool(self, name, arguments, timeout_seconds=None):
            FlakyTransport.calls_made += 1
            self.call_timeout = timeout_seconds
            if FlakyTransport.calls_made == 1:
                raise SpecialistInteropError(
                    MCP_AUTHENTICATION_FAILED, "401 expired"
                )
            return {"content": [{"type": "text", "text": "ok"}]}

    FlakyTransport.calls_made = 0
    FakeTransport.instances.clear()
    creds = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=creds,
        transport_factory=lambda p, t: FlakyTransport(p),
    )
    outcome = adapter.call_remote_tool(
        DAVI,
        "discover_delpi_information",
        {"query": "q"},
        correlation_id="c",
        timeout_seconds=2.5,
    )
    assert outcome.is_error is False
    assert FlakyTransport.calls_made == 2
    # re-exchange happened under the same shrinking budget — both
    # credential bounds fit inside the original 2.5s and shrink.
    assert len(creds.credential_timeouts) == 2
    assert 0 < creds.credential_timeouts[1] <= creds.credential_timeouts[0]
    assert creds.credential_timeouts[0] <= 2.5
    retry_transport = FakeTransport.instances[-1]
    assert 0 < retry_transport.call_timeout <= 2.5


def test_r2_adapter_zero_budget_zero_wire_calls():
    """R2-03: an explicit non-positive operation bound fails fast —
    zero transport posts, MCP_TIMEOUT semantic end-to-end."""
    posts: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append((url, timeout))
        return FakeResponse()

    creds = FakeCredentialProvider()
    adapter = McpSpecialistAdapter(
        {"davi": _profile()},
        credential_provider=creds,
        transport_factory=lambda p, t: DelpiMcpTransport(
            "http://svc:8000/mcp",
            timeout_seconds=2.0,
            bearer_token=t,
            http_post=http_post,
        ),
    )
    for bound in (0.0, -1.0):
        with pytest.raises(SpecialistInteropError) as exc:
            adapter.list_remote_tools(DAVI, timeout_seconds=bound)
        assert exc.value.code == MCP_TIMEOUT
    assert posts == []


def test_r2_mcp_trickling_body_bounded():
    """Real socket + real requests: a server that trickles body bytes
    forever cannot outlive the operation bound — total wall-clock."""
    import http.server
    import threading

    import requests as _requests

    class TrickleHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(length)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            while True:
                try:
                    self.wfile.write(b"x")
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
                time.sleep(0.05)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), TrickleHandler
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        transport = DelpiMcpTransport(
            f"http://127.0.0.1:{server.server_address[1]}/mcp",
            timeout_seconds=30.0,
            bearer_token=TOKEN,
            http_post=_requests.post,
        )
        started = time.monotonic()
        with pytest.raises(SpecialistInteropError) as exc:
            transport.list_tools(timeout_seconds=0.4)
        assert exc.value.code == MCP_TIMEOUT
        assert time.monotonic() - started < 2.0
    finally:
        server.shutdown()
