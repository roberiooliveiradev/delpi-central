from __future__ import annotations

from financial_app.core.security import (
    ALLOWED_BRANCHES,
    BRANCH_VIEW_PERMISSIONS,
    FIN_ACCESS,
    FIN_VIEW_FILIAL_01,
    FIN_VIEW_FILIAL_02,
    can,
)
from financial_app.domain.errors import BranchAccessDenied, InvalidBranch

_CONSOLIDATED_ALIASES = frozenset({"", "all", "consolidado"})


class BranchAccessService:
    """Gate de filial no BFF — o MFE não é barreira de segurança."""

    def assert_can_access(self, user: object | None) -> None:
        if not can(user, FIN_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal Financeiro.")

    def assert_can_use(self, user: object | None, permission: str) -> None:
        self.assert_can_access(user)
        if not can(user, permission):
            raise PermissionError("Você não tem permissão para este módulo do Portal Financeiro.")

    def resolve_branch_scope(self, user: object | None, branch: str | None) -> str | None:
        """Valida a filial e devolve o código TOTVS, ou ``None`` no consolidado.

        Consultas consolidadas (`None`, vazio ou `all`) exigem as duas filiais.
        """
        self.assert_can_access(user)
        raw = (branch or "").strip().lower()
        if raw in _CONSOLIDATED_ALIASES:
            if not (can(user, FIN_VIEW_FILIAL_01) and can(user, FIN_VIEW_FILIAL_02)):
                raise BranchAccessDenied(
                    "O consolidado exige permissão das duas filiais (01 e 02)."
                )
            return None
        if raw not in ALLOWED_BRANCHES:
            raise InvalidBranch("Filial inválida. Use 01 ou 02.")
        permission = BRANCH_VIEW_PERMISSIONS[raw]
        if not can(user, permission):
            raise BranchAccessDenied("Sem permissão para esta filial.")
        return raw
