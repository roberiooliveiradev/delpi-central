"""Write-governance smoke for TÉO MCP tool bridge (mocked AuthZ context)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.interface.mcp.tool_bridge import (
    tool_commit_improvement_package,
    tool_get_catalog,
    tool_manage_evidence,
    tool_validate_improvement_package,
)


def _auth_user(**kwargs):
    return SimpleNamespace(
        id="u1",
        email="teo@example.com",
        name="Téo",
        roles=[],
        groups=[],
        permissions=kwargs.get("permissions", ["transformometro.view"]),
        is_superadmin=False,
    )


def test_validate_package_is_prepare_no_write_flags_needed():
    user_token = set_current_user(_auth_user())
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._packages.validate",
            return_value={"ready": False, "missing": ["process.nome"]},
        ) as validate:
            result = tool_validate_improvement_package(process={}, instance={})
        assert result.isError is False
        assert result.structuredContent["data"]["ready"] is False
        validate.assert_called_once()
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)


def test_manage_evidence_delete_without_confirm_surfaces_error():
    user_token = set_current_user(_auth_user())
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._dispatch.manage_evidence",
            side_effect=GptActionsError(
                "confirm_delete=true is required for evidence delete.",
                400,
            ),
        ):
            result = tool_manage_evidence(
                scope="process",
                operation="delete",
                parent_id="p1",
                evidence_id="e1",
                confirm_delete=False,
            )
        assert result.isError is True
        assert "confirm_delete" in result.structuredContent["message"]
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)


def test_get_catalog_unauthorized_without_user():
    result = tool_get_catalog()
    assert result.isError is True
    assert result.structuredContent["status_code"] == 401


def test_commit_package_dry_run_stays_prepare_semantics():
    user_token = set_current_user(_auth_user())
    auth_token = set_request_authorization("Bearer test")
    try:
        with patch(
            "tm_app.interface.mcp.tool_bridge._packages.commit",
            return_value={"ready": True, "dry_run": True},
        ) as commit:
            result = tool_commit_improvement_package(
                process={"nome": "X"},
                instance={"filial_id": "filial-01"},
                dry_run=True,
            )
        assert result.isError is False
        assert "pronto" in result.structuredContent["message"].lower() or result.structuredContent[
            "data"
        ].get("ready")
        commit.assert_called_once()
        assert commit.call_args.args[1]["dry_run"] is True
    finally:
        reset_request_authorization(auth_token)
        reset_current_user(user_token)
