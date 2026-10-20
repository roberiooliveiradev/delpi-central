"""Dataset-scope resolution for financial settlement reads (doc 48 D3.1).

Probes executed on 20/10/2026 found every ``*_FILIAL`` column empty across
FK1, FK2, FK7_FILTIT, SE1 and SE2 — no Protheus column currently proves
which business branch/company a settlement belongs to, and the api-delpi
connection is a single shared database context.

Until an authorized scope contract exists (proven isolation mechanism or an
explicitly approved shared-dataset audience), real rows must stay
fail-closed: ``SettlementScopeResolver`` returns ``unresolved`` and the
interface layer answers with the typed ``scope_unavailable`` error. The
delegated user identity alone does not authorize the dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SettlementScope:
    resolved: bool
    reason: str


class SettlementScopeUnavailableError(Exception):
    """Raised when no proven mechanism authorizes the requested dataset."""


class SettlementScopeResolver(Protocol):
    def resolve(self, *, user_subject: str | None) -> SettlementScope: ...


class UnresolvedSettlementScopeResolver:
    """Fail-closed default — no proven branch/dataset scope exists yet.

    Replacing this implementation (with a proven carrier or an approved
    shared-dataset contract) is the documented unlock path; do not weaken it
    to make smokes pass.
    """

    def resolve(self, *, user_subject: str | None) -> SettlementScope:
        return SettlementScope(
            resolved=False,
            reason="no proven financial dataset scope (doc 48 D3.1)",
        )


def require_settlement_scope(
    resolver: SettlementScopeResolver, *, user_subject: str | None
) -> SettlementScope:
    scope = resolver.resolve(user_subject=user_subject)
    if not scope.resolved:
        raise SettlementScopeUnavailableError(scope.reason)
    return scope
