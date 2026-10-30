"""EVA MCP V1 — contract, transport AuthN, business AuthZ and bridge.

Mirrors the TÉO surface gates over the engineering-api MCP (EVA —
Engenharia Virtual Assistida): same delpi_mcp transport, same fail-
closed negatives, same owner model (engineering-api = EVA boundary).
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from delpi_mcp.conformance import McpConformanceConfig, run_mcp_conformance
from delpi_mcp.protocol import DELPI_MCP_PROTOCOL_MINIMUM
from mcp.types import LATEST_PROTOCOL_VERSION

from engineering_app.interface.mcp import tool_bridge as bridge
from engineering_app.interface.mcp.constants import (
    CANONICAL_MCP_RESOURCE_URL,
    DESTRUCTIVE_ACT_TOOLS,
    MCP_PREDEFINED_CLIENT_ID,
    MCP_TOOL_NAMES,
    TOOL_CLASS,
)
from engineering_app.interface.mcp.oauth_contract import (
    EVA_MCP_SECURITY_SCHEMES,
    MCP_OAUTH_SCOPES,
    build_www_authenticate_challenge,
    missing_required_oauth_scopes,
    resolve_required_mcp_resource_audience,
    token_has_exact_audience,
)
from engineering_app.interface.mcp.resource_metadata import (
    build_oauth_protected_resource_metadata,
)
from engineering_app.interface.mcp.server import create_mcp_server
from engineering_app.middleware.auth_middleware import jwt_middleware


def _request(path: str, headers: dict | None = None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (k.lower().encode(), v.encode())
            for k, v in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 123),
        "server": ("test", 443),
    }
    return Request(scope)


def _human_user(permissions=("engineering.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


# --- contract freeze ------------------------------------------------------


def test_contract_freeze() -> None:
    assert CANONICAL_MCP_RESOURCE_URL.endswith("/apps/engineering-api/mcp")
    assert MCP_PREDEFINED_CLIENT_ID == "mcp-engineering"
    assert set(MCP_TOOL_NAMES) == {
        "get_catalog",
        "get_engineering_home",
        "get_engineering_overview",
        "list_lmps",
        "get_lmp_summary",
        "get_lmp_detail",
        "get_lmp_history",
        "get_lmp_goal_context",
        "get_lmp_department_idd",
        "get_lmp_nc_streak",
        "get_product_structure",
        "search_nonconformities",
        "get_nonconformity",
        "get_nonconformity_history",
        "get_nonconformity_indicators",
        "get_nonconformity_tags",
        "get_nonconformity_context",
        "export_nonconformities",
        "prepare_nonconformity_mutation",
        "create_nonconformity",
        "update_nonconformity",
        "delete_nonconformity",
        "import_nonconformities",
    }
    assert all(
        v in {"DISCOVERY", "READ", "PREPARE", "ACT"}
        for v in TOOL_CLASS.values()
    )
    assert DESTRUCTIVE_ACT_TOOLS == frozenset(
        {"delete_nonconformity", "import_nonconformities"}
    )
    assert all(
        TOOL_CLASS[name] == "ACT" for name in DESTRUCTIVE_ACT_TOOLS
    )


def test_scopes_contract() -> None:
    assert "mcp:tools" in MCP_OAUTH_SCOPES
    schemes = EVA_MCP_SECURITY_SCHEMES
    assert schemes[0]["type"] == "oauth2"
    assert set(schemes[0]["scopes"]) == set(MCP_OAUTH_SCOPES)
    # Nenhum RBAC/permission code vaza nos schemes OAuth.
    assert "engineering.access" not in " ".join(schemes[0]["scopes"])


def test_audience_and_scope_helpers() -> None:
    resource = resolve_required_mcp_resource_audience()
    assert token_has_exact_audience({"aud": [resource]}, resource)
    assert token_has_exact_audience(
        {"aud": ["delpi-central", resource]}, resource
    )
    assert not token_has_exact_audience({"aud": ["delpi-central"]}, resource)
    assert missing_required_oauth_scopes(
        {"scope": "openid profile email mcp:tools"}
    ) == []
    assert missing_required_oauth_scopes({"scope": "openid"})


def test_resource_metadata_document() -> None:
    doc = build_oauth_protected_resource_metadata()
    assert doc["resource"] == resolve_required_mcp_resource_audience()
    assert "mcp:tools" in doc["scopes_supported"]


def test_www_authenticate_challenge() -> None:
    challenge = build_www_authenticate_challenge()
    assert challenge.startswith("Bearer ")
    assert "resource_metadata=" in challenge
    assert "mcp:tools" in challenge


# --- list_tools wire surface ----------------------------------------------


def _wire_tools() -> list[dict]:
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    return [
        t.model_dump(mode="json", by_alias=True, exclude_none=True)
        for t in tools
    ]


def test_list_tools_surface() -> None:
    tools = _wire_tools()
    names = {t["name"] for t in tools}
    assert names == set(MCP_TOOL_NAMES)
    for tool in tools:
        assert tool["securitySchemes"][0]["type"] == "oauth2"
        kind = TOOL_CLASS[tool["name"]]
        if kind == "ACT":
            assert tool["annotations"]["readOnlyHint"] is False
        else:
            assert tool["annotations"]["readOnlyHint"] is True
        if tool["name"] in DESTRUCTIVE_ACT_TOOLS:
            assert tool["annotations"]["destructiveHint"] is True
        else:
            assert tool["annotations"]["destructiveHint"] is False


@pytest.fixture(scope="module")
def conformance_report():
    config = McpConformanceConfig(
        name="engineering",
        expected_tool_names=tuple(MCP_TOOL_NAMES),
        expected_tool_count=len(MCP_TOOL_NAMES),
        provider_profile="openai",
        sdk_latest_protocol=LATEST_PROTOCOL_VERSION,
        protocol_minimum=DELPI_MCP_PROTOCOL_MINIMUM,
    )
    return run_mcp_conformance(_wire_tools(), config)


def test_mcp_conformance_no_failures(conformance_report):
    assert conformance_report.failures == [], conformance_report.summary()


def test_mcp_protocol_minimum(conformance_report):
    gate = next(
        r
        for r in conformance_report.results
        if r.gate == "protocol_minimum"
    )
    assert gate.status.value == "PASS"


# --- transport AuthN (middleware) -----------------------------------------


async def test_mcp_path_rejects_missing_bearer() -> None:
    request = _request("/mcp")
    call_next = AsyncMock()
    response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    call_next.assert_not_awaited()


async def test_mcp_path_rejects_missing_resource_audience() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock()
    with patch(
        "engineering_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": ["delpi-central"],
            "scope": "openid profile email mcp:tools",
        },
    ):
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    call_next.assert_not_awaited()


async def test_mcp_path_rejects_missing_mcp_tools_scope() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock()
    with patch(
        "engineering_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": [
                "delpi-central",
                resolve_required_mcp_resource_audience(),
            ],
            "scope": "openid profile email",
        },
    ):
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 401
    call_next.assert_not_awaited()


async def test_mcp_path_rejects_service_token() -> None:
    request = _request("/mcp", {"Authorization": "Bearer svc-token"})
    call_next = AsyncMock()
    with patch(
        "engineering_app.middleware.auth_middleware.request_has_valid_internal_service_token",
        return_value=True,
    ):
        response = await jwt_middleware(request, call_next)
    # Service token é proibido na superfície MCP — fail-closed.
    assert response.status_code == 401
    call_next.assert_not_awaited()


async def test_mcp_path_accepts_valid_token_and_delegates() -> None:
    request = _request("/mcp", {"Authorization": "Bearer tok"})
    call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
    with patch(
        "engineering_app.middleware.auth_middleware.validate_token",
        return_value={
            "aud": [
                "delpi-central",
                resolve_required_mcp_resource_audience(),
            ],
            "scope": "openid profile email mcp:tools",
        },
    ), patch(
        "engineering_app.middleware.auth_middleware._base_jwt_middleware",
        new_callable=AsyncMock,
    ) as base:
        base.return_value = JSONResponse({"ok": True})
        response = await jwt_middleware(request, call_next)
    assert response.status_code == 200
    base.assert_awaited_once()


async def test_oauth_metadata_is_public() -> None:
    request = _request(
        "/apps/engineering-api/.well-known/oauth-protected-resource"
    )
    call_next = AsyncMock(return_value=JSONResponse({"resource": "x"}))
    response = await jwt_middleware(request, call_next)
    assert response.status_code == 200
    call_next.assert_awaited_once()


# --- business AuthZ + tools ------------------------------------------------


def test_catalog_ok() -> None:
    _set_context(_human_user())
    result = bridge.tool_get_catalog()
    assert not result.is_error
    data = result.structured_content["data"]
    assert {t["name"] for t in data["tools"]} == set(MCP_TOOL_NAMES)
    assert set(data["write_tools"]) == {
        name for name, kind in TOOL_CLASS.items() if kind == "ACT"
    }
    assert all(
        p["status"] == "not_implemented"
        for p in data["planned_capabilities"]
    )
    assert all(
        t["required_permission"] == "engineering.access"
        for t in data["tools"]
    )


def test_catalog_forbidden_without_permission() -> None:
    _set_context(_human_user(permissions=()))
    result = bridge.tool_get_catalog()
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_home_requires_human_principal() -> None:
    _set_context(
        _human_user(principal_type="service"), "Bearer svc"
    )
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_home_forbidden_without_permission() -> None:
    _set_context(_human_user(permissions=()))
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_home_unauthenticated_without_context() -> None:
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert result.is_error
    assert result.structured_content["status_code"] == 401


def test_home_delegates_use_case_with_human_token(monkeypatch) -> None:
    _set_context(_human_user())
    captured = {}

    class _FakeUseCase:
        async def execute(self, ctx):
            captured["ctx"] = ctx
            return SimpleNamespace(
                model_dump=lambda: {"status": "available", "sections": []}
            )

    monkeypatch.setattr(
        bridge, "build_get_engineering_home_use_case", lambda: _FakeUseCase()
    )
    result = asyncio.run(bridge.tool_get_engineering_home())
    assert not result.is_error
    assert captured["ctx"].access_token == "human-token"
    assert captured["ctx"].user_id == "user-1"


def test_overview_filter_validation() -> None:
    _set_context(_human_user())
    bad = asyncio.run(
        bridge.tool_get_engineering_overview(start_date="not-a-date")
    )
    assert bad.is_error
    assert bad.structured_content["status_code"] == 400

    inverted = asyncio.run(
        bridge.tool_get_engineering_overview(
            start_date="2026-10-10", end_date="2026-10-01"
        )
    )
    assert inverted.is_error

    bad_competence = asyncio.run(
        bridge.tool_get_engineering_overview(competence="2026/10")
    )
    assert bad_competence.is_error


def test_overview_delegates_filters(monkeypatch) -> None:
    _set_context(_human_user())
    captured = {}

    class _FakeUseCase:
        async def execute(self, ctx, query):
            captured["ctx"] = ctx
            captured["query"] = query
            return SimpleNamespace(
                model_dump=lambda: {"indicators": [], "status": "available"}
            )

    monkeypatch.setattr(
        bridge,
        "build_get_engineering_overview_use_case",
        lambda: _FakeUseCase(),
    )
    result = asyncio.run(
        bridge.tool_get_engineering_overview(
            start_date="2026-10-01",
            end_date="2026-10-31",
            competence="2026-10",
            branch="Matriz",
        )
    )
    assert not result.is_error
    assert captured["query"].start_date == "2026-10-01"
    assert captured["query"].branch == "Matriz"
    assert captured["ctx"].access_token == "human-token"


def test_overview_upstream_error_is_honest(monkeypatch) -> None:
    _set_context(_human_user())

    class _FailingUseCase:
        async def execute(self, ctx, query):
            raise ConnectionError("downstream down")

    monkeypatch.setattr(
        bridge,
        "build_get_engineering_overview_use_case",
        lambda: _FailingUseCase(),
    )
    result = asyncio.run(bridge.tool_get_engineering_overview())
    assert result.is_error
    assert result.structured_content["status_code"] == 502


# --- NC READ tools (E-NC-01..05, E-NC-11) ----------------------------------


def _fake_use_case(result=None, error=None):
    captured = {}

    class _Fake:
        async def execute(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            if error is not None:
                raise error
            return result if result is not None else {"items": []}

    _Fake.captured = captured
    return _Fake()


def test_nc_search_delegates_filters(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"items": [], "total": 0})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_list_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        bridge.tool_search_nonconformities(
            status="open", sale_number="004101", page=2, page_size=10
        )
    )
    assert not result.is_error
    kwargs = fake.captured["kwargs"]
    assert kwargs["status"] == "open"
    assert kwargs["sale_number"] == "004101"
    assert kwargs["page"] == 2


def test_nc_tools_forbidden_without_permission() -> None:
    _set_context(_human_user(permissions=()))
    for call in (
        lambda: bridge.tool_search_nonconformities(),
        lambda: bridge.tool_get_nonconformity(record_id="x"),
        lambda: bridge.tool_get_nonconformity_history(record_id="x"),
        lambda: bridge.tool_get_nonconformity_indicators(),
        lambda: bridge.tool_get_nonconformity_tags(),
        lambda: bridge.tool_get_nonconformity_context(record_id="x"),
    ):
        result = asyncio.run(call())
        assert result.is_error
        assert result.structured_content["status_code"] == 403


def test_nc_tools_reject_service_principal() -> None:
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    result = asyncio.run(bridge.tool_search_nonconformities())
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_nc_tools_unauthenticated_without_context() -> None:
    result = asyncio.run(bridge.tool_get_nonconformity_tags())
    assert result.is_error
    assert result.structured_content["status_code"] == 401


def test_nc_get_maps_not_found(monkeypatch) -> None:
    from engineering_app.domain.nonconformity.errors import NcNotFoundError

    _set_context(_human_user())
    fake = _fake_use_case(error=NcNotFoundError("abc"))
    monkeypatch.setattr(
        bridge.nc_composer, "build_get_nonconformity_use_case", lambda: fake
    )
    result = asyncio.run(bridge.tool_get_nonconformity(record_id="abc"))
    assert result.is_error
    assert result.structured_content["status_code"] == 404


def test_nc_search_maps_unavailable(monkeypatch) -> None:
    from engineering_app.domain.nonconformity.errors import NcRepositoryError

    _set_context(_human_user())
    fake = _fake_use_case(error=NcRepositoryError("db down"))
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_list_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(bridge.tool_search_nonconformities())
    assert result.is_error
    assert result.structured_content["status_code"] == 503


def test_nc_indicators_propagates_human_token(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"current_days_without_nc": 0})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_indicators_use_case",
        lambda: fake,
    )
    result = asyncio.run(bridge.tool_get_nonconformity_indicators())
    assert not result.is_error
    assert fake.captured["kwargs"]["access_token"] == "human-token"


def test_nc_context_propagates_source_context(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"ov_status": "available"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_context_use_case",
        lambda: fake,
    )
    result = asyncio.run(bridge.tool_get_nonconformity_context(record_id="r1"))
    assert not result.is_error
    ctx = fake.captured["args"][0]
    assert ctx.access_token == "human-token"
    assert fake.captured["kwargs"]["record_id"] == "r1"


def test_nc_history_wraps_items(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case([{"event_type": "created"}])
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_list_nonconformity_history_use_case",
        lambda: fake,
    )
    result = asyncio.run(bridge.tool_get_nonconformity_history(record_id="r1"))
    assert not result.is_error
    assert result.structured_content["data"]["items"][0]["event_type"] == "created"


def test_nc_prepare_is_side_effect_free(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case(
        {"valid": True, "side_effects": "none", "projected_changes": {}}
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_prepare_nonconformity_mutation_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        bridge.tool_prepare_nonconformity_mutation(
            operation="create",
            payload={"status": "open", "defect_description": "x"},
        )
    )
    assert not result.is_error
    assert fake.captured["kwargs"]["operation"] == "create"
    assert result.structured_content["data"]["side_effects"] == "none"


def test_nc_prepare_forbidden_without_permission() -> None:
    _set_context(_human_user(permissions=()))
    result = asyncio.run(
        bridge.tool_prepare_nonconformity_mutation(
            operation="create", payload={}
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_prepare_tool_annotations_readonly() -> None:
    tools = _wire_tools()
    prepare = next(t for t in tools if t["name"] == "prepare_nonconformity_mutation")
    assert prepare["annotations"]["readOnlyHint"] is True
    assert prepare["annotations"]["destructiveHint"] is False


# --- ACT tools: gate de ambiente ----------------------------------------


def _enable_act(monkeypatch) -> None:
    monkeypatch.setenv(bridge.EVA_ACT_ENV_FLAG, "true")


def test_act_tools_disabled_without_env_flag(monkeypatch) -> None:
    monkeypatch.delenv(bridge.EVA_ACT_ENV_FLAG, raising=False)
    _set_context(_human_user())
    for call in (
        lambda: bridge.tool_create_nonconformity(
            payload={"status": "open"}, confirmed=True
        ),
        lambda: bridge.tool_update_nonconformity(
            record_id="r1", changes={"status": "done"}, confirmed=True
        ),
        lambda: bridge.tool_delete_nonconformity(
            record_id="r1", confirmed=True
        ),
        lambda: bridge.tool_import_nonconformities(
            items=[{"status": "open"}],
            confirmed=True,
            dry_run=False,
            confirm_replace=True,
        ),
    ):
        result = asyncio.run(call())
        assert result.is_error
        assert result.structured_content["status_code"] == 403
        assert result.structured_content["data"]["error_code"] == "act_disabled"


def test_act_tools_require_human_even_with_flag(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    result = asyncio.run(
        bridge.tool_create_nonconformity(payload={}, confirmed=True)
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_act_tools_forbidden_without_permission(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user(permissions=()))
    result = asyncio.run(
        bridge.tool_delete_nonconformity(record_id="r1", confirmed=True)
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_act_tools_require_confirmation(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    for call in (
        lambda: bridge.tool_create_nonconformity(
            payload={"status": "open"}, confirmed=False
        ),
        lambda: bridge.tool_update_nonconformity(
            record_id="r1", changes={"status": "done"}, confirmed=False
        ),
        lambda: bridge.tool_delete_nonconformity(
            record_id="r1", confirmed=False
        ),
        lambda: bridge.tool_import_nonconformities(
            items=[{"status": "open"}], confirmed=False, dry_run=False
        ),
    ):
        result = asyncio.run(call())
        assert result.is_error
        assert result.structured_content["status_code"] == 400
        assert (
            result.structured_content["data"]["error_code"]
            == "confirmation_required"
        )


# --- ACT tools: execução delegada ----------------------------------------


def test_nc_create_delegates_actor_and_idempotency(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    create = _fake_use_case({"id": "nc-1"})
    get = _fake_use_case({"id": "nc-1", "updated_at": "t2"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_create_nonconformity_use_case",
        lambda: create,
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: get,
    )
    result = asyncio.run(
        bridge.tool_create_nonconformity(
            payload={"status": "open", "defect_description": "x"},
            confirmed=True,
            idempotency_key="k-123",
        )
    )
    assert not result.is_error
    kwargs = create.captured["kwargs"]
    assert kwargs["idempotency_key"] == "k-123"
    assert kwargs["actor"].user_id == "user-1"
    assert kwargs["actor"].email == "user@delpi.test"
    data = result.structured_content["data"]
    assert data["postcondition"]["verified"] is True
    assert data["postcondition"]["record_id"] == "nc-1"


def test_nc_create_honest_when_readback_fails(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    from engineering_app.domain.nonconformity.errors import NcRepositoryError

    create = _fake_use_case({"id": "nc-1"})
    get = _fake_use_case(error=NcRepositoryError("db down"))
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_create_nonconformity_use_case",
        lambda: create,
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: get,
    )
    result = asyncio.run(
        bridge.tool_create_nonconformity(
            payload={"status": "open"}, confirmed=True
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["postcondition"]["verified"] is False


def test_nc_update_merges_full_replace_and_locks(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    current = {
        "id": "r1",
        "status": "open",
        "sale_number": "004101",
        "defect_description": "orig",
        "updated_at": "2025-01-01T00:00:00",
    }
    get = _fake_use_case(current)
    update = _fake_use_case({"id": "r1", "status": "done"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: get,
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_update_nonconformity_use_case",
        lambda: update,
    )
    result = asyncio.run(
        bridge.tool_update_nonconformity(
            record_id="r1",
            changes={"status": "done", "corrective_actions": "fixed"},
            confirmed=True,
        )
    )
    assert not result.is_error
    payload = update.captured["kwargs"]["payload"]
    assert payload["sale_number"] == "004101"
    assert payload["defect_description"] == "orig"
    assert payload["status"] == "done"
    assert payload["corrective_actions"] == "fixed"
    assert (
        update.captured["kwargs"]["expected_updated_at"]
        == "2025-01-01T00:00:00"
    )


def test_nc_update_rejects_unknown_change_keys(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    get = _fake_use_case({"id": "r1", "updated_at": "t1"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: get,
    )
    result = asyncio.run(
        bridge.tool_update_nonconformity(
            record_id="r1", changes={"bogus_field": "x"}, confirmed=True
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 400


def test_nc_update_maps_concurrency_conflict(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    from engineering_app.domain.nonconformity.errors import (
        NcConcurrencyError,
    )

    get = _fake_use_case({"id": "r1", "updated_at": "t1"})
    update = _fake_use_case(error=NcConcurrencyError("stale etag"))
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: get,
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_update_nonconformity_use_case",
        lambda: update,
    )
    result = asyncio.run(
        bridge.tool_update_nonconformity(
            record_id="r1", changes={"status": "done"}, confirmed=True
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 409
    assert (
        result.structured_content["data"]["error_code"]
        == "concurrency_conflict"
    )


def test_nc_delete_verifies_postcondition(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    from engineering_app.domain.nonconformity.errors import NcNotFoundError

    calls = {"n": 0}

    class _GetSequence:
        async def execute(self, record_id):
            calls["n"] += 1
            if calls["n"] == 1:
                return {"id": record_id, "sale_number": "004101"}
            raise NcNotFoundError(record_id)

    delete = _fake_use_case({"id": "r1", "deleted": True})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _GetSequence(),
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_delete_nonconformity_use_case",
        lambda: delete,
    )
    result = asyncio.run(
        bridge.tool_delete_nonconformity(record_id="r1", confirmed=True)
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["deleted"] is True
    assert data["postcondition"]["verified"] is True
    assert data["deleted_record_summary"]["sale_number"] == "004101"


def test_nc_delete_not_found_is_honest(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    from engineering_app.domain.nonconformity.errors import NcNotFoundError

    get = _fake_use_case(error=NcNotFoundError("r1"))
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: get,
    )
    result = asyncio.run(
        bridge.tool_delete_nonconformity(record_id="r1", confirmed=True)
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 404


def test_nc_import_dry_run_without_confirmation(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())

    class _Result:
        def to_dict(self):
            return {
                "deleted": 0,
                "created": 2,
                "skipped": 0,
                "errors": 0,
                "items": [],
            }

    fake = _fake_use_case(_Result())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_import_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        bridge.tool_import_nonconformities(
            items=[{"status": "open"}], confirmed=False, dry_run=True
        )
    )
    assert not result.is_error
    kwargs = fake.captured["kwargs"]
    assert kwargs["dry_run"] is True
    assert kwargs["confirm_replace"] is False


def test_nc_import_replace_requires_confirmation(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    result = asyncio.run(
        bridge.tool_import_nonconformities(
            items=[{"status": "open"}],
            confirmed=False,
            dry_run=False,
            confirm_replace=True,
        )
    )
    assert result.is_error
    assert (
        result.structured_content["data"]["error_code"]
        == "confirmation_required"
    )


def test_nc_import_maps_unsafe_operation(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    from engineering_app.domain.nonconformity.errors import (
        NcUnsafeOperationError,
    )

    fake = _fake_use_case(
        error=NcUnsafeOperationError("confirm_replace obrigatório")
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_import_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        bridge.tool_import_nonconformities(
            items=[{"status": "open"}],
            confirmed=True,
            dry_run=False,
            confirm_replace=False,
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_nc_export_delegates(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"version": "1", "count": 3, "items": []})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_export_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(bridge.tool_export_nonconformities())
    assert not result.is_error
    assert result.structured_content["data"]["count"] == 3


# --- READ tools: LMPs e produtos ------------------------------------------


def test_list_lmps_delegates_filters_and_token(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"items": [], "total": 0})
    monkeypatch.setattr(
        bridge,
        "build_list_lmps_dashboard_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        bridge.tool_list_lmps(
            start_date="2025-01-01",
            end_date="2025-01-31",
            branch="filial-01",
            status="late",
            page=2,
            page_size=10,
        )
    )
    assert not result.is_error
    ctx, query = fake.captured["args"]
    assert ctx.access_token == "human-token"
    assert query.start_date == "2025-01-01"
    assert query.status_filter == "late"
    assert query.page == 2


def test_list_lmps_validates_period() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        bridge.tool_list_lmps(
            start_date="2025-02-01", end_date="2025-01-01"
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 400


def test_lmp_detail_maps_not_found(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"status": "not_found"})
    monkeypatch.setattr(
        bridge, "build_get_lmp_detail_use_case", lambda: fake
    )
    result = asyncio.run(bridge.tool_get_lmp_detail(sale_number="004101"))
    assert result.is_error
    assert result.structured_content["status_code"] == 404


def test_lmp_detail_maps_forbidden(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"status": "forbidden"})
    monkeypatch.setattr(
        bridge, "build_get_lmp_detail_use_case", lambda: fake
    )
    result = asyncio.run(bridge.tool_get_lmp_detail(sale_number="004101"))
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_lmp_history_requires_valid_view(monkeypatch) -> None:
    _set_context(_human_user())
    seen = {"built": False}

    def _builder(view):
        seen["built"] = True
        return _fake_use_case({})

    monkeypatch.setattr(bridge, "build_get_lmp_history_use_case", _builder)
    result = asyncio.run(
        bridge.tool_get_lmp_history(sale_number="004101", view="bogus")
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 400
    assert seen["built"] is False


def test_lmp_history_delegates_view(monkeypatch) -> None:
    _set_context(_human_user())
    built = {}
    fake = _fake_use_case({"events": []})

    def _builder(view):
        built["view"] = view
        return fake

    monkeypatch.setattr(bridge, "build_get_lmp_history_use_case", _builder)
    result = asyncio.run(
        bridge.tool_get_lmp_history(
            sale_number="004101", view="flow", revision="3"
        )
    )
    assert not result.is_error
    assert built["view"] == "flow"
    _, query = fake.captured["args"]
    assert query.sale_number == "004101"
    assert query.revision == "3"


def test_lmp_auxiliary_tools_delegate_source_context(monkeypatch) -> None:
    _set_context(_human_user())

    class _Aux:
        calls = {}

        async def fetch_goal_context(self, ctx, **kw):
            self.calls["goal"] = (ctx, kw)
            return {"status": "available"}

        async def fetch_department_idd(self, ctx, **kw):
            self.calls["idd"] = (ctx, kw)
            return {"status": "available"}

        async def fetch_nc_streak(self, ctx):
            self.calls["streak"] = ctx
            return {"status": "available"}

        async def fetch_product_structure(self, ctx, **kw):
            self.calls["product"] = (ctx, kw)
            return {"status": "available"}

    aux = _Aux()
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: aux
    )
    asyncio.run(bridge.tool_get_lmp_goal_context())
    asyncio.run(bridge.tool_get_lmp_department_idd(competence="2025-01"))
    asyncio.run(bridge.tool_get_lmp_nc_streak())
    asyncio.run(bridge.tool_get_product_structure(product_code="P-10"))
    assert aux.calls["goal"][0].access_token == "human-token"
    assert aux.calls["idd"][1]["competence"] == "2025-01"
    assert aux.calls["streak"].access_token == "human-token"
    assert aux.calls["product"][1]["code"] == "P-10"


def test_product_structure_validates_code() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        bridge.tool_get_product_structure(product_code="  ")
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 400


def test_lmp_tools_reject_service_principal() -> None:
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    for call in (
        lambda: bridge.tool_list_lmps(),
        lambda: bridge.tool_get_lmp_summary(),
        lambda: bridge.tool_get_product_structure(product_code="P-1"),
        lambda: bridge.tool_export_nonconformities(),
    ):
        result = asyncio.run(call())
        assert result.is_error
        assert result.structured_content["status_code"] == 403


def test_act_tool_annotations() -> None:
    tools = _wire_tools()
    for name in ("create_nonconformity", "update_nonconformity"):
        tool = next(t for t in tools if t["name"] == name)
        assert tool["annotations"]["readOnlyHint"] is False
        assert tool["annotations"]["destructiveHint"] is False
    for name in ("delete_nonconformity", "import_nonconformities"):
        tool = next(t for t in tools if t["name"] == name)
        assert tool["annotations"]["readOnlyHint"] is False
        assert tool["annotations"]["destructiveHint"] is True


def test_catalog_reports_act_surface_and_gate(monkeypatch) -> None:
    monkeypatch.delenv(bridge.EVA_ACT_ENV_FLAG, raising=False)
    _set_context(_human_user())
    result = bridge.tool_get_catalog()
    data = result.structured_content["data"]
    assert data["act_enabled"] is False
    assert set(data["write_tools"]) == {
        "create_nonconformity",
        "update_nonconformity",
        "delete_nonconformity",
        "import_nonconformities",
    }
    by_name = {t["name"]: t for t in data["tools"]}
    assert by_name["delete_nonconformity"]["destructive"] is True
    assert by_name["create_nonconformity"]["requires_human_confirmation"]
    assert by_name["search_nonconformities"]["read_only"] is True
