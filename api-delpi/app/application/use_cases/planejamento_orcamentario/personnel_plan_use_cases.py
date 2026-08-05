"""Casos de uso — planos e linhas do Orçamento de Pessoal (Fase 3B.1 / 3C.1)."""

from __future__ import annotations

from typing import Any

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.acknowledgement_guard import (
    BudgetGuidanceAcknowledgementGuard,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterAmbiguousError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetResponsibilityForbiddenError,
    BudgetUserNotAuthorizedError,
    PersonnelApprovalForbiddenError,
    PersonnelCostCenterBranchMismatchError,
    PersonnelInvalidHeadcountError,
    PersonnelLineDuplicatePositionError,
    PersonnelLineNotFoundError,
    PersonnelLineVersionConflictError,
    PersonnelPlanAlreadyApprovedError,
    PersonnelPlanCommentRequiredError,
    PersonnelPlanIncompleteError,
    PersonnelPlanInvalidError,
    PersonnelPlanInvalidTransitionError,
    PersonnelPlanLockedError,
    PersonnelPlanNotFoundError,
    PersonnelPlanVersionConflictError,
    PersonnelPositionNameRequiredError,
    PersonnelPositionNameTooLongError,
    PersonnelResponsibilityRequiredError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_resolution import (
    authorized_unit_cost_center_pairs,
    resolve_org_cost_center,
)
from app.domain.services.planejamento_orcamentario.personnel_budget_constants import (
    AUDIT_ACCESS_DENIED,
    AUDIT_LINE_ARCHIVED,
    AUDIT_LINE_CREATED,
    AUDIT_LINE_UPDATED,
    AUDIT_LINE_VERSION_CONFLICT,
    AUDIT_PLAN_APPROVED,
    AUDIT_PLAN_CREATED,
    AUDIT_PLAN_REJECTED,
    AUDIT_PLAN_REQUEST_CHANGES,
    AUDIT_PLAN_RESOLVED,
    AUDIT_PLAN_SUBMITTED,
    AUDIT_PLAN_VERSION_CONFLICT,
    ENTITY_TYPE_PERSONNEL_PLAN,
    ENTITY_TYPE_PERSONNEL_PLAN_LINE,
    HEADCOUNT_FIELDS,
    HISTORY_ACTION_APPROVED,
    HISTORY_ACTION_CREATED,
    HISTORY_ACTION_REJECTED,
    HISTORY_ACTION_REQUEST_CHANGES,
    HISTORY_ACTION_SUBMITTED,
    PLAN_TRANSITIONS,
    POSITION_NAME_MAX_LENGTH,
    STATUS_APPROVED,
    STATUS_CHANGES_REQUESTED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    STATUS_SUBMITTED,
)
from app.domain.services.planejamento_orcamentario.personnel_plan_guard import (
    assert_personnel_plan_allows_mutation,
)
from app.domain.services.planejamento_orcamentario.responsibility_constants import (
    BUDGET_MODULE_PERSONNEL,
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
PERM_VIEW = "planejamento-orcamentario.personnel.view"
PERM_EDIT = "planejamento-orcamentario.personnel.edit"
PERM_SUBMIT = "planejamento-orcamentario.personnel.submit"
PERM_APPROVE = "planejamento-orcamentario.personnel.approve"


def _is_admin(actor: BudgetActor) -> bool:
    return PERM_ADMIN in actor.permissions


def _can_view(actor: BudgetActor) -> bool:
    return bool(
        actor.permissions
        & {
            PERM_ACCESS,
            PERM_ADMIN,
            PERM_VIEW,
            PERM_EDIT,
            PERM_SUBMIT,
            PERM_APPROVE,
            "planejamento-orcamentario.guidance.view",
            "planejamento-orcamentario.scopes.manage",
        }
    )


def _can_edit(actor: BudgetActor) -> bool:
    return PERM_EDIT in actor.permissions or _is_admin(actor)


def _can_submit(actor: BudgetActor) -> bool:
    return PERM_SUBMIT in actor.permissions or _is_admin(actor)


def _can_approve(actor: BudgetActor) -> bool:
    return PERM_APPROVE in actor.permissions or _is_admin(actor)


def _require_view(actor: BudgetActor) -> None:
    if not _can_view(actor):
        raise BudgetUserNotAuthorizedError(
            "Sem permissão para consultar o Orçamento de Pessoal."
        )


def _require_edit(actor: BudgetActor) -> None:
    if not _can_edit(actor):
        raise BudgetUserNotAuthorizedError(
            "Sem permissão para editar o Orçamento de Pessoal."
        )


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
    )
    return {k: row.get(k) for k in keys}


def _normalize_position_name(value: Any) -> str:
    """Trim preservando acentos; rejeita vazio e acima do limite."""
    if value is None:
        raise PersonnelPositionNameRequiredError("Nome do cargo é obrigatório.")
    name = str(value).strip()
    if not name:
        raise PersonnelPositionNameRequiredError("Nome do cargo é obrigatório.")
    if len(name) > POSITION_NAME_MAX_LENGTH:
        raise PersonnelPositionNameTooLongError(
            f"Nome do cargo deve ter no máximo {POSITION_NAME_MAX_LENGTH} caracteres."
        )
    return name


def _position_name_key(name: str) -> str:
    return name.strip().casefold()


def _parse_headcount(value: Any, field: str, *, allow_null: bool = True) -> int | None:
    if value is None or value == "":
        if allow_null:
            return None
        raise PersonnelInvalidHeadcountError(f"{field} é obrigatório.")
    if isinstance(value, bool):
        raise PersonnelInvalidHeadcountError(f"{field} deve ser um inteiro ≥ 0.")
    try:
        if isinstance(value, float) and not value.is_integer():
            raise PersonnelInvalidHeadcountError(
                f"{field} deve ser um inteiro (sem casas decimais)."
            )
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise PersonnelInvalidHeadcountError(
            f"{field} deve ser um inteiro ≥ 0."
        ) from exc
    if number < 0:
        raise PersonnelInvalidHeadcountError(
            f"{field} não pode ser negativo."
        )
    return number


def _line_completeness(row: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for field in HEADCOUNT_FIELDS:
        if row.get(field) is None:
            missing.append(field)
    return {"is_complete": len(missing) == 0, "missing_fields": missing}


def _public_line(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "plan_id",
        "position_name",
        "headcount_dec_2025",
        "headcount_oct_2026",
        "headcount_forecast",
        "headcount_dec_2027",
        "observations",
        "version",
        "is_active",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
    )
    out = {k: row.get(k) for k in keys}
    completeness = _line_completeness(row)
    out["is_complete"] = completeness["is_complete"]
    out["missing_fields"] = completeness["missing_fields"]
    return out


def _aggregate_lines(lines: list[dict[str, Any]]) -> dict[str, Any]:
    active = [ln for ln in lines if ln.get("is_active", True)]
    totals = {field: 0 for field in HEADCOUNT_FIELDS}
    incomplete = 0
    plan_missing: list[str] = []
    for ln in active:
        comp = _line_completeness(ln)
        if not comp["is_complete"]:
            incomplete += 1
        for field in HEADCOUNT_FIELDS:
            value = ln.get(field)
            if value is not None:
                totals[field] += int(value)
    if not active:
        plan_missing.append("lines")
        is_complete = False
    else:
        is_complete = incomplete == 0
        if not is_complete:
            plan_missing.append("incomplete_lines")
    return {
        "position_count": len(active),
        "totals": {
            "headcount_dec_2025": totals["headcount_dec_2025"],
            "headcount_oct_2026": totals["headcount_oct_2026"],
            "headcount_forecast": totals["headcount_forecast"],
            "headcount_dec_2027": totals["headcount_dec_2027"],
        },
        "incomplete_line_count": incomplete,
        "is_complete": is_complete,
        "missing_fields": plan_missing,
    }


class PersonnelPlanUseCases:
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
        audit_on_deny: bool = True,
    ) -> dict[str, Any]:
        try:
            return self._resp_guard.assert_user_has_budget_responsibility(
                actor.user_id,
                exercise_id,
                BUDGET_MODULE_PERSONNEL,
                cost_center_id,
                unit_id=unit_id,
            )
        except BudgetResponsibilityForbiddenError as exc:
            if audit_on_deny:
                self._repo.append_audit(
                    exercise_id=exercise_id,
                    entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
                    entity_id=None,
                    action=AUDIT_ACCESS_DENIED,
                    actor_user_id=actor.user_id,
                    actor_name=actor.user_name,
                    before_state=None,
                    after_state={
                        "unit_id": unit_id,
                        "cost_center_id": cost_center_id,
                        "module": BUDGET_MODULE_PERSONNEL,
                    },
                )
            raise PersonnelResponsibilityRequiredError(str(exc)) from exc

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
            raise PersonnelPlanInvalidError(str(exc)) from exc
        except BudgetCostCenterNotFoundError as exc:
            # Código existe em outra filial → mismatch explícito (não colisão silenciosa)
            if unit_id:
                others = self._repo.list_org_cost_centers_by_code(cost_center_id)
                if others:
                    raise PersonnelCostCenterBranchMismatchError(
                        f"Centro de custo {cost_center_id} não pertence à filial {unit_id}."
                    ) from exc
            raise PersonnelPlanInvalidError(str(exc)) from exc
        except BudgetCostCenterInvalidError as exc:
            raise PersonnelPlanInvalidError(str(exc)) from exc
        resolved_unit = str(cc.get("unit_code") or cc.get("branch") or "").strip()
        if not resolved_unit:
            raise PersonnelPlanInvalidError("Centro de custo sem filial associada.")
        if unit_id and str(unit_id).strip() != resolved_unit:
            raise PersonnelCostCenterBranchMismatchError(
                f"Centro de custo {cost_center_id} não pertence à filial {unit_id}."
            )
        area_id = cc.get("area_code")
        return {
            "unit_id": resolved_unit,
            "area_id": str(area_id) if area_id else None,
            "cost_center": cc,
        }

    def _authorized_pairs(
        self, actor: BudgetActor, *, exercise_id: str | None
    ) -> list[tuple[str, str]] | None:
        if _is_admin(actor) or _can_approve(actor):
            return None
        rows = self._repo.list_budget_responsibilities_for_user(
            user_sub=actor.user_id,
            module=BUDGET_MODULE_PERSONNEL,
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

    def _enrich_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        lines = self._repo.list_personnel_plan_lines(
            plan_id=str(plan["id"]), active_only=True
        )
        public_lines = [_public_line(ln) for ln in lines]
        agg = _aggregate_lines(lines)
        keys = (
            "id",
            "exercise_id",
            "unit_id",
            "area_id",
            "cost_center_id",
            "status",
            "version",
            "submitted_by",
            "submitted_at",
            "reviewed_by",
            "reviewed_at",
            "decision_comment",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        )
        out = {k: plan.get(k) for k in keys}
        out["branch"] = plan.get("unit_id")
        out["lines"] = public_lines
        out.update(agg)
        return out

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
        except PersonnelResponsibilityRequiredError:
            raise PersonnelPlanNotFoundError(
                "Planejamento de Pessoal não encontrado."
            ) from None

    def _assert_plan_editable(self, plan_id: str) -> dict[str, Any]:
        return assert_personnel_plan_allows_mutation(self._repo, plan_id=plan_id)

    def resolve_plan(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str,
        cost_center_id: str,
        unit_id: str | None = None,
    ) -> dict[str, Any]:
        _require_edit(actor)
        self._assert_unlocked(actor)
        exercise_id = str(exercise_id or "").strip()
        cost_center_id = str(cost_center_id or "").strip()
        unit_id_raw = str(unit_id or "").strip() or None
        if not exercise_id or not cost_center_id:
            raise PersonnelPlanInvalidError(
                "Exercício e centro de custo são obrigatórios."
            )
        if not unit_id_raw:
            raise PersonnelPlanInvalidError(
                "Filial (unit_id) é obrigatória para resolver o plano de Pessoal."
            )

        exercise = self._repo.get_exercise(exercise_id)
        if not exercise:
            raise PersonnelPlanInvalidError("Exercício orçamentário não encontrado.")
        if str(exercise.get("status") or "") == "archived":
            raise PersonnelPlanInvalidError(
                "Exercício arquivado não permite planejamento de Pessoal."
            )

        # Filial/CC primeiro (mismatch estável), depois responsabilidade.
        org = self._resolve_org(cost_center_id, unit_id=unit_id_raw)
        self._assert_responsibility(
            actor,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=org["unit_id"],
        )

        existing = self._repo.get_personnel_plan_by_exercise_cc(
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=org["unit_id"],
        )
        if existing:
            enriched = self._enrich_plan(existing)
            self._repo.append_audit(
                exercise_id=exercise_id,
                entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
                entity_id=existing["id"],
                action=AUDIT_PLAN_RESOLVED,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state={
                    "id": existing["id"],
                    "unit_id": existing.get("unit_id"),
                    "cost_center_id": existing.get("cost_center_id"),
                    "created": False,
                },
            )
            return enriched

        try:
            created = self._repo.create_personnel_plan(
                {
                    "exercise_id": exercise_id,
                    "unit_id": org["unit_id"],
                    "area_id": org["area_id"],
                    "cost_center_id": cost_center_id,
                    "created_by": actor.user_id,
                }
            )
        except PluginsRepositoryError:
            raced = self._repo.get_personnel_plan_by_exercise_cc(
                exercise_id=exercise_id,
                cost_center_id=cost_center_id,
                unit_id=org["unit_id"],
            )
            if raced:
                return self._enrich_plan(raced)
            raise

        self._repo.append_personnel_plan_history(
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
        enriched = self._enrich_plan(created)
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
            entity_id=created["id"],
            action=AUDIT_PLAN_CREATED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state={
                "id": created["id"],
                "unit_id": created.get("unit_id"),
                "cost_center_id": created.get("cost_center_id"),
                "status": STATUS_DRAFT,
                "created": True,
            },
        )
        return enriched

    def list_plans(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        unit_id: str | None = None,
        cost_center_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _require_view(actor)
        self._assert_unlocked(actor)
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 50)))
        allowed = self._authorized_pairs(actor, exercise_id=exercise_id)
        if cost_center_id and not self._pair_authorized(
            allowed, cost_center_id=cost_center_id, unit_id=unit_id
        ):
            raise PersonnelResponsibilityRequiredError(
                "Sem responsabilidade orçamentária de Pessoal para o filtro informado."
            )
        items, total = self._repo.list_personnel_plans(
            exercise_id=exercise_id,
            unit_id=unit_id,
            cost_center_id=cost_center_id,
            unit_cost_center_pairs=allowed,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        return {
            "items": [self._enrich_plan(i) for i in items],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": (page * page_size) < total,
            },
        }

    def get_plan(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        _require_view(actor)
        self._assert_unlocked(actor)
        plan = self._repo.get_personnel_plan(plan_id)
        if not plan:
            raise PersonnelPlanNotFoundError("Planejamento de Pessoal não encontrado.")
        self._assert_can_view_plan(actor, plan)
        return self._enrich_plan(plan)

    def create_line(
        self, actor: BudgetActor, plan_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        _require_edit(actor)
        self._assert_unlocked(actor)
        plan = self._assert_plan_editable(plan_id)
        self._assert_responsibility(
            actor,
            exercise_id=str(plan["exercise_id"]),
            cost_center_id=str(plan["cost_center_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
        )

        position_name = _normalize_position_name(body.get("position_name"))
        existing = self._repo.get_personnel_plan_line_by_plan_position_name(
            plan_id=plan_id, position_name=position_name, active_only=True
        )
        if existing:
            raise PersonnelLineDuplicatePositionError(
                "Já existe linha ativa para este cargo neste plano."
            )

        payload: dict[str, Any] = {
            "plan_id": plan_id,
            "position_name": position_name,
            "observations": (
                None
                if body.get("observations") is None
                else (str(body.get("observations") or "").strip() or None)
            ),
            "created_by": actor.user_id,
            "updated_by": actor.user_id,
        }
        for field in HEADCOUNT_FIELDS:
            if field in body:
                payload[field] = _parse_headcount(body.get(field), field)
            else:
                payload[field] = None

        try:
            created = self._repo.create_personnel_plan_line(payload)
        except PluginsRepositoryError as exc:
            msg = str(exc).lower()
            if "duplicate" in msg or "unique" in msg:
                raise PersonnelLineDuplicatePositionError(
                    "Já existe linha ativa para este cargo neste plano."
                ) from exc
            raise

        public = _public_line(created)
        self._repo.append_audit(
            exercise_id=str(plan["exercise_id"]),
            entity_type=ENTITY_TYPE_PERSONNEL_PLAN_LINE,
            entity_id=created["id"],
            action=AUDIT_LINE_CREATED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=public,
        )
        return public

    def update_line(
        self, actor: BudgetActor, line_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        _require_edit(actor)
        self._assert_unlocked(actor)
        current = self._repo.get_personnel_plan_line(line_id)
        if not current or not current.get("is_active"):
            raise PersonnelLineNotFoundError("Linha de Pessoal não encontrada.")
        plan = self._assert_plan_editable(str(current["plan_id"]))
        self._assert_responsibility(
            actor,
            exercise_id=str(plan["exercise_id"]),
            cost_center_id=str(plan["cost_center_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
        )

        if "version" not in body:
            raise PersonnelPlanInvalidError(
                "Campo version é obrigatório para atualização (autosave/concorrência)."
            )
        try:
            expected_version = int(body["version"])
        except (TypeError, ValueError) as exc:
            raise PersonnelPlanInvalidError("version inválida.") from exc

        fields: dict[str, Any] = {"updated_by": actor.user_id}
        if "observations" in body:
            obs = body["observations"]
            fields["observations"] = (
                None if obs is None else (str(obs).strip() or None)
            )
        for field in HEADCOUNT_FIELDS:
            if field in body:
                fields[field] = _parse_headcount(body.get(field), field)

        if "position_name" in body:
            new_name = _normalize_position_name(body.get("position_name"))
            current_key = _position_name_key(str(current.get("position_name") or ""))
            if _position_name_key(new_name) != current_key:
                clash = self._repo.get_personnel_plan_line_by_plan_position_name(
                    plan_id=str(current["plan_id"]),
                    position_name=new_name,
                    active_only=True,
                )
                if clash and str(clash.get("id")) != line_id:
                    raise PersonnelLineDuplicatePositionError(
                        "Já existe linha ativa para este cargo neste plano."
                    )
            fields["position_name"] = new_name

        try:
            updated = self._repo.update_personnel_plan_line(
                line_id, fields, expected_version=expected_version
            )
        except PluginsRepositoryError as exc:
            msg = str(exc).lower()
            if "duplicate" in msg or "unique" in msg:
                raise PersonnelLineDuplicatePositionError(
                    "Já existe linha ativa para este cargo neste plano."
                ) from exc
            if "conflito" in msg or "versão" in msg or "version" in msg:
                self._repo.append_audit(
                    exercise_id=str(plan["exercise_id"]),
                    entity_type=ENTITY_TYPE_PERSONNEL_PLAN_LINE,
                    entity_id=line_id,
                    action=AUDIT_LINE_VERSION_CONFLICT,
                    actor_user_id=actor.user_id,
                    actor_name=actor.user_name,
                    before_state=_public_line(current),
                    after_state={"expected_version": expected_version},
                )
                raise PersonnelLineVersionConflictError(
                    "Conflito de versão da linha de Pessoal. Recarregue e tente novamente."
                ) from exc
            raise

        public = _public_line(updated)
        self._repo.append_audit(
            exercise_id=str(plan["exercise_id"]),
            entity_type=ENTITY_TYPE_PERSONNEL_PLAN_LINE,
            entity_id=line_id,
            action=AUDIT_LINE_UPDATED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_line(current),
            after_state=public,
        )
        return public

    def archive_line(self, actor: BudgetActor, line_id: str) -> dict[str, Any]:
        _require_edit(actor)
        self._assert_unlocked(actor)
        current = self._repo.get_personnel_plan_line(line_id)
        if not current or not current.get("is_active"):
            raise PersonnelLineNotFoundError("Linha de Pessoal não encontrada.")
        plan = self._assert_plan_editable(str(current["plan_id"]))
        self._assert_responsibility(
            actor,
            exercise_id=str(plan["exercise_id"]),
            cost_center_id=str(plan["cost_center_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
        )
        archived = self._repo.archive_personnel_plan_line(
            line_id, actor_id=actor.user_id
        )
        public = _public_line(archived)
        self._repo.append_audit(
            exercise_id=str(plan["exercise_id"]),
            entity_type=ENTITY_TYPE_PERSONNEL_PLAN_LINE,
            entity_id=line_id,
            action=AUDIT_LINE_ARCHIVED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_line(current),
            after_state=public,
        )
        return public

    # ---- Workflow (Fase 3C.1) ----

    def _validate_for_submit(self, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not lines:
            raise PersonnelPlanIncompleteError(
                "É necessário ao menos uma linha ativa para submeter.",
                incomplete_lines=[],
            )
        incomplete: list[dict[str, Any]] = []
        for row in lines:
            missing: list[str] = []
            name = str(row.get("position_name") or "").strip()
            if not name:
                missing.append("position_name")
            for field in HEADCOUNT_FIELDS:
                value = row.get(field)
                if value is None:
                    missing.append(field)
                elif isinstance(value, (int, float)) and int(value) < 0:
                    missing.append(field)
            if missing:
                incomplete.append(
                    {
                        "id": row.get("id"),
                        "position_name": row.get("position_name"),
                        "missing_fields": missing,
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
        _require_view(actor)
        self._assert_unlocked(actor)
        if not _can_submit(actor):
            raise PersonnelApprovalForbiddenError(
                "Sem permissão para submeter o Orçamento de Pessoal."
            )

        plan = self._repo.get_personnel_plan(plan_id)
        if not plan:
            raise PersonnelPlanNotFoundError("Planejamento de Pessoal não encontrado.")
        self._assert_responsibility(
            actor,
            exercise_id=str(plan["exercise_id"]),
            cost_center_id=str(plan["cost_center_id"]),
            unit_id=str(plan.get("unit_id") or "") or None,
        )

        exercise = self._repo.get_exercise(str(plan["exercise_id"]))
        if not exercise or str(exercise.get("status") or "") not in {"open", "closing"}:
            raise PersonnelPlanInvalidError(
                "Exercício precisa estar aberto (ou em encerramento) para submissão."
            )

        current_status = str(plan.get("status") or "")
        target = PLAN_TRANSITIONS.get((current_status, "submit"))
        if not target:
            raise PersonnelPlanInvalidTransitionError(
                f"Não é possível submeter a partir do status '{current_status}'."
            )

        if int(plan.get("version") or 0) != int(version):
            self._repo.append_audit(
                exercise_id=str(plan["exercise_id"]),
                entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
                entity_id=plan_id,
                action=AUDIT_PLAN_VERSION_CONFLICT,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=self._enrich_plan(plan),
                after_state={"expected_version": version},
            )
            raise PersonnelPlanVersionConflictError(
                "O planejamento foi alterado em outra sessão. Recarregue e tente novamente."
            )

        lines = self._repo.list_personnel_plan_lines(plan_id=plan_id, active_only=True)
        incomplete = self._validate_for_submit(lines)
        if incomplete:
            raise PersonnelPlanIncompleteError(
                "Há linhas incompletas ou inválidas. Corrija antes de submeter.",
                incomplete_lines=incomplete,
            )

        try:
            updated = self._repo.transition_personnel_plan(
                plan_id,
                expected_version=int(version),
                new_status=STATUS_SUBMITTED,
                actor_id=actor.user_id,
                submitted_by=actor.user_id,
                clear_review=True,
                decision_comment=(comment.strip() if comment else None),
            )
        except PluginsRepositoryError as exc:
            raise PersonnelPlanVersionConflictError(
                "Conflito de versão do planejamento de Pessoal."
            ) from exc

        self._repo.append_personnel_plan_history(
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
            entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
            entity_id=plan_id,
            action=AUDIT_PLAN_SUBMITTED,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=self._enrich_plan(plan),
            after_state=self._enrich_plan(updated),
        )
        return self._enrich_plan(updated)

    def list_history(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        plan = self.get_plan(actor, plan_id)
        rows = self._repo.list_personnel_plan_history(str(plan["id"]))
        return {"items": [_public_history(r) for r in rows]}

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
        _require_view(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise PersonnelApprovalForbiddenError(
                "Sem permissão para acessar a fila de aprovação de Pessoal."
            )
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 50)))
        filter_status = status or STATUS_SUBMITTED
        items, total = self._repo.list_personnel_plans(
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
            "items": [self._enrich_plan(i) for i in items],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": (page * page_size) < total,
            },
        }

    def get_review_detail(self, actor: BudgetActor, plan_id: str) -> dict[str, Any]:
        _require_view(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise PersonnelApprovalForbiddenError(
                "Sem permissão para revisar o Orçamento de Pessoal."
            )
        plan = self._repo.get_personnel_plan(plan_id)
        if not plan:
            raise PersonnelPlanNotFoundError("Planejamento de Pessoal não encontrado.")
        return self._enrich_plan(plan)

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
        _require_view(actor)
        self._assert_unlocked(actor)
        if not _can_approve(actor):
            raise PersonnelApprovalForbiddenError(
                "Sem permissão para decidir sobre o Orçamento de Pessoal."
            )

        plan = self._repo.get_personnel_plan(plan_id)
        if not plan:
            raise PersonnelPlanNotFoundError("Planejamento de Pessoal não encontrado.")

        current_status = str(plan.get("status") or "")
        if current_status == STATUS_APPROVED and action == "approve":
            raise PersonnelPlanAlreadyApprovedError(
                "Este planejamento de Pessoal já está aprovado."
            )

        target = PLAN_TRANSITIONS.get((current_status, action))
        if not target or target != new_status:
            raise PersonnelPlanInvalidTransitionError(
                f"Transição '{action}' inválida a partir de '{current_status}'."
            )

        if require_comment and not (comment or "").strip():
            raise PersonnelPlanCommentRequiredError(
                "Comentário/justificativa é obrigatório para esta decisão."
            )

        if plan.get("submitted_by") and str(plan["submitted_by"]) == actor.user_id:
            if not _is_admin(actor):
                raise PersonnelApprovalForbiddenError(
                    "Segregação de funções: quem submeteu não pode decidir o próprio planejamento."
                )

        if int(plan.get("version") or 0) != int(version):
            self._repo.append_audit(
                exercise_id=str(plan["exercise_id"]),
                entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
                entity_id=plan_id,
                action=AUDIT_PLAN_VERSION_CONFLICT,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=self._enrich_plan(plan),
                after_state={"expected_version": version, "action": action},
            )
            raise PersonnelPlanVersionConflictError(
                "O planejamento foi alterado em outra sessão. Recarregue e tente novamente."
            )

        try:
            updated = self._repo.transition_personnel_plan(
                plan_id,
                expected_version=int(version),
                new_status=new_status,
                actor_id=actor.user_id,
                reviewed_by=actor.user_id,
                decision_comment=(comment.strip() if comment else None),
            )
        except PluginsRepositoryError as exc:
            raise PersonnelPlanVersionConflictError(
                "Conflito de versão do planejamento de Pessoal."
            ) from exc

        self._repo.append_personnel_plan_history(
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
            entity_type=ENTITY_TYPE_PERSONNEL_PLAN,
            entity_id=plan_id,
            action=audit_action,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=self._enrich_plan(plan),
            after_state=self._enrich_plan(updated),
        )
        return self._enrich_plan(updated)

    def request_changes(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str,
    ) -> dict[str, Any]:
        return self._decide(
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

    def reject_plan(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str,
    ) -> dict[str, Any]:
        return self._decide(
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

    def approve_plan(
        self,
        actor: BudgetActor,
        plan_id: str,
        *,
        version: int,
        comment: str | None = None,
    ) -> dict[str, Any]:
        return self._decide(
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
