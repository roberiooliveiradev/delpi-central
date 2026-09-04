"""Casos de uso — planejamento CAPEX por centro de custo (Fase 2C.1)."""

from __future__ import annotations

from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder

from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.application.use_cases.planejamento_orcamentario.capex_investment_use_cases import (
    _compute_completeness,
    _public_row as _public_investment,
)
from app.domain.services.planejamento_orcamentario.acknowledgement_guard import (
    BudgetGuidanceAcknowledgementGuard,
)
from app.domain.services.planejamento_orcamentario.capex_investment_constants import (
    ENTITY_TYPE_CAPEX_INVESTMENT,
    REVIEW_APPROVED,
    REVIEW_PENDING,
    REVIEW_REJECTED,
    STATUS_DRAFT as INVESTMENT_STATUS_DRAFT,
)
from app.domain.services.planejamento_orcamentario.capex_plan_constants import (
    AUDIT_INVESTMENT_APPROVED,
    AUDIT_INVESTMENT_REJECTED,
    AUDIT_PLAN_APPROVED,
    AUDIT_PLAN_CREATED,
    AUDIT_PLAN_REJECTED,
    AUDIT_PLAN_REQUEST_CHANGES,
    AUDIT_PLAN_SUBMITTED,
    AUDIT_PLAN_VERSION_CONFLICT,
    ENTITY_TYPE_CAPEX_PLAN,
    HISTORY_ACTION_APPROVED,
    HISTORY_ACTION_CREATED,
    HISTORY_ACTION_INVESTMENT_APPROVED,
    HISTORY_ACTION_INVESTMENT_REJECTED,
    HISTORY_ACTION_REJECTED,
    HISTORY_ACTION_REQUEST_CHANGES,
    HISTORY_ACTION_SUBMITTED,
    PLAN_TRANSITIONS,
    STATUS_APPROVED,
    STATUS_CHANGES_REQUESTED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    STATUS_SUBMITTED,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterAmbiguousError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetResponsibilityForbiddenError,
    BudgetUserNotAuthorizedError,
    CapexApprovalForbiddenError,
    CapexInvestmentNotFoundError,
    CapexInvestmentReviewInvalidError,
    CapexPlanAlreadyApprovedError,
    CapexPlanCommentRequiredError,
    CapexPlanIncompleteError,
    CapexPlanInvalidError,
    CapexPlanInvalidTransitionError,
    CapexPlanNotFoundError,
    CapexPlanVersionConflictError,
    CapexInvestmentCostCenterForbiddenError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_resolution import (
    authorized_unit_cost_center_pairs,
    resolve_org_cost_center,
)
from app.domain.services.planejamento_orcamentario.responsibility_constants import (
    BUDGET_MODULE_CAPEX,
)
from app.domain.services.planejamento_orcamentario.responsibility_guard import (
    BudgetResponsibilityGuard,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)

PERM_ACCESS = "planejamento-orcamentario.access"
PERM_ADMIN = "planejamento-orcamentario.admin"
PERM_SUBMIT = "planejamento-orcamentario.capex.submit"
PERM_APPROVE = "planejamento-orcamentario.capex.approve"


def _is_admin(actor: BudgetActor) -> bool:
    return PERM_ADMIN in actor.permissions


def _has_access(actor: BudgetActor) -> bool:
    return bool(
        actor.permissions
        & {
            PERM_ACCESS,
            PERM_ADMIN,
            PERM_SUBMIT,
            PERM_APPROVE,
            "planejamento-orcamentario.guidance.view",
            "planejamento-orcamentario.guidance.manage",
            "planejamento-orcamentario.scopes.manage",
        }
    )


def _can_submit(actor: BudgetActor) -> bool:
    return PERM_SUBMIT in actor.permissions or _is_admin(actor)


def _can_approve(actor: BudgetActor) -> bool:
    return PERM_APPROVE in actor.permissions or _is_admin(actor)


def _require_access(actor: BudgetActor) -> None:
    if not _has_access(actor):
        raise BudgetUserNotAuthorizedError(
            "Sem permissão de acesso ao planejamento orçamentário."
        )


def _public_plan(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "exercise_id",
        "unit_id",
        "area_id",
        "cost_center_id",
        "status",
        "version",
        "submitted_by",
        "submitted_by_name",
        "submitted_at",
        "reviewed_by",
        "reviewed_at",
        "decision_comment",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "cost_center_icon_key",
        "cost_center_name",
        "cost_center_owner_name",
        "cost_center_owner_sub",
        "investment_count",
    )
    out = {k: row.get(k) for k in keys}
    out["branch"] = row.get("unit_id")
    if out.get("investment_count") is not None:
        try:
            out["investment_count"] = int(out["investment_count"])
        except (TypeError, ValueError):
            out["investment_count"] = 0
    return out


def _public_history(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "plan_id",
        "action",
        "previous_status",
        "new_status",
        "comment",
        "actor_sub",
        "actor_name",
        "created_at",
        "investment_id",
    )
    return {k: row.get(k) for k in keys}


class CapexPlanUseCases:
    def __init__(self, repository: PostgresBudgetPlanningRepository | None = None) -> None:
        self._repo = repository or PostgresBudgetPlanningRepository()
        self._ack_guard = BudgetGuidanceAcknowledgementGuard(self._repo)
        self._resp_guard = BudgetResponsibilityGuard(self._repo)

    def _assert_unlocked(self, actor: BudgetActor) -> dict[str, Any]:
        return self._ack_guard.assert_modules_unlocked(user_sub=actor.user_id)

    def _assert_responsibility(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self._resp_guard.assert_user_has_budget_responsibility(
                actor.user_id,
                exercise_id,
                BUDGET_MODULE_CAPEX,
                cost_center_id,
                unit_id=unit_id,
            )
        except BudgetResponsibilityForbiddenError as exc:
            raise CapexInvestmentCostCenterForbiddenError(str(exc)) from exc

    def _resolve_org(
        self, cost_center_id: str, *, unit_id: str | None = None
    ) -> dict[str, Any]:
        try:
            cc = resolve_org_cost_center(
                self._repo,
                code=cost_center_id,
                unit_id=unit_id,
                require_active=True,
            )
        except BudgetCostCenterAmbiguousError as exc:
            raise CapexPlanInvalidError(str(exc)) from exc
        except (BudgetCostCenterNotFoundError, BudgetCostCenterInvalidError) as exc:
            raise CapexPlanInvalidError(str(exc)) from exc
        unit = str(cc.get("unit_code") or cc.get("branch") or "").strip()
        if not unit:
            raise CapexPlanInvalidError("Centro de custo sem unidade associada.")
        area_id = cc.get("area_code")
        return {
            "unit_id": unit,
            "area_id": str(area_id) if area_id else None,
            "cost_center": cc,
        }

    def _assert_can_view_plan(self, actor: BudgetActor, plan: dict[str, Any]) -> None:
        if _is_admin(actor) or _can_approve(actor):
            return
        try:
            self._assert_responsibility(
                actor,
                exercise_id=str(plan["exercise_id"]),
                cost_center_id=str(plan["cost_center_id"]),
                unit_id=str(plan.get("unit_id") or "") or None,
            )
        except CapexInvestmentCostCenterForbiddenError:
            raise CapexPlanNotFoundError("Planejamento CAPEX não encontrado.") from None

    def _authorized_cost_centers(
        self, actor: BudgetActor, *, exercise_id: str | None
    ) -> list[tuple[str, str]] | None:
        if _is_admin(actor) or _can_approve(actor):
            return None
        rows = self._repo.list_budget_responsibilities_for_user(
            user_sub=actor.user_id,
            module=BUDGET_MODULE_CAPEX,
            exercise_id=exercise_id,
            active_only=True,
        )
        return authorized_unit_cost_center_pairs(rows)

    def _pair_authorized(
        self,
        pairs: list[tuple[str, str]] | None,
        *,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> bool:
        if pairs is None:
            return True
        if unit_id:
            return (unit_id, cost_center_id) in pairs
        return any(cc == cost_center_id for _, cc in pairs)

    def resolve_plan(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> dict[str, Any]:
        """Obtém ou cria o planejamento único do exercício+filial+CC."""
        _require_access(actor)
        self._assert_unlocked(actor)
        exercise_id = str(exercise_id or "").strip()
        cost_center_id = str(cost_center_id or "").strip()
        unit_id_raw = str(unit_id or "").strip() or None
        if not exercise_id or not cost_center_id:
            raise CapexPlanInvalidError("Exercício e centro de custo são obrigatórios.")

        exercise = self._repo.get_exercise(exercise_id)
        if not exercise:
            raise CapexPlanInvalidError("Exercício orçamentário não encontrado.")
        if str(exercise.get("status") or "") == "archived":
            raise CapexPlanInvalidError("Exercício arquivado não permite planejamento CAPEX.")

        self._assert_responsibility(
            actor,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id_raw,
        )
        org = self._resolve_org(cost_center_id, unit_id=unit_id_raw)

        existing = self._repo.get_capex_plan_by_exercise_cc(
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=org["unit_id"],
        )
        if existing:
            return _public_plan(existing)

        try:
            created = self._repo.create_capex_plan(
                {
                    "exercise_id": exercise_id,
                    "unit_id": org["unit_id"],
                    "area_id": org["area_id"],
                    "cost_center_id": cost_center_id,
                    "created_by": actor.user_id,
                }
            )
        except PluginsRepositoryError:
            # Corrida / conflito único: garante txn limpa antes do SELECT de recuperação.
            try:
                self._repo.rollback()
            except PluginsRepositoryError:
                pass
            raced = self._repo.get_capex_plan_by_exercise_cc(
                exercise_id=exercise_id,
                cost_center_id=cost_center_id,
                unit_id=org["unit_id"],
            )
            if raced:
                return _public_plan(raced)
            raise

        self._repo.append_capex_plan_history(
            {
                "plan_id": created["id"],
                "action": HISTORY_ACTION_CREATED,
                "previous_status": None,
                "new_status": STATUS_DRAFT,
                "comment": None,
                "actor_sub": actor.user_id,
                "actor_name": actor.user_name,
            }
        )
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type=ENTITY_TYPE_CAPEX_PLAN,
            entity_id=created["id"],
            action=AUDIT_PLAN_CREATED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=_public_plan(created),
        )
        return _public_plan(created)

    def list_plans(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        status: str | None = None,
        submitted_by: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 50)))
        allowed = self._authorized_cost_centers(actor, exercise_id=exercise_id)
        if cost_center_id and not self._pair_authorized(
            allowed, cost_center_id=cost_center_id, unit_id=unit_id
        ):
            raise CapexInvestmentCostCenterForbiddenError(
                "Sem responsabilidade orçamentária para o centro de custo filtrado."
            )
        items, total = self._repo.list_capex_plans(
            exercise_id=exercise_id,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            status=status,
            submitted_by=submitted_by,
            cost_center_ids=None,
            unit_cost_center_pairs=allowed,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return {
            "items": [_public_plan(i) for i in items],
            "pagination": PaginationEnvelopeBuilder.build(
                shape="paged_count",
                page=page,
                page_size=page_size,
                total=total,
                extra={"has_more": (page * page_size) < total},
            ),
        }

    def get_plan(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        plan = self._repo.get_capex_plan(plan_id)
        if not plan:
            raise CapexPlanNotFoundError("Planejamento CAPEX não encontrado.")
        self._assert_can_view_plan(actor, plan)
        return _public_plan(plan)

    def get_plan_detail(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        plan = self.get_plan(actor, plan_id)
        investments, _total = self._repo.list_capex_investments(
            exercise_id=str(plan["exercise_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
            cost_center_id=str(plan["cost_center_id"]),
            status=INVESTMENT_STATUS_DRAFT,
            offset=0,
            limit=500,
        )
        return {
            **plan,
            "investments": [_public_investment(i) for i in investments],
        }

    def list_history(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        plan = self.get_plan(actor, plan_id)
        rows = self._repo.list_capex_plan_history(str(plan["id"]))
        return {"items": [_public_history(r) for r in rows]}

    def _collect_active_investments(
        self, *, exercise_id: str, cost_center_id: str, unit_id: str | None = None
    ) -> list[dict[str, Any]]:
        items, _total = self._repo.list_capex_investments(
            exercise_id=exercise_id,
            unit_id=unit_id,
            cost_center_id=cost_center_id,
            status=INVESTMENT_STATUS_DRAFT,
            offset=0,
            limit=1000,
        )
        return items

    def _plan_org(self, plan: dict[str, Any]) -> tuple[str, str, str | None]:
        return (
            str(plan["exercise_id"]),
            str(plan["cost_center_id"]),
            str(plan.get("unit_id") or "") or None,
        )

    def _stamp_reviews(
        self,
        plan: dict[str, Any],
        *,
        review_status: str,
        reviewed_by: str | None = None,
        reviewed_by_name: str | None = None,
        review_comment: str | None = None,
    ) -> None:
        exercise_id, cost_center_id, unit_id = self._plan_org(plan)
        self._repo.stamp_capex_investment_reviews(
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
            review_status=review_status,
            reviewed_by=reviewed_by,
            reviewed_by_name=reviewed_by_name,
            review_comment=review_comment,
        )

    def _investment_belongs_to_plan(
        self, investment: dict[str, Any], plan: dict[str, Any]
    ) -> bool:
        if str(investment.get("status") or "") != INVESTMENT_STATUS_DRAFT:
            return False
        if str(investment.get("exercise_id")) != str(plan.get("exercise_id")):
            return False
        if str(investment.get("cost_center_id")) != str(plan.get("cost_center_id")):
            return False
        inv_unit = str(investment.get("unit_id") or "")
        plan_unit = str(plan.get("unit_id") or "")
        return not plan_unit or inv_unit == plan_unit

    def _review_status_of(self, row: dict[str, Any]) -> str:
        value = str(row.get("review_status") or REVIEW_PENDING).strip() or REVIEW_PENDING
        return value

    def _maybe_close_plan_after_item_decisions(
        self, actor: BudgetActor, plan: dict[str, Any]
    ) -> dict[str, Any]:
        current = self._repo.get_capex_plan(str(plan["id"])) or plan
        if str(current.get("status") or "") != STATUS_SUBMITTED:
            return current
        exercise_id, cost_center_id, unit_id = self._plan_org(current)
        investments = self._collect_active_investments(
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
        )
        statuses = [self._review_status_of(row) for row in investments]
        if not statuses or any(status == REVIEW_PENDING for status in statuses):
            return current
        new_status = (
            STATUS_APPROVED
            if any(status == REVIEW_APPROVED for status in statuses)
            else STATUS_REJECTED
        )
        history_action = (
            HISTORY_ACTION_APPROVED
            if new_status == STATUS_APPROVED
            else HISTORY_ACTION_REJECTED
        )
        audit_action = (
            AUDIT_PLAN_APPROVED if new_status == STATUS_APPROVED else AUDIT_PLAN_REJECTED
        )
        try:
            updated = self._repo.transition_capex_plan(
                str(current["id"]),
                expected_version=int(current.get("version") or 0),
                new_status=new_status,
                actor_id=actor.user_id,
                reviewed_by=actor.user_id,
                decision_comment=None,
            )
        except PluginsRepositoryError:
            return self._repo.get_capex_plan(str(current["id"])) or current
        self._repo.append_capex_plan_history(
            {
                "plan_id": str(current["id"]),
                "action": history_action,
                "previous_status": STATUS_SUBMITTED,
                "new_status": new_status,
                "comment": None,
                "actor_sub": actor.user_id,
                "actor_name": actor.user_name,
            }
        )
        self._repo.append_audit(
            exercise_id=str(current["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_PLAN,
            entity_id=str(current["id"]),
            action=audit_action,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_plan(current),
            after_state=_public_plan(updated),
        )
        return updated

    def _validate_for_submit(
        self, investments: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not investments:
            raise CapexPlanIncompleteError(
                "É necessário ao menos um investimento ativo para submeter.",
                incomplete_investments=[],
            )
        incomplete: list[dict[str, Any]] = []
        for row in investments:
            completeness = _compute_completeness(row)
            if not completeness["is_complete"]:
                incomplete.append(
                    {
                        "id": row.get("id"),
                        "description": row.get("description"),
                        "missing_fields": completeness["missing_fields"],
                    }
                )
                continue
            # Categoria ativa
            cat_id = row.get("category_id")
            if cat_id:
                cat = self._repo.get_capex_category(str(cat_id))
                if not cat or not cat.get("is_active"):
                    incomplete.append(
                        {
                            "id": row.get("id"),
                            "description": row.get("description"),
                            "missing_fields": ["category_id"],
                            "reason": "category_inactive",
                        }
                    )
                    continue
            # Valor positivo
            try:
                amount = Decimal(str(row.get("estimated_amount")))
                if amount <= 0:
                    incomplete.append(
                        {
                            "id": row.get("id"),
                            "description": row.get("description"),
                            "missing_fields": ["estimated_amount"],
                        }
                    )
            except (InvalidOperation, TypeError, ValueError):
                incomplete.append(
                    {
                        "id": row.get("id"),
                        "description": row.get("description"),
                        "missing_fields": ["estimated_amount"],
                    }
                )
        return incomplete

    def submit_plan(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        if not _can_submit(actor):
            raise CapexApprovalForbiddenError(
                "Sem permissão para submeter planejamento CAPEX."
            )

        plan = self._repo.get_capex_plan(plan_id)
        if not plan:
            raise CapexPlanNotFoundError("Planejamento CAPEX não encontrado.")
        self._assert_responsibility(
            actor,
            exercise_id=str(plan["exercise_id"]),
            cost_center_id=str(plan["cost_center_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
        )

        exercise = self._repo.get_exercise(str(plan["exercise_id"]))
        if not exercise or str(exercise.get("status") or "") not in {"open", "closing"}:
            raise CapexPlanInvalidError(
                "Exercício precisa estar aberto (ou em encerramento) para submissão."
            )

        current_status = str(plan.get("status") or "")
        target = PLAN_TRANSITIONS.get((current_status, "submit"))
        if not target:
            raise CapexPlanInvalidTransitionError(
                f"Não é possível submeter a partir do status '{current_status}'."
            )

        if int(plan.get("version") or 0) != int(version):
            self._repo.append_audit(
                exercise_id=str(plan["exercise_id"]),
                entity_type=ENTITY_TYPE_CAPEX_PLAN,
                entity_id=plan_id,
                action=AUDIT_PLAN_VERSION_CONFLICT,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=_public_plan(plan),
                after_state={"expected_version": version},
            )
            raise CapexPlanVersionConflictError(
                "O planejamento foi alterado em outra sessão. Recarregue e tente novamente."
            )

        investments = self._collect_active_investments(
            exercise_id=str(plan["exercise_id"]),
            cost_center_id=str(plan["cost_center_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
        )
        incomplete = self._validate_for_submit(investments)
        if incomplete:
            raise CapexPlanIncompleteError(
                "Há investimentos incompletos ou inválidos. Corrija antes de submeter.",
                incomplete_investments=incomplete,
            )

        try:
            updated = self._repo.transition_capex_plan(
                plan_id,
                expected_version=int(version),
                new_status=STATUS_SUBMITTED,
                actor_id=actor.user_id,
                submitted_by=actor.user_id,
                submitted_by_name=actor.user_name,
                clear_review=True,
                decision_comment=(comment.strip() if comment else None),
            )
        except PluginsRepositoryError as exc:
            raise CapexPlanVersionConflictError(
                "Conflito de versão do planejamento CAPEX."
            ) from exc

        self._repo.append_capex_plan_history(
            {
                "plan_id": plan_id,
                "action": HISTORY_ACTION_SUBMITTED,
                "previous_status": current_status,
                "new_status": STATUS_SUBMITTED,
                "comment": (comment.strip() if comment else None),
                "actor_sub": actor.user_id,
                "actor_name": actor.user_name,
            }
        )
        self._repo.append_audit(
            exercise_id=str(plan["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_PLAN,
            entity_id=plan_id,
            action=AUDIT_PLAN_SUBMITTED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_plan(plan),
            after_state=_public_plan(updated),
        )
        self._stamp_reviews(updated, review_status=REVIEW_PENDING)
        return _public_plan(updated)

    def list_review_queue(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        status: str | None = None,
        submitted_by: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise CapexApprovalForbiddenError(
                "Sem permissão para acessar a fila de aprovação CAPEX."
            )
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 50)))
        # Fila padrão: submitted; filtro de status opcional
        filter_status = status or STATUS_SUBMITTED
        items, total = self._repo.list_capex_plans(
            exercise_id=exercise_id,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            status=filter_status,
            submitted_by=submitted_by,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return {
            "items": [_public_plan(i) for i in items],
            "pagination": PaginationEnvelopeBuilder.build(
                shape="paged_count",
                page=page,
                page_size=page_size,
                total=total,
                extra={"has_more": (page * page_size) < total},
            ),
        }

    def get_review_detail(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise CapexApprovalForbiddenError(
                "Sem permissão para revisar planejamento CAPEX."
            )
        plan = self._repo.get_capex_plan(plan_id)
        if not plan:
            raise CapexPlanNotFoundError("Planejamento CAPEX não encontrado.")
        return self.get_plan_detail(actor, plan_id)

    def _decide(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        action: str,
        comment: str | None,
        require_comment: bool,
        history_action: str,
        audit_action: str,
        new_status: str,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise CapexApprovalForbiddenError(
                "Sem permissão para decidir sobre planejamento CAPEX."
            )

        plan = self._repo.get_capex_plan(plan_id)
        if not plan:
            raise CapexPlanNotFoundError("Planejamento CAPEX não encontrado.")

        current_status = str(plan.get("status") or "")
        if current_status == STATUS_APPROVED and action == "approve":
            raise CapexPlanAlreadyApprovedError(
                "Este planejamento CAPEX já está aprovado."
            )

        target = PLAN_TRANSITIONS.get((current_status, action))
        if not target or target != new_status:
            raise CapexPlanInvalidTransitionError(
                f"Transição '{action}' inválida a partir de '{current_status}'."
            )

        if require_comment and not (comment or "").strip():
            raise CapexPlanCommentRequiredError(
                "Comentário/justificativa é obrigatório para esta decisão."
            )

        # Segregação: aprovador não decide o plano que ele mesmo submeteu
        # (matriz de papéis: submit ≠ approve; reforço por ator).
        if plan.get("submitted_by") and str(plan["submitted_by"]) == actor.user_id:
            if not _is_admin(actor):
                raise CapexApprovalForbiddenError(
                    "Segregação de funções: quem submeteu não pode decidir o próprio planejamento."
                )

        if int(plan.get("version") or 0) != int(version):
            self._repo.append_audit(
                exercise_id=str(plan["exercise_id"]),
                entity_type=ENTITY_TYPE_CAPEX_PLAN,
                entity_id=plan_id,
                action=AUDIT_PLAN_VERSION_CONFLICT,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=_public_plan(plan),
                after_state={"expected_version": version, "action": action},
            )
            raise CapexPlanVersionConflictError(
                "O planejamento foi alterado em outra sessão. Recarregue e tente novamente."
            )

        try:
            updated = self._repo.transition_capex_plan(
                plan_id,
                expected_version=int(version),
                new_status=new_status,
                actor_id=actor.user_id,
                reviewed_by=actor.user_id,
                decision_comment=(comment.strip() if comment else None),
            )
        except PluginsRepositoryError as exc:
            raise CapexPlanVersionConflictError(
                "Conflito de versão do planejamento CAPEX."
            ) from exc

        self._repo.append_capex_plan_history(
            {
                "plan_id": plan_id,
                "action": history_action,
                "previous_status": current_status,
                "new_status": new_status,
                "comment": (comment.strip() if comment else None),
                "actor_sub": actor.user_id,
                "actor_name": actor.user_name,
            }
        )
        self._repo.append_audit(
            exercise_id=str(plan["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_PLAN,
            entity_id=plan_id,
            action=audit_action,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_plan(plan),
            after_state=_public_plan(updated),
        )
        return _public_plan(updated)

    def request_changes(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str,
    ) -> dict[str, Any]:
        updated = self._decide(
            actor,
            plan_id,
            version=version,
            action="request_changes",
            comment=comment,
            require_comment=True,
            history_action=HISTORY_ACTION_REQUEST_CHANGES,
            audit_action=AUDIT_PLAN_REQUEST_CHANGES,
            new_status=STATUS_CHANGES_REQUESTED,
        )
        self._stamp_reviews(updated, review_status=REVIEW_PENDING)
        return updated

    def reject_plan(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str,
    ) -> dict[str, Any]:
        updated = self._decide(
            actor,
            plan_id,
            version=version,
            action="reject",
            comment=comment,
            require_comment=True,
            history_action=HISTORY_ACTION_REJECTED,
            audit_action=AUDIT_PLAN_REJECTED,
            new_status=STATUS_REJECTED,
        )
        self._stamp_reviews(
            updated,
            review_status=REVIEW_REJECTED,
            reviewed_by=actor.user_id,
            reviewed_by_name=actor.user_name,
            review_comment=comment,
        )
        return updated

    def approve_plan(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        updated = self._decide(
            actor,
            plan_id,
            version=version,
            action="approve",
            comment=comment,
            require_comment=False,
            history_action=HISTORY_ACTION_APPROVED,
            audit_action=AUDIT_PLAN_APPROVED,
            new_status=STATUS_APPROVED,
        )
        self._stamp_reviews(
            updated,
            review_status=REVIEW_APPROVED,
            reviewed_by=actor.user_id,
            reviewed_by_name=actor.user_name,
            review_comment=(comment.strip() if comment else None),
        )
        return updated

    def decide_investment(
        self,
        actor: BudgetActor,
        plan_id: str,
        investment_id: str,
        *,
        version: int,
        action: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise CapexApprovalForbiddenError(
                "Sem permissão para decidir sobre planejamento CAPEX."
            )
        if action not in {"approve", "reject"}:
            raise CapexInvestmentReviewInvalidError(
                "Ação de decisão inválida para o investimento."
            )

        plan = self._repo.get_capex_plan(plan_id)
        if not plan:
            raise CapexPlanNotFoundError("Planejamento CAPEX não encontrado.")
        if str(plan.get("status") or "") != STATUS_SUBMITTED:
            raise CapexPlanInvalidTransitionError(
                "Decisão por investimento só é aceita com o planejamento enviado para aprovação."
            )
        if plan.get("submitted_by") and str(plan["submitted_by"]) == actor.user_id:
            if not _is_admin(actor):
                raise CapexApprovalForbiddenError(
                    "Segregação de funções: quem submeteu não pode decidir o próprio planejamento."
                )
        if int(plan.get("version") or 0) != int(version):
            self._repo.append_audit(
                exercise_id=str(plan["exercise_id"]),
                entity_type=ENTITY_TYPE_CAPEX_PLAN,
                entity_id=plan_id,
                action=AUDIT_PLAN_VERSION_CONFLICT,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=_public_plan(plan),
                after_state={"expected_version": version, "action": action},
            )
            raise CapexPlanVersionConflictError(
                "O planejamento foi alterado em outra sessão. Recarregue e tente novamente."
            )

        investment = self._repo.get_capex_investment(investment_id)
        if not investment or not self._investment_belongs_to_plan(investment, plan):
            raise CapexInvestmentNotFoundError(
                "Investimento não encontrado neste planejamento."
            )

        note = (comment or "").strip() or None
        if action == "reject" and not note:
            raise CapexPlanCommentRequiredError(
                "Justificativa obrigatória para reprovar o investimento."
            )

        review_status = REVIEW_APPROVED if action == "approve" else REVIEW_REJECTED
        updated_investment = self._repo.set_capex_investment_review(
            investment_id,
            review_status=review_status,
            review_comment=note,
            reviewed_by=actor.user_id,
            reviewed_by_name=actor.user_name,
        )
        label = str(updated_investment.get("description") or "Investimento").strip()
        hist_comment = f"{label}: {note}" if note else label
        history_action = (
            HISTORY_ACTION_INVESTMENT_APPROVED
            if action == "approve"
            else HISTORY_ACTION_INVESTMENT_REJECTED
        )
        audit_action = (
            AUDIT_INVESTMENT_APPROVED if action == "approve" else AUDIT_INVESTMENT_REJECTED
        )
        self._repo.append_capex_plan_history(
            {
                "plan_id": plan_id,
                "action": history_action,
                "previous_status": STATUS_SUBMITTED,
                "new_status": STATUS_SUBMITTED,
                "comment": hist_comment,
                "actor_sub": actor.user_id,
                "actor_name": actor.user_name,
                "investment_id": investment_id,
            }
        )
        self._repo.append_audit(
            exercise_id=str(plan["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_INVESTMENT,
            entity_id=investment_id,
            action=audit_action,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_investment(investment),
            after_state=_public_investment(updated_investment),
        )
        self._maybe_close_plan_after_item_decisions(actor, plan)
        return self.get_plan_detail(actor, plan_id)
