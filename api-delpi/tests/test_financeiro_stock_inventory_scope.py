"""Shared-dataset scope resolver (doc 49) — fail-closed contract."""

from __future__ import annotations

from app.application.security.stock_inventory_scope import (
    SharedDatasetStockInventoryScopeResolver,
)


def test_disabled_gate_never_resolves() -> None:
    resolver = SharedDatasetStockInventoryScopeResolver(enabled=False)
    assert resolver.resolve(user_subject="user-1").resolved is False
    assert resolver.resolve(user_subject=None).resolved is False


def test_enabled_gate_requires_human_subject() -> None:
    resolver = SharedDatasetStockInventoryScopeResolver(enabled=True)
    assert resolver.resolve(user_subject=None).resolved is False
    assert resolver.resolve(user_subject="").resolved is False
    assert resolver.resolve(user_subject="   ").resolved is False


def test_enabled_gate_resolves_with_delegated_user() -> None:
    resolver = SharedDatasetStockInventoryScopeResolver(enabled=True)
    scope = resolver.resolve(user_subject="user-1")
    assert scope.resolved is True
    assert "shared dataset" in scope.reason
