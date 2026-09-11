"""E11.S7 — capability metadata from OpenAPI method/sensitivity."""

from __future__ import annotations

from app.domain.services.chat_capability_discovery_service import (
    ChatCapabilityDiscoveryService,
)


def test_read_get_action_is_low_risk_parallel_safe():
    caps = ChatCapabilityDiscoveryService.capabilities_from_actions(
        [
            {
                "actionId": "acme.stock",
                "method": "GET",
                "sensitivity": "read",
                "summary": "stock",
                "enabled": True,
            }
        ]
    )
    assert len(caps) == 1
    cap = caps[0]
    assert cap["readWrite"] == "read"
    assert cap["risk"] == "low"
    assert cap["parallelSafe"] is True
    assert cap["requiresConfirmation"] is False
    assert cap["contractSource"] == "method+sensitivity"


def test_write_post_action_is_medium_risk_not_parallel():
    caps = ChatCapabilityDiscoveryService.capabilities_from_actions(
        [
            {
                "actionId": "acme.create",
                "method": "POST",
                "sensitivity": "write",
                "summary": "create",
                "enabled": True,
            }
        ]
    )
    cap = caps[0]
    assert cap["readWrite"] == "write"
    assert cap["risk"] == "medium"
    assert cap["parallelSafe"] is False
    assert cap["requiresConfirmation"] is True


def test_destructive_delete_is_high_risk():
    caps = ChatCapabilityDiscoveryService.capabilities_from_actions(
        [
            {
                "actionId": "acme.delete",
                "method": "DELETE",
                "sensitivity": "destructive",
                "summary": "delete",
                "enabled": True,
            }
        ]
    )
    cap = caps[0]
    assert cap["readWrite"] == "write"
    assert cap["risk"] == "high"
    assert cap["parallelSafe"] is False
    assert cap["requiresConfirmation"] is True


def test_unknown_external_action_without_sensitivity_uses_method():
    caps = ChatCapabilityDiscoveryService.capabilities_from_actions(
        [
            {
                "actionId": "vendorx.widget.patch",
                "method": "PATCH",
                "summary": "patch widget",
                "enabled": True,
            }
        ]
    )
    cap = caps[0]
    assert cap["readWrite"] == "write"
    assert cap["risk"] == "medium"
    assert cap["requiresConfirmation"] is True
