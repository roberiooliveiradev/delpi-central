"""MCP adapter + transport tests — C3-MCP-INTEROP-01.

Mock transport + fake HTTP: proves the second fail-closed boundary
(invocation re-check), profile gating (not configured / disabled / no
delegated credential), error normalization, size bound, timeout mapping,
session echo, and bounded outcome mapping. No real network.
"""

from __future__ import annotations

import json
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
    WRITE_CAPABILITY_BLOCKED,
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


def _profile(**overrides):
    values = {
        "endpoint": "http://svc:8000/mcp",
        "enabled": True,
        "timeout_seconds": 5.0,
        "user_token": TOKEN,
    }
    values.update(overrides)
    return SpecialistConnectionProfile(**values)


class FakeTransport:
    """Records calls; scripted results."""

    instances: list["FakeTransport"] = []

    def __init__(self, profile, tools=(), call_result=None):
        self.profile = profile
        self.tools = tools
        self.call_result = call_result or {"content": []}
        self.initialized = False
        self.calls: list[tuple] = []
        FakeTransport.instances.append(self)

    def initialize(self):
        self.initialized = True

    def list_tools(self):
        return self.tools

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        return self.call_result


def _adapter(tools=(), call_result=None, **profile_overrides):
    def factory(profile):
        return FakeTransport(profile, tools=tools, call_result=call_result)

    return McpSpecialistAdapter(
        {"davi": _profile(**profile_overrides)}, transport_factory=factory
    )


def test_list_remote_tools_maps_wire_metadata():
    FakeTransport.instances.clear()
    adapter = _adapter(
        tools=(
            {
                "name": "discover_delpi_information",
                "description": "d",
                "inputSchema": {"type": "object"},
            },
            {"name": "execute_delpi_information"},
        )
    )
    tools = adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert [t.remote_name for t in tools] == [
        "discover_delpi_information",
        "execute_delpi_information",
    ]
    assert tools[0].input_schema == {"type": "object"}
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
    adapter = _adapter(user_token=None)
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.list_remote_tools(DAVI, timeout_seconds=5.0)
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert FakeTransport.instances == []


def test_call_rechecks_allowlist_before_wire():
    FakeTransport.instances.clear()
    adapter = _adapter()
    for name, code in (
        ("commit_proposal_evil", UNKNOWN_CAPABILITY),
        ("execute_delpi_information", CAPABILITY_NOT_ALLOWED_IN_PHASE),
        ("prepare_x", UNKNOWN_CAPABILITY),
    ):
        with pytest.raises(SpecialistInteropError) as exc:
            adapter.call_remote_tool(
                DAVI, name, {}, correlation_id="c", timeout_seconds=5.0
            )
        assert exc.value.code == code
    assert FakeTransport.instances == []


def test_call_write_class_blocked_even_with_valid_config():
    adapter = McpSpecialistAdapter(
        {"teo": _profile()},
        transport_factory=lambda p: FakeTransport(p),
    )
    teo = SpecialistRef(
        specialist_id="teo", display_name="TEO", owner_ref="transformometro-api"
    )
    with pytest.raises(SpecialistInteropError) as exc:
        adapter.call_remote_tool(
            teo, "commit_proposal", {}, correlation_id="c", timeout_seconds=5.0
        )
    assert exc.value.code == WRITE_CAPABILITY_BLOCKED


def test_call_maps_bounded_outcome():
    adapter = _adapter(
        call_result={
            "content": [{"type": "text", "text": "hello"}],
            "structuredContent": {"candidates": []},
            "isError": False,
        }
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
        call_result={
            "content": [{"type": "text", "text": "denied"}],
            "isError": True,
        }
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

    def http_post(url, headers=None, data=None, timeout=None):
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
