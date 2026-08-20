from __future__ import annotations

from production_control_app.core.security import (
    ALLOWED_BRANCHES,
    BRANCH_VIEW_PERMISSIONS,
    PC_ACCESS,
    can,
)
from production_control_app.domain.errors import BranchAccessDenied, InvalidBranch


class BranchAccessService:
    """Gate de filial no BFF — equivalente ao BranchAccessGate da api-delpi."""

    def assert_can_access(self, user: object | None) -> None:
        if not can(user, PC_ACCESS):
            raise PermissionError("Você não tem permissão para acessar o Portal PCP.")

    def assert_can_view_branch(self, user: object | None, branch: str) -> None:
        self.assert_can_access(user)
        code = (branch or "").strip()
        if code not in ALLOWED_BRANCHES:
            raise InvalidBranch("Filial inválida. Use 01 ou 02.")
        permission = BRANCH_VIEW_PERMISSIONS[code]
        if not can(user, permission):
            raise BranchAccessDenied("Sem permissão para esta filial.")
