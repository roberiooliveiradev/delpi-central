"""Resolução de centro de custo branch-aware (filial + código)."""

from __future__ import annotations

from typing import Any, Protocol

from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterAmbiguousError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_constants import (
    normalize_budget_branch,
    serialize_org_cost_center,
)


class OrgCostCenterLookup(Protocol):
    def get_org_cost_center(
        self, code: str, *, branch: str | None = None
    ) -> dict[str, Any] | None: ...

    def list_org_cost_centers_by_code(self, code: str) -> list[dict[str, Any]]: ...


def resolve_org_cost_center(
    repository: OrgCostCenterLookup,
    *,
    code: str,
    branch: str | None = None,
    unit_id: str | None = None,
    require_active: bool = True,
) -> dict[str, Any]:
    """Resolve CC por (filial, código). Filial pode vir de branch ou unit_id."""
    code_norm = str(code or "").strip()
    if not code_norm:
        raise BudgetCostCenterInvalidError("Centro de custo obrigatório.")

    branch_raw = (branch or unit_id or "").strip() or None
    branch_norm: str | None = None
    if branch_raw:
        try:
            branch_norm = normalize_budget_branch(branch_raw)
        except ValueError as exc:
            raise BudgetCostCenterInvalidError(str(exc)) from exc

    if branch_norm:
        cc = repository.get_org_cost_center(code_norm, branch=branch_norm)
        if not cc:
            raise BudgetCostCenterNotFoundError(
                "Centro de custo inexistente no catálogo interno para a filial informada."
            )
    else:
        matches = repository.list_org_cost_centers_by_code(code_norm)
        if not matches:
            raise BudgetCostCenterNotFoundError(
                "Centro de custo inexistente no catálogo interno."
            )
        if len(matches) > 1:
            raise BudgetCostCenterAmbiguousError(
                "Centro de custo existe em mais de uma filial. Informe a filial (01 ou 02)."
            )
        cc = matches[0]

    if require_active and not cc.get("active", True):
        raise BudgetCostCenterInvalidError(
            "Centro de custo inexistente ou inativo no catálogo interno."
        )
    return cc


def authorized_unit_cost_center_pairs(
    rows: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for row in rows:
        unit_id = str(row.get("unit_id") or "").strip()
        code = str(row.get("cost_center_id") or "").strip()
        if unit_id and code and row.get("is_active", True):
            pairs.add((unit_id, code))
    return sorted(pairs)


def public_cost_center_fields(cc: dict[str, Any] | None) -> dict[str, Any]:
    serialized = serialize_org_cost_center(cc) or {}
    return {
        "branch": serialized.get("branch"),
        "code": serialized.get("code"),
        "description": serialized.get("description"),
        "cost_center_id": serialized.get("code"),
        "unit_id": serialized.get("unit_code") or serialized.get("branch"),
        "cost_center_name": serialized.get("name"),
        "cost_center_uuid": serialized.get("id"),
        "source": serialized.get("source"),
    }
