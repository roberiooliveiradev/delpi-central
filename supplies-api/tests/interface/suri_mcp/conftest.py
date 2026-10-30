"""SURI MCP test fixtures — thin pytest wrappers over suri_fixtures."""

from __future__ import annotations

import pytest
from suri_mcp.suri_fixtures import FakeGateway, make_context, make_user_ns

from app.interfaces.mcp import tool_bridge


@pytest.fixture()
def access_context(monkeypatch):
    """Authenticated human user with supplies.access."""

    def _install(**kwargs):
        ns = make_user_ns(permissions=["supplies.access"], **kwargs)
        monkeypatch.setattr(
            tool_bridge, "require_mcp_context", lambda: make_context(ns)
        )
        return ns

    return _install


@pytest.fixture()
def no_access_context(monkeypatch):
    """Authenticated human user without supplies.access."""
    ns = make_user_ns(permissions=[])
    monkeypatch.setattr(
        tool_bridge, "require_mcp_context", lambda: make_context(ns)
    )
    return ns


@pytest.fixture()
def anonymous_context(monkeypatch):
    """No validated identity — require_mcp_context fails closed."""

    def _raise():
        raise PermissionError("Unauthorized")

    monkeypatch.setattr(tool_bridge, "require_mcp_context", _raise)


@pytest.fixture()
def fake_gateway(monkeypatch):
    def _install(payload=None, error=None) -> FakeGateway:
        gw = FakeGateway(payload=payload, error=error)
        monkeypatch.setattr(tool_bridge, "_GATEWAY", gw)
        return gw

    return _install
