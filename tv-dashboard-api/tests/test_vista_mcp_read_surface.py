"""MCP1 — VISTA READ surface (Streamable HTTP / FastMCP adapter).

Coverage: tool surface exactness, OAuth transport (401 challenge, service
token forbidden, audience/scope gates), context bridge → dispatch delegation,
typed error preservation, non-persistence, trailing-slash rewrite, and the
canonical ROL preview value (~2.6667) through the real application runtime.

MCP is an adapter: every tool delegates to ``GptActionsDispatchService`` —
no duplicated AuthZ, business logic, or persistence lives in the MCP layer.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from test_data_model_foundation import (
    _enrichment,
    _gateway_by_preset,
    _rol_model,
    _rol_payload,
)

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.asgi import mcp_mount_path_middleware
from tv_app.interface.mcp.constants import (
    MCP_FORBIDDEN_TOOLS,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
from tv_app.interface.mcp.oauth_contract import (
    build_www_authenticate_challenge,
    resolve_required_mcp_resource_audience,
)
from tv_app.interface.mcp.resource_metadata import (
    build_protected_resource_document,
    protected_resource_metadata_url,
)
from tv_app.interface.mcp.server import create_mcp_server
from tv_app.middleware.auth_middleware import (
    _is_mcp_data_path,
    jwt_middleware,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _viewer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read"],
        roles=[],
        groups=[],
        id="viewer-1",
        email="viewer@delpi.local",
    )


def _request(path: str, headers: dict[str, str] | None = None) -> Request:
    raw = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": raw,
        "query_string": b"",
        "root_path": "",
        "state": {},
    }
    return Request(scope)


class _ctx:
    """ContextVar auth context for bridge tests."""

    def __init__(self, user=None, authorization: str | None = "Bearer test"):
        self.user = user
        self.authorization = authorization
        self._u = None
        self._a = None

    def __enter__(self):
        if self.user is not None:
            self._u = set_current_user(self.user)
        self._a = set_request_authorization(self.authorization)
        return self

    def __exit__(self, *exc):
        if self._u is not None:
            reset_current_user(self._u)
        if self._a is not None:
            reset_request_authorization(self._a)


def _test_dispatch(**overrides) -> GptActionsDispatchService:
    """Real dispatch with mocked persistence ports (unit-level)."""
    kwargs = dict(repo=MagicMock(), writes=MagicMock(), commit=MagicMock())
    kwargs.update(overrides)
    return GptActionsDispatchService(**kwargs)


# ---------------------------------------------------------------------------
# Surface exactness + classification
# ---------------------------------------------------------------------------


def test_tools_list_exactly_eight_governed_tools():
    tools = asyncio.run(create_mcp_server().list_tools())
    names = {t.name for t in tools}
    assert names == set(MCP_TOOL_NAMES)
    assert names == {
        "list_playlists",
        "get_playlist_context",
        "get_catalog",
        "search_data_routes",
        "inspect_data_model",
        "preview_data_model",
        "prepare_change",
        "commit_proposal",
    }
    assert len(tools) == 8
    assert "inspect_data_source" not in names


def test_no_native_op_or_legacy_tools_registered():
    names = {t.name for t in asyncio.run(create_mcp_server().list_tools())}
    assert MCP_FORBIDDEN_TOOLS.isdisjoint(names)
    banned = {"preview_change", "commit_change", "suggest_change", "preview_data_block",
              "upsert_data_model", "bind_visual", "migrate_data_sources_to_model",
              "execute_capability", "generic_http"}
    assert banned.isdisjoint(names)


def test_tool_classification_read_prepare_act():
    assert TOOL_CLASS["prepare_change"] == "PREPARE"
    assert TOOL_CLASS["commit_proposal"] == "ACT"
    assert sum(1 for v in TOOL_CLASS.values() if v == "READ") == 6
    assert set(TOOL_CLASS.keys()) == set(MCP_TOOL_NAMES)


def test_tool_annotations_match_class():
    tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
    for name, t in tools.items():
        ann = t.annotations
        assert ann is not None, name
        if TOOL_CLASS[name] == "READ":
            assert ann.read_only_hint is True, name
            assert ann.destructive_hint in (False, None), name
        elif TOOL_CLASS[name] == "PREPARE":
            assert ann.read_only_hint is False, name
            assert ann.destructive_hint is False, name
        else:  # ACT
            assert ann.read_only_hint is False, name
            assert ann.destructive_hint is True, name
            assert ann.idempotent_hint is True, name


def test_no_resources_or_prompts_registered():
    mcp = create_mcp_server()
    assert asyncio.run(mcp.list_resources()) == []
    assert asyncio.run(mcp.list_prompts()) == []


# ---------------------------------------------------------------------------
# OAuth transport — middleware gates
# ---------------------------------------------------------------------------


def test_mcp_path_detection():
    assert _is_mcp_data_path("/mcp")
    assert _is_mcp_data_path("/mcp/")
    assert _is_mcp_data_path("/apps/tv-dashboard-api/mcp")
    assert _is_mcp_data_path("/apps/tv-dashboard-api/mcp/")
    assert not _is_mcp_data_path("/gpt-actions/v1/dispatch")
    assert not _is_mcp_data_path("/.well-known/oauth-protected-resource")


def test_mcp_unauthenticated_401_challenge():
    request = _request("/mcp")
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    response = asyncio.run(jwt_middleware(request, call_next))
    assert response.status_code == 401
    www = response.headers.get("www-authenticate") or ""
    assert 'resource_metadata="' in www
    assert 'realm="mcp"' in www
    call_next.assert_not_awaited()


def test_mcp_service_token_forbidden():
    request = _request("/mcp", {"Authorization": "Bearer svc"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "tv_app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=True,
    ):
        response = asyncio.run(jwt_middleware(request, call_next))
    assert response.status_code == 401
    call_next.assert_not_awaited()


def test_mcp_requires_resource_audience():
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "tv_app.middleware.auth_middleware.validate_token",
        return_value={"aud": ["delpi-central"], "scope": "openid profile email mcp:tools"},
    ):
        response = asyncio.run(jwt_middleware(request, call_next))
    assert response.status_code == 401
    call_next.assert_not_awaited()


def test_mcp_requires_generic_scopes():
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "tv_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": ["delpi-central", resolve_required_mcp_resource_audience()],
            "scope": "openid profile email",
        },
    ):
        response = asyncio.run(jwt_middleware(request, call_next))
    assert response.status_code == 401
    call_next.assert_not_awaited()


def test_mcp_valid_token_delegates_to_base_middleware():
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "tv_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": ["delpi-central", resolve_required_mcp_resource_audience()],
            "scope": "openid profile email mcp:tools",
        },
    ), patch(
        "tv_app.middleware.auth_middleware._base_jwt_middleware",
        new_callable=AsyncMock,
    ) as base:
        base.return_value = JSONResponse({"ok": True})
        response = asyncio.run(jwt_middleware(request, call_next))
    assert response.status_code == 200
    base.assert_awaited_once()


def test_oauth_metadata_route_is_public():
    request = _request("/.well-known/oauth-protected-resource")
    call_next = AsyncMock(return_value=JSONResponse({"resource": "x"}))
    response = asyncio.run(jwt_middleware(request, call_next))
    assert response.status_code == 200
    call_next.assert_awaited_once()


# ---------------------------------------------------------------------------
# OAuth metadata document + challenge
# ---------------------------------------------------------------------------


def test_protected_resource_document_shape():
    doc = build_protected_resource_document("http://testserver")
    assert doc["resource"] == resolve_required_mcp_resource_audience()
    assert doc["resource"].endswith("/mcp")
    assert "mcp:tools" in doc["scopes_supported"]
    # audience-delpi (internal mapper) must never be advertised as a scope
    assert not any("audience" in s for s in doc["scopes_supported"])
    assert doc["bearer_methods_supported"] == ["header"]
    assert isinstance(doc.get("authorization_servers"), list)


def test_www_authenticate_challenge_targets_metadata_url():
    challenge = build_www_authenticate_challenge()
    meta = protected_resource_metadata_url()
    assert meta in challenge
    assert 'scope="mcp:tools"' in challenge


# ---------------------------------------------------------------------------
# Context bridge → dispatch delegation
# ---------------------------------------------------------------------------


def test_list_playlists_delegates_to_dispatch():
    expected = {"items": [{"id": "p1", "title": "DM5 Acceptance"}], "pagination": {"total": 1}}
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch, "list_playlists", return_value=expected
    ) as fn:
        result = tool_bridge.tool_list_playlists(limit=10, offset=0)
    assert result.is_error is False
    fn.assert_called_once()
    assert result.structured_content["status"] == "success"
    assert result.structured_content["data"]["items"][0]["id"] == "p1"


def test_identity_propagates_to_dispatch():
    user = _viewer()
    seen = {}

    def _capture(*, user, limit, offset):  # noqa: A002 — signature mirrors dispatch
        seen["user"] = user
        return {"items": []}

    with _ctx(user), patch.object(tool_bridge._dispatch, "list_playlists", side_effect=_capture):
        result = tool_bridge.tool_list_playlists()
    assert result.is_error is False
    assert seen["user"] is user
    assert seen["user"].id == "viewer-1"


def test_unauthenticated_tool_call_401():
    with _ctx(None, None):
        result = tool_bridge.tool_list_playlists()
    assert result.is_error is True
    body = result.structured_content
    assert body["httpStatus"] == 401
    assert body["code"] == "AUTHENTICATION_REQUIRED"
    meta = getattr(result, "meta", None) or {}
    assert "mcp/www_authenticate" in meta


def test_get_playlist_context_delegates():
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch,
        "get_playlist_context",
        return_value={"playlist": {"id": "p1"}, "slides": []},
    ) as fn:
        result = tool_bridge.tool_get_playlist_context(
            playlist_id="850d110a-4ec8-4fe8-91be-225f1dcfcf0e", scope="full"
        )
    assert result.is_error is False
    kwargs = fn.call_args.kwargs
    assert kwargs["playlist_id"] == "850d110a-4ec8-4fe8-91be-225f1dcfcf0e"
    assert kwargs["scope"] == "full"


def test_get_catalog_delegates():
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch, "get_catalog", return_value={"operations": ["x"]}
    ) as fn:
        result = tool_bridge.tool_get_catalog()
    assert result.is_error is False
    fn.assert_called_once()


def test_get_catalog_write_permission_preserved_as_403():
    """get_catalog asserts TV_WRITE in the application layer — the adapter must
    not reinterpret it; viewer without write gets a structured 403."""
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch,
        "get_catalog",
        side_effect=PermissionError("Você não tem permissão para esta ação."),
    ):
        result = tool_bridge.tool_get_catalog()
    assert result.is_error is True
    assert result.structured_content["httpStatus"] == 403


def test_search_data_routes_delegates_and_preserves_validation():
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch,
        "search_data_routes",
        side_effect=GptActionsError("Informe uma busca.", code="QUERY_REQUIRED", status_code=422),
    ):
        result = tool_bridge.tool_search_data_routes(query="")
    assert result.is_error is True
    assert result.structured_content["code"] == "QUERY_REQUIRED"
    assert result.structured_content["httpStatus"] == 422


def test_inspect_data_model_passes_authorization_from_context():
    seen = {}

    def _capture(*, user, playlist_id, slide_id, model_id, authorization, include_runtime):
        seen["authorization"] = authorization
        return {"definition": {"id": model_id}}

    with _ctx(_viewer(), "Bearer user-token-abc"), patch.object(
        tool_bridge._dispatch, "inspect_data_model", side_effect=_capture
    ):
        result = tool_bridge.tool_inspect_data_model(
            playlist_id="p", slide_id="s", model_id="mdl_14b3b212b2"
        )
    assert result.is_error is False
    assert seen["authorization"] == "Bearer user-token-abc"


def test_inspect_model_not_found_preserves_domain_code():
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch,
        "inspect_data_model",
        side_effect=GptActionsError(
            "DataModel não encontrado.",
            code="data_model.not_found",
            status_code=404,
            details={"modelId": "mdl_x"},
        ),
    ):
        result = tool_bridge.tool_inspect_data_model(playlist_id="p", slide_id="s", model_id="m")
    assert result.is_error is True
    body = result.structured_content
    assert body["code"] == "data_model.not_found"
    assert body["httpStatus"] == 404
    assert body["details"] == {"modelId": "mdl_x"}
    assert "Traceback" not in json.dumps(body)


def test_unauthorized_playlist_fails_closed():
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch,
        "get_playlist_context",
        side_effect=GptActionsError(
            "Programação não encontrada.", code="RESOURCE_NOT_FOUND", status_code=404
        ),
    ):
        result = tool_bridge.tool_get_playlist_context(playlist_id="other-tenant")
    assert result.is_error is True
    assert result.structured_content["code"] == "RESOURCE_NOT_FOUND"
    assert "slides" not in result.structured_content.get("data", {})


def test_internal_error_no_stack_leak():
    with _ctx(_viewer()), patch.object(
        tool_bridge._dispatch, "list_playlists", side_effect=RuntimeError("db conn secret")
    ):
        result = tool_bridge.tool_list_playlists()
    assert result.is_error is True
    body = result.structured_content
    assert body["code"] == "INTERNAL_ERROR"
    assert "db conn secret" not in json.dumps(body)


# ---------------------------------------------------------------------------
# preview_data_model — real runtime, non-persistence, ROL value
# ---------------------------------------------------------------------------


def _preview_dispatch_with_gateway(gateway) -> GptActionsDispatchService:
    preview = TvDataPreviewService()
    preview._resolution = _enrichment(gateway)
    return _test_dispatch(preview=preview)


def _inline_model_body():
    model = _rol_model()
    return {
        "version": 5,
        "blocks": [],
        "dataModels": [model],
    }, model


def test_preview_data_model_rol_value_through_mcp():
    gateway = _gateway_by_preset(
        {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
    )
    dispatch = _preview_dispatch_with_gateway(gateway)
    cfg, model = _inline_model_body()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_preview_data_model(model=model)
    assert result.is_error is False
    data = result.structured_content["data"]
    resolved = data["resolved"]
    rows = (resolved.get("table") or {}).get("rows") or []
    assert rows, "preview should materialize rows"
    assert rows[0].get("value") == pytest.approx(2.6667, abs=0.01)


def test_preview_inline_candidate_not_persisted():
    gateway = _gateway_by_preset(
        {"previous": _rol_payload(4399153.22), "current": _rol_payload(4516461.10)}
    )
    dispatch = _preview_dispatch_with_gateway(gateway)
    cfg, model = _inline_model_body()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_preview_data_model(model=model)
    assert result.is_error is False
    # No persistence port touched by the inline preview path.
    assert dispatch._repo.method_calls == []
    assert dispatch._writes.method_calls == []
    assert dispatch._commit.method_calls == []


def test_preview_requires_model_or_model_id():
    with _ctx(_viewer()):
        result = tool_bridge.tool_preview_data_model()
    assert result.is_error is True
    assert result.structured_content["code"] == "INVALID_CHANGE"
    assert result.structured_content["httpStatus"] == 422


# ---------------------------------------------------------------------------
# Trailing slash / mount rewrite
# ---------------------------------------------------------------------------


def test_mcp_exact_path_rewritten_for_mount():
    request = _request("/mcp")
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    asyncio.run(mcp_mount_path_middleware(request, call_next))
    assert request.scope["path"] == "/mcp/"


def test_mcp_gateway_prefixed_path_rewritten():
    request = _request("/apps/tv-dashboard-api/mcp")
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    asyncio.run(mcp_mount_path_middleware(request, call_next))
    assert request.scope["path"] == "/apps/tv-dashboard-api/mcp/"


def test_mcp_trailing_path_untouched_for_non_mcp():
    request = _request("/gpt-actions/v1/dispatch")
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    asyncio.run(mcp_mount_path_middleware(request, call_next))
    assert request.scope["path"] == "/gpt-actions/v1/dispatch"


# ---------------------------------------------------------------------------
# Write-tool absence + app wiring
# ---------------------------------------------------------------------------


def test_calling_forbidden_tool_fails_tool_not_found():
    from mcp.server.mcpserver.exceptions import ToolError

    mcp = create_mcp_server()
    with pytest.raises(ToolError, match="upsert_data_model"):
        asyncio.run(mcp.call_tool("upsert_data_model", {}))
    with pytest.raises(ToolError, match="migrate_data_sources_to_model"):
        asyncio.run(mcp.call_tool("migrate_data_sources_to_model", {}))


def test_app_mounts_mcp_and_metadata_and_health():
    from tv_app.main import app

    mounts = [getattr(r, "path", "") for r in app.routes if type(r).__name__ == "Mount"]
    assert "/mcp" in mounts
    included = [r for r in app.routes if type(r).__name__ == "_IncludedRouter"]
    well_known = [
        getattr(x, "path", "")
        for r in included
        for x in getattr(r, "original_router", MagicMock(routes=[])).routes
    ]
    assert any(p.startswith("/.well-known/oauth-protected-resource") for p in well_known)
    api_paths = [getattr(r, "path", "") for r in app.routes]
    assert "/health" in api_paths


# ---------------------------------------------------------------------------
# Modern protocol era (2026-07-28) — regression for the ChatGPT discovery
# failure: SDK 1.30 rejected non-initialize requests carrying
# ``MCP-Protocol-Version: 2026-07-28`` with HTTP 400
# "Unsupported protocol version". With mcp>=2 the modern era is served
# natively on the same streamable endpoint (no fallback required).
# ---------------------------------------------------------------------------

_MODERN_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
    "MCP-Protocol-Version": "2026-07-28",
}
_MODERN_META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientCapabilities": {},
}


async def _mcp_post(client, payload, headers=None):
    return await client.post("/", json=payload, headers=headers or {})


def test_modern_era_tools_list_served_natively():
    """Modern-era request envelope (MCP-Method header + params._meta) → 200.

    Regression: this class of request returned HTTP 400 under mcp 1.30.
    """
    import httpx

    from tv_app.interface.mcp.asgi import mcp_http_app

    async def _run():
        mcp = create_mcp_server()
        app = mcp_http_app(mcp)
        async with mcp.session_manager.run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://localhost"
            ) as client:
                headers = {**_MODERN_HEADERS, "MCP-Method": "tools/list"}
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {"_meta": dict(_MODERN_META)},
                }
                return await _mcp_post(client, payload, headers)

    resp = asyncio.run(_run())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "error" not in body, body
    tools = body["result"]["tools"]
    assert {t["name"] for t in tools} == set(MCP_TOOL_NAMES)


def test_tool_meta_keys_are_vendor_namespaced():
    """Bare `securitySchemes` in tool _meta is a reserved key for the OpenAI
    connector (parsed as typed OAuthSecurityScheme objects) — string values
    there broke ChatGPT action discovery. Vendor keys must stay `delpi/*`."""
    tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
    for name, t in tools.items():
        meta = t.meta or {}
        assert "securitySchemes" not in meta, name
        assert "toolClass" not in meta, name
        assert meta.get("delpi/toolClass") == TOOL_CLASS[name], name
        assert meta.get("delpi/securitySchemes"), name


def test_modern_protocol_header_does_not_emit_unsupported_version_400():
    """A request under the modern era must never fail with the v1-era
    'Unsupported protocol version' 400 (the exact production failure)."""
    import httpx

    from tv_app.interface.mcp.asgi import mcp_http_app

    async def _run():
        mcp = create_mcp_server()
        app = mcp_http_app(mcp)
        async with mcp.session_manager.run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://localhost"
            ) as client:
                return await _mcp_post(
                    client,
                    {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                    _MODERN_HEADERS,
                )

    resp = asyncio.run(_run())
    assert "Unsupported protocol version" not in resp.text


def test_legacy_initialize_still_accepted():
    """Handshake-era initialize (no MCP-Protocol-Version header) → 200."""
    import httpx

    from tv_app.interface.mcp.asgi import mcp_http_app

    async def _run():
        mcp = create_mcp_server()
        app = mcp_http_app(mcp)
        async with mcp.session_manager.run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://localhost"
            ) as client:
                return await _mcp_post(
                    client,
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-06-18",
                            "capabilities": {},
                            "clientInfo": {"name": "regression", "version": "0"},
                        },
                    },
                    {
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                    },
                )

    resp = asyncio.run(_run())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["result"]["serverInfo"]["name"] == "tv-dashboard"
