"""GPT Action gpt_get_methodology_guide shares the MCP methodology source."""

from __future__ import annotations

import json

from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID,
    build_gpt_actions_openapi,
    count_operations,
)
from tm_app.application.methodology.guide import query_methodology_guide
from tm_app.interface.mcp.tool_bridge import tool_get_methodology_guide
from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from types import SimpleNamespace
from unittest.mock import patch


def test_openapi_lists_methodology_as_21st_importable_operation() -> None:
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == 18
    assert len(GPT_ACTIONS_OPERATION_IDS) == 18
    assert "gpt_get_methodology_guide" in GPT_ACTIONS_OPERATION_IDS
    assert GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID not in GPT_ACTIONS_OPERATION_IDS
    op = doc["paths"]["/transformometro/gpt-actions/v1/methodology-guide"]["get"]
    assert op["operationId"] == "gpt_get_methodology_guide"
    assert op["x-openai-isConsequential"] is False
    assert len(op["description"]) <= 300
    names = [item["name"] for item in op["parameters"]]
    assert names == ["method", "task"]
    assert all(len(item["description"]) <= 700 for item in op["parameters"])
    ids = [item["operationId"] for path in doc["paths"].values() for item in path.values()]
    assert len(ids) == len(set(ids)) == 18


def test_gpt_methodology_router_and_specific_methods(tm_client) -> None:
    router = tm_client.get("/transformometro/gpt-actions/v1/methodology-guide")
    assert router.status_code == 200
    body = router.json()
    assert body["success"] is True
    assert body["data"]["writes"] is False
    assert body["data"]["read_only"] is True
    assert body["data"]["selection"] == "router"
    assert body["data"] == query_methodology_guide()

    sipoc = tm_client.get(
        "/transformometro/gpt-actions/v1/methodology-guide",
        params={"method": "sipoc"},
    )
    assert sipoc.status_code == 200
    assert sipoc.json()["data"]["method"]["id"] == "sipoc"
    assert sipoc.json()["data"] == query_methodology_guide(method="sipoc")

    diagnosed = tm_client.get(
        "/transformometro/gpt-actions/v1/methodology-guide",
        params={"method": "ishikawa", "task": "diagnose"},
    )
    assert diagnosed.status_code == 200
    payload = diagnosed.json()["data"]
    assert payload["method"]["id"] == "ishikawa"
    assert payload["task"] == "diagnose"
    assert payload["recommended_for_task"] is True
    assert payload["writes"] is False

    for method in ("five_whys", "lean", "kpi"):
        response = tm_client.get(
            "/transformometro/gpt-actions/v1/methodology-guide",
            params={"method": method},
        )
        assert response.status_code == 200
        assert response.json()["data"]["method"]["id"] == method
        blob = json.dumps(response.json())
        assert "client_secret" not in blob
        assert "proposal_handle" not in blob


def test_gpt_methodology_unknown_method_and_task(tm_client) -> None:
    missing = tm_client.get(
        "/transformometro/gpt-actions/v1/methodology-guide",
        params={"method": "get_any_prompt"},
    )
    assert missing.status_code == 400
    assert missing.json()["data"]["error_kind"] == "validation"

    bad_task = tm_client.get(
        "/transformometro/gpt-actions/v1/methodology-guide",
        params={"task": "authorize_write"},
    )
    assert bad_task.status_code == 400
    assert "Unknown methodology task" in bad_task.json()["message"]


def test_gpt_methodology_forbidden_without_view() -> None:
    from tests.support import test_app as support
    from tests.support.test_app import create_test_app
    from starlette.testclient import TestClient

    client = TestClient(create_test_app())
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = []
    try:
        response = client.get(
            "/transformometro/gpt-actions/v1/methodology-guide",
            params={"method": "sipoc"},
        )
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
    assert response.status_code == 403
    assert "sipoc" not in response.json().get("message", "")
    assert (response.json().get("data") or {}).get("method") is None


def test_action_and_mcp_project_the_same_sipoc_playbook() -> None:
    user = SimpleNamespace(
        id="u1",
        email="teo@example.com",
        name="Téo",
        roles=[],
        groups=[],
        permissions=["transformometro.view"],
        is_superadmin=True,
    )
    user_token = set_current_user(user)
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
            return_value=None,
        ):
            mcp = tool_get_methodology_guide(method="sipoc", task="interview")
        assert mcp.isError is False
        assert mcp.structuredContent["data"] == query_methodology_guide(
            method="sipoc",
            task="interview",
        )
        assert mcp.structuredContent["data"]["writes"] is False
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)
