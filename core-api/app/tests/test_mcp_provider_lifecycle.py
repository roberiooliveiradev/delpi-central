"""Unit tests for MCP provider lifecycle rules."""

from __future__ import annotations

import pytest

from app.domain.mcp_providers.lifecycle import (
    McpProviderLifecycleError,
    after_approve,
    after_enable,
    after_revoke,
    can_transition,
    is_eligible,
    transition,
)


def test_approve_from_discovered():
    status, enabled = after_approve("DISCOVERED")
    assert status == "APPROVED"
    assert enabled is False


def test_enable_requires_approved():
    with pytest.raises(McpProviderLifecycleError) as exc:
        after_enable("DISCOVERED")
    assert exc.value.code == "mcp_provider.enable_not_allowed"


def test_enable_approved_becomes_active():
    status, enabled = after_enable("APPROVED")
    assert status == "ACTIVE"
    assert enabled is True


def test_revoke_blocks_eligibility():
    status, enabled = after_revoke("ACTIVE")
    assert status == "REVOKED"
    assert enabled is False
    assert is_eligible(approval_status=status, enabled=enabled) is False


def test_illegal_transition_revoked_to_active():
    assert can_transition("REVOKED", "ACTIVE") is False
    with pytest.raises(McpProviderLifecycleError):
        transition("REVOKED", "ACTIVE")


def test_eligible_requires_enabled_and_status():
    assert is_eligible(approval_status="APPROVED", enabled=True) is True
    assert is_eligible(approval_status="APPROVED", enabled=False) is False
    assert is_eligible(approval_status="REVOKED", enabled=True) is False
