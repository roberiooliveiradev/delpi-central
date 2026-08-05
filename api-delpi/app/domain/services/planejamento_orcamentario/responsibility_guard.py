"""Guard reutilizável: responsabilidade orçamentária válida por CC/módulo/exercício."""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterAmbiguousError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetResponsibilityForbiddenError,
    BudgetResponsibilityNotFoundError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_resolution import (
    resolve_org_cost_center,
)
from app.domain.services.planejamento_orcamentario.responsibility_constants import (
    ALLOWED_BUDGET_MODULES,
)


class ResponsibilityLookup(Protocol):
    def get_exercise(self, exercise_id: str) -> dict[str, Any] | None: ...

    def get_org_cost_center(
        self, code: str, *, branch: str | None = None
    ) -> dict[str, Any] | None: ...

    def list_org_cost_centers_by_code(self, code: str) -> list[dict[str, Any]]: ...

    def find_valid_responsibility(
        self,
        *,
        user_sub: str,
        exercise_id: str,
        module: str,
        cost_center_id: str,
        unit_id: str | None = None,
        on_date: date | None = None,
    ) -> dict[str, Any] | None: ...


def _is_within_validity(row: dict[str, Any], on_date: date) -> bool:
    valid_from = row.get("valid_from")
    valid_until = row.get("valid_until")
    if isinstance(valid_from, str):
        valid_from = date.fromisoformat(valid_from[:10])
    if isinstance(valid_until, str):
        valid_until = date.fromisoformat(valid_until[:10])
    if valid_from and on_date < valid_from:
        return False
    if valid_until and on_date > valid_until:
        return False
    return True


class BudgetResponsibilityGuard:
    """Valida vínculo ativo + vigência + exercício + módulo + CC + integridade org."""

    def __init__(self, repository: ResponsibilityLookup) -> None:
        self._repository = repository

    def assert_user_has_budget_responsibility(
        self,
        user_sub: str,
        exercise_id: str,
        module: str,
        cost_center_id: str,
        *,
        unit_id: str | None = None,
        on_date: date | None = None,
    ) -> dict[str, Any]:
        if not (user_sub or "").strip():
            raise BudgetResponsibilityForbiddenError(
                "Usuário autenticado obrigatório para validar responsabilidade."
            )
        module_norm = (module or "").strip().lower()
        if module_norm not in ALLOWED_BUDGET_MODULES:
            raise BudgetResponsibilityForbiddenError(
                f"Módulo orçamentário inválido: {module}.",
                code="budget_responsibility_invalid",
                status_code=422,
            )
        exercise = self._repository.get_exercise(exercise_id)
        if not exercise:
            raise BudgetResponsibilityNotFoundError("Exercício orçamentário não encontrado.")
        if str(exercise.get("status") or "") == "archived":
            raise BudgetResponsibilityForbiddenError(
                "Exercício arquivado não concede responsabilidade orçamentária."
            )
        try:
            cc = resolve_org_cost_center(
                self._repository,
                code=str(cost_center_id).strip(),
                unit_id=unit_id,
                require_active=True,
            )
        except BudgetCostCenterAmbiguousError as exc:
            raise BudgetResponsibilityForbiddenError(
                str(exc),
                code="budget_cost_center_ambiguous",
                status_code=422,
            ) from exc
        except (BudgetCostCenterNotFoundError, BudgetCostCenterInvalidError) as exc:
            raise BudgetResponsibilityForbiddenError(
                "Centro de custo inexistente ou inativo no catálogo interno.",
                code="budget_responsibility_invalid",
                status_code=422,
            ) from exc
        branch = str(cc.get("branch") or cc.get("unit_code") or "").strip()
        check_date = on_date or date.today()
        row = self._repository.find_valid_responsibility(
            user_sub=user_sub.strip(),
            exercise_id=str(exercise_id),
            module=module_norm,
            cost_center_id=str(cost_center_id).strip(),
            unit_id=branch,
            on_date=check_date,
        )
        if not row:
            raise BudgetResponsibilityForbiddenError(
                "Usuário sem responsabilidade orçamentária válida para este centro de custo."
            )
        if str(row.get("unit_id") or "") != branch:
            raise BudgetResponsibilityForbiddenError(
                "Integridade organizacional inconsistente no vínculo de responsabilidade."
            )
        area_cc = cc.get("area_code")
        area_row = row.get("area_id")
        if area_cc and area_row and str(area_row) != str(area_cc):
            raise BudgetResponsibilityForbiddenError(
                "Área do vínculo incompatível com o centro de custo do catálogo."
            )
        if not _is_within_validity(row, check_date):
            raise BudgetResponsibilityForbiddenError(
                "Responsabilidade orçamentária fora da vigência."
            )
        return {
            "responsibility": row,
            "exercise": exercise,
            "cost_center": cc,
        }
