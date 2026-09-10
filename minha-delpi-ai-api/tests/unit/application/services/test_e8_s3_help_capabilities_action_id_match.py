"""E8.S3 — help/capabilities: actionId preferido; path substring só fallback."""

from __future__ import annotations

from app.application.security.chat_permissions import CHAT_TOOLS_USE_PERMISSION
from app.application.services.assistant_capabilities_registry import (
    AssistantCapabilitiesRegistry,
)


def _ids(bucket: list[dict]) -> set[str]:
    return {str(item.get("id") or "") for item in bucket}


def test_e8_s3_action_id_token_preferred_over_path():
    """Positive: requiredActions com actionId casa sem path no catalog entry."""

    buckets = AssistantCapabilitiesRegistry.resolve_availability(
        allowed_action_ids=["get_product_stock"],
        action_catalog=[
            {
                "actionId": "get_product_stock",
                "path": "/renamed/inventory-balance",
                "operationId": "get_product_stock",
            }
        ],
        web_search_enabled=True,
        user_permissions={CHAT_TOOLS_USE_PERMISSION},
        can_use_tools=True,
    )
    assert "stock_lookup" in _ids(buckets["availableNow"])


def test_e8_s3_path_substring_fallback_still_works():
    """Sibling: token path legado `/stock` continua válido."""

    buckets = AssistantCapabilitiesRegistry.resolve_availability(
        allowed_action_ids=["legacy_stock_action"],
        action_catalog=[
            {
                "actionId": "legacy_stock_action",
                "path": "/products/{code}/stock",
                "operationId": "legacy_get_stock",
            }
        ],
        web_search_enabled=True,
        user_permissions={CHAT_TOOLS_USE_PERMISSION},
        can_use_tools=True,
    )
    assert "stock_lookup" in _ids(buckets["availableNow"])


def test_e8_s3_unauthorized_action_not_available_now():
    """Negative: action comercial no catalog mas não allowed → não availableNow."""

    buckets = AssistantCapabilitiesRegistry.resolve_availability(
        allowed_action_ids=["get_product_stock"],
        action_catalog=[
            {
                "actionId": "get_product_stock",
                "path": "/products/{code}/stock",
                "operationId": "get_product_stock",
            },
            {
                "actionId": "list_commercial_rol",
                "path": "/commercial/rol",
                "operationId": "list_commercial_rol",
            },
        ],
        web_search_enabled=True,
        user_permissions={CHAT_TOOLS_USE_PERMISSION},
        can_use_tools=True,
    )
    available = _ids(buckets["availableNow"])
    assert "stock_lookup" in available
    assert "commercial_indicators" not in available
    assert "commercial_indicators" in _ids(buckets["requiresPermission"]) or (
        "commercial_indicators" in _ids(buckets["requiresAgent"])
    )


def test_e8_s3_common_chat_without_allowed_goes_requires_agent():
    """Common chat: sem allowed actions → operacional em requiresAgent."""

    buckets = AssistantCapabilitiesRegistry.resolve_availability(
        allowed_action_ids=[],
        action_catalog=[],
        web_search_enabled=True,
        user_permissions={CHAT_TOOLS_USE_PERMISSION},
        can_use_tools=True,
    )
    assert "stock_lookup" in _ids(buckets["requiresAgent"])
    assert "stock_lookup" not in _ids(buckets["availableNow"])
