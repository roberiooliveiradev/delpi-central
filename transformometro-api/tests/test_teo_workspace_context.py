"""TÉO get_workspace_context — deictic navigation-hint capability.

Contract under test:
- same capability on MCP + GPT Actions (parity via capability_registry);
- bounded projection of the Core workspace_context_v1 payload;
- statuses active/absent/stale/ambiguous mapped deterministically;
- never domain truth, never AuthZ — domain read stays get_process_context;
- no silent fallback to search/recency heuristics.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import patch

from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.gpt_actions.workspace_context_service import (
    WorkspaceContextService,
)


def _service_with(payload: dict) -> WorkspaceContextService:
    class _FakeGateway:
        def get_my_workspace_context(self, authorization, *, app_id="transformometro"):
            assert authorization == "Bearer test"
            assert app_id == "transformometro"
            return payload

    return WorkspaceContextService(gateway=_FakeGateway())


_ACTIVE_CORE_RESPONSE = {
    "status": "active",
    "context": {
        "version": 1,
        "app_id": "transformometro",
        "route_id": "process-workspace",
        "client_instance_id": "tab-1",
        "entity_refs": [
            {"entity_type": "process", "entity_id": "P1"},
            {"entity_type": "instance", "entity_id": "I1"},
            {"entity_type": "revision", "entity_id": "R1"},
        ],
        "presentation_state": {"area": "resultados"},
        "canonical_path": "/apps/transformometro/processes/P1/instances/I1/revisions/R1#resultados",
        "active": True,
        "focused": True,
        "source": "mfe",
        "updated_at": "2025-01-01T10:00:00+00:00",
        "age_seconds": 3,
    },
}


def test_active_context_projects_flat_refs() -> None:
    data = _service_with(_ACTIVE_CORE_RESPONSE).get_workspace_context("Bearer test")
    assert data["status"] == "active"
    assert data["process_id"] == "P1"
    assert data["instance_id"] == "I1"
    assert data["revision_id"] == "R1"
    assert data["area"] == "resultados"
    assert data["canonical_path"].endswith("#resultados")
    assert "get_process_context" in data["next_step"]
    # Never leaks raw store internals or identity.
    assert "client_instance_id" not in data
    assert "user_id" not in data


def test_absent_context_never_fabricates_refs() -> None:
    data = _service_with({"status": "absent"}).get_workspace_context("Bearer test")
    assert data["status"] == "absent"
    assert "process_id" not in data
    assert "never" in data["next_step"].lower() or "nunca" in data["next_step"].lower()


def test_stale_context_marks_stale_not_fresh() -> None:
    payload = {
        "status": "stale",
        "context": _ACTIVE_CORE_RESPONSE["context"],
    }
    data = _service_with(payload).get_workspace_context("Bearer test")
    assert data["status"] == "stale"
    assert data["process_id"] == "P1"  # refs visible but explicitly stale
    assert "stale" in data["next_step"].lower()


def test_ambiguous_context_returns_candidates() -> None:
    payload = {
        "status": "ambiguous",
        "candidates": [
            _ACTIVE_CORE_RESPONSE["context"],
            {
                **_ACTIVE_CORE_RESPONSE["context"],
                "client_instance_id": "tab-2",
                "entity_refs": [{"entity_type": "process", "entity_id": "P2"}],
                "canonical_path": "/apps/transformometro/processes/P2",
            },
        ],
    }
    data = _service_with(payload).get_workspace_context("Bearer test")
    assert data["status"] == "ambiguous"
    assert {c["process_id"] for c in data["candidates"]} == {"P1", "P2"}
    assert "discriminating question" in data["next_step"]


def test_unknown_status_fails_closed_to_absent() -> None:
    data = _service_with({"status": "bogus"}).get_workspace_context("Bearer test")
    assert data["status"] == "absent"


def test_missing_authorization_is_authn_error() -> None:
    import pytest

    with pytest.raises(GptActionsError) as exc:
        _service_with({}).get_workspace_context("")
    assert exc.value.status_code == 401


def test_workspace_tool_bound_on_both_transports() -> None:
    """Same semantic capability on MCP + GPT Actions via the registry."""
    from tm_app.application.intelligence.capability_registry import (
        actions_to_mcp_primary,
    )

    primary = actions_to_mcp_primary()
    assert primary["gpt_get_workspace_context"] == "get_workspace_context"


def test_mcp_surface_includes_workspace_context() -> None:
    from tm_app.interface.mcp.server import create_mcp_server

    tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
    assert "get_workspace_context" in tools
    assert tools["get_workspace_context"].annotations.read_only_hint is True


def test_openapi_operation_present_and_read_only() -> None:
    from tm_app.application.gpt_actions.openapi_builder import (
        build_gpt_actions_openapi,
    )

    doc = build_gpt_actions_openapi()
    ops = {
        o["operationId"]: o
        for s in doc["paths"].values()
        for o in s.values()
        if "operationId" in o
    }
    op = ops["gpt_get_workspace_context"]
    assert op["x-openai-isConsequential"] is False
    assert "AUTHORIZATION" in op["description"]


def test_mcp_tool_returns_structured_payload() -> None:
    """End-to-end through the real bridge (Core call mocked)."""
    import contextlib
    from types import SimpleNamespace

    from delpi_auth.request_context import (
        reset_current_user,
        reset_request_authorization,
        set_current_user,
        set_request_authorization,
    )
    from tm_app.interface.mcp.tool_bridge import tool_get_workspace_context

    user = SimpleNamespace(
        id="u1", email="t@t", name="t", roles=["user"], groups=[], permissions=[]
    )
    ut = set_current_user(user)
    at = set_request_authorization("Bearer test")
    try:
        with contextlib.ExitStack() as stack:
            stack.enter_context(
                patch(
                    "tm_app.interface.mcp.tool_bridge.require_transformometro_view_access",
                    return_value=None,
                )
            )
            stack.enter_context(
                patch(
                    "tm_app.interface.mcp.tool_bridge._workspace_context",
                    _service_with(_ACTIVE_CORE_RESPONSE),
                )
            )
            result = tool_get_workspace_context()
        data = json.loads(result.content[0].text)["data"]
        assert data["status"] == "active"
        assert data["process_id"] == "P1"
    finally:
        reset_request_authorization(at)
        reset_current_user(ut)
