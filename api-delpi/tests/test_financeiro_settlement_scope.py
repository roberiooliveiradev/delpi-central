"""Shared-dataset scope resolver (doc 48 D3) — fail-closed contract."""

from __future__ import annotations

from app.application.security.settlement_scope import (
    SharedDatasetSettlementScopeResolver,
)


def test_disabled_gate_never_resolves() -> None:
    resolver = SharedDatasetSettlementScopeResolver(shared_dataset_enabled=False)
    assert resolver.resolve(user_subject="user-1").resolved is False
    assert resolver.resolve(user_subject=None).resolved is False


def test_enabled_gate_requires_human_subject() -> None:
    resolver = SharedDatasetSettlementScopeResolver(shared_dataset_enabled=True)
    assert resolver.resolve(user_subject=None).resolved is False
    assert resolver.resolve(user_subject="").resolved is False
    assert resolver.resolve(user_subject="   ").resolved is False


def test_enabled_gate_resolves_with_delegated_user() -> None:
    resolver = SharedDatasetSettlementScopeResolver(shared_dataset_enabled=True)
    scope = resolver.resolve(user_subject="user-1")
    assert scope.resolved is True
    assert "D3" in scope.reason
