"""Gate RBAC por escopo de filial Protheus (Todas | 01 | 02)."""

from __future__ import annotations

from dataclasses import dataclass

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.core.responses import error_response
from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    PROTHEUS_BRANCH_CODES,
    is_all_branches,
    normalize_branch_scope,
)


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


@dataclass
class BranchAccessGate:
    """Autorização consolidada vs filial única para um módulo."""

    global_view_perm: str
    branch_view_perms: dict[str, str]
    resource_label: str
    extra_global_view_perms: tuple[str, ...] = ()

    def _global_perms(self) -> tuple[str, ...]:
        return (self.global_view_perm, *self.extra_global_view_perms)

    def branch_view_allowed(self, branch_code: str) -> bool:
        if _is_superadmin():
            return True
        user = get_current_user()
        if user is None:
            return False
        if any(has_permission(user, perm) for perm in self._global_perms()):
            return True
        branch_perm = self.branch_view_perms.get(branch_code)
        return branch_perm is not None and has_permission(user, branch_perm)

    def consolidated_view_allowed(self) -> bool:
        return all(
            self.branch_view_allowed(code) for code in sorted(PROTHEUS_BRANCH_CODES)
        )

    def branch_access_error(self, raw: str | None):
        try:
            scope = normalize_branch_scope(raw)
        except ValueError:
            return error_response(
                f"branch inválida para {self.resource_label}. Use all, 01 ou 02.",
                status_code=400,
            )

        if is_all_branches(scope):
            if self.consolidated_view_allowed():
                return None
            return error_response(
                f"Sem permissão para acessar {self.resource_label} consolidado "
                f"({BRANCH_SCOPE_ALL} branches).",
                status_code=403,
            )

        if self.branch_view_allowed(scope):
            return None
        return error_response(
            f"Sem permissão para acessar {self.resource_label} desta filial.",
            status_code=403,
        )
