"""Dataset-scope resolution for the R03/P7 stock-inventory read (doc 49).

Unlike FK1/FK2 settlements, ``SB9010.B9_FILIAL`` is populated, so the
snapshot can be filtered per branch — but the PO decided (doc 49 §8) that
branch is a data filter only: the ``controllership-finance.access``
audience is authorized for the shared dataset across every branch, and no
per-branch permission exists or will be created.

Until the dedicated enablement gate is on, real rows stay fail-closed:
the resolver returns ``unresolved`` and the interface layer answers the
typed ``scope_unavailable`` error. The delegated user identity alone does
not authorize the dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StockInventoryScope:
    resolved: bool
    reason: str


class StockInventoryScopeUnavailableError(Exception):
    """Raised when no proven mechanism authorizes the requested dataset."""


class StockInventoryScopeResolver(Protocol):
    def resolve(self, *, user_subject: str | None) -> StockInventoryScope: ...


class UnresolvedStockInventoryScopeResolver:
    """Fail-closed default — the enablement gate is not proven on."""

    def resolve(self, *, user_subject: str | None) -> StockInventoryScope:
        return StockInventoryScope(
            resolved=False,
            reason="no proven stock-inventory dataset scope (doc 49)",
        )


class SharedDatasetStockInventoryScopeResolver:
    """Approved shared-dataset resolver for the R03 stock inventory read.

    ``resolved`` requires both trust preconditions proven at request time:

    1. the feature gate (``FINANCEIRO_STOCK_INVENTORY_ENABLED``) is on —
       the separate production enablement gate, off by default; and
    2. a real delegated human principal exists (``user_subject`` non-empty
       — the interface layer only forwards the subject of a
       ``principal_type == "user"`` context).

    The dedicated S2S client identity (``controllership-finance-api``) and
    the ``stock-inventory.read`` scope are enforced upstream by the route
    guard; functional ``controllership-finance.access`` is enforced by the
    BFF against Core effective permissions.
    """

    def __init__(self, *, enabled: bool) -> None:
        self._enabled = bool(enabled)

    def resolve(self, *, user_subject: str | None) -> StockInventoryScope:
        if not self._enabled:
            return StockInventoryScope(
                resolved=False,
                reason=(
                    "stock-inventory dataset gate is disabled "
                    "(FINANCEIRO_STOCK_INVENTORY_ENABLED; doc 49)"
                ),
            )
        if not (user_subject or "").strip():
            return StockInventoryScope(
                resolved=False,
                reason=(
                    "stock-inventory dataset requires a delegated human "
                    "principal (doc 49)"
                ),
            )
        return StockInventoryScope(
            resolved=True,
            reason="shared dataset authorized (dedicated S2S client + delegated user)",
        )


def require_stock_inventory_scope(
    resolver: StockInventoryScopeResolver, *, user_subject: str | None
) -> StockInventoryScope:
    scope = resolver.resolve(user_subject=user_subject)
    if not scope.resolved:
        raise StockInventoryScopeUnavailableError(scope.reason)
    return scope
