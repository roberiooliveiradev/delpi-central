import pytest

from app.domain.exceptions.tool_exceptions import ToolPermissionDeniedError
from app.application.security.chat_permissions import CHAT_TOOLS_USE_PERMISSION
from app.domain.services.tool_policy_service import ToolPolicyService


def test_allows_superadmin():
    service = ToolPolicyService()

    assert service.can_execute(
        tool_name="get_allowed_apps",
        required_permission=CHAT_TOOLS_USE_PERMISSION,
        permission_context={
            "is_superadmin": True,
            "permissions": set(),
        },
    )


def test_allows_when_permission_exists():
    service = ToolPolicyService()

    assert service.can_execute(
        tool_name="get_allowed_apps",
        required_permission=CHAT_TOOLS_USE_PERMISSION,
        permission_context={
            "is_superadmin": False,
            "permissions": {CHAT_TOOLS_USE_PERMISSION},
        },
    )


def test_blocks_when_permission_missing():
    service = ToolPolicyService()

    with pytest.raises(ToolPermissionDeniedError):
        service.require_tool_permission(
            tool_name="get_allowed_apps",
            required_permission=CHAT_TOOLS_USE_PERMISSION,
            permission_context={
                "is_superadmin": False,
                "permissions": set(),
            },
        )


def test_sanitize_removes_sensitive_keys():
    service = ToolPolicyService()

    result = service.sanitize_for_llm(
        {
            "name": "Teste",
            "access_token": "secret",
            "nested": {
                "client_secret": "secret",
                "value": 123,
            },
        }
    )

    assert "access_token" not in result
    assert "client_secret" not in result["nested"]
    assert result["nested"]["value"] == 123
