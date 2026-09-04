"""Casos de uso — responsabilidades orçamentárias por centro de custo (Fase 2A.1)."""

from __future__ import annotations

from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder

from datetime import date
from typing import Any

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterAmbiguousError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetExerciseNotFoundError,
    BudgetResponsibilityConflictError,
    BudgetResponsibilityForbiddenError,
    BudgetResponsibilityInvalidError,
    BudgetResponsibilityNotFoundError,
    BudgetUserNotAuthorizedError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_resolution import (
    resolve_org_cost_center,
)
from app.domain.services.planejamento_orcamentario.responsibility_constants import (
    ALLOWED_BUDGET_MODULES,
    ALLOWED_RESPONSIBILITY_TYPES,
    BUDGET_MODULE_CAPEX,
    EXERCISE_STATUSES_BLOCKING_RESPONSIBILITY,
)
from app.domain.services.planejamento_orcamentario.responsibility_guard import (
    BudgetResponsibilityGuard,
)
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)


def _parse_date(value: Any, field: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise BudgetResponsibilityInvalidError(f"Data inválida em {field}.") from exc


def _require_admin_or_scopes(actor: BudgetActor) -> None:
    if not (
        actor.permissions
        & {
            "planejamento-orcamentario.scopes.manage",
            "planejamento-orcamentario.admin",
        }
    ):
        raise BudgetUserNotAuthorizedError(
            "Sem permissão administrativa para gerenciar responsabilidades orçamentárias."
        )


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    """Snapshot seguro — sem tokens ou payloads de diretório."""
    keys = (
        "id",
        "exercise_id",
        "module",
        "user_sub",
        "user_name_snapshot",
        "user_email_snapshot",
        "unit_id",
        "area_id",
        "cost_center_id",
        "responsibility_type",
        "valid_from",
        "valid_until",
        "is_active",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "deactivated_by",
        "deactivated_at",
        "deactivation_reason",
    )
    out = {k: row.get(k) for k in keys}
    out["branch"] = row.get("unit_id")
    name = str(row.get("cost_center_name") or "").strip() or None
    icon_raw = row.get("cost_center_icon_key")
    icon_key = str(icon_raw).strip().lower() if icon_raw else None
    out["cost_center_name"] = name
    out["cost_center_icon_key"] = icon_key
    return out


class BudgetResponsibilityUseCases:
    def __init__(self, repository: PostgresBudgetPlanningRepository | None = None) -> None:
        self._repo = repository or PostgresBudgetPlanningRepository()
        self._guard = BudgetResponsibilityGuard(self._repo)

    def assert_user_has_budget_responsibility(
        self,
        user_sub: str,
        exercise_id: str,
        module: str,
        cost_center_id: str,
        *,
        unit_id: str | None = None,
    ) -> dict[str, Any]:
        return self._guard.assert_user_has_budget_responsibility(
            user_sub,
            exercise_id,
            module,
            cost_center_id,
            unit_id=unit_id,
        )

    def _validate_exercise(self, exercise_id: str) -> dict[str, Any]:
        exercise = self._repo.get_exercise(exercise_id)
        if not exercise:
            raise BudgetExerciseNotFoundError("Exercício orçamentário não encontrado.")
        if str(exercise.get("status") or "") in EXERCISE_STATUSES_BLOCKING_RESPONSIBILITY:
            raise BudgetResponsibilityInvalidError(
                "Exercício arquivado não aceita vínculos de responsabilidade."
            )
        return exercise

    def _validate_org_hierarchy(
        self, *, unit_id: str, area_id: str | None, cost_center_id: str
    ) -> dict[str, Any]:
        unit = self._repo.get_org_unit(unit_id)
        if not unit or not unit.get("active", True):
            raise BudgetResponsibilityInvalidError(
                "Unidade inexistente ou inativa no catálogo interno."
            )
        try:
            cc = resolve_org_cost_center(
                self._repo,
                code=cost_center_id,
                unit_id=unit_id,
                require_active=True,
            )
        except BudgetCostCenterAmbiguousError as exc:
            raise BudgetResponsibilityInvalidError(str(exc)) from exc
        except (BudgetCostCenterNotFoundError, BudgetCostCenterInvalidError) as exc:
            raise BudgetResponsibilityInvalidError(str(exc)) from exc
        branch = str(cc.get("branch") or cc.get("unit_code") or "").strip()
        if branch and branch != unit_id:
            raise BudgetResponsibilityInvalidError(
                "Unidade incompatível com o centro de custo selecionado."
            )
        area_code = (area_id or "").strip() or None
        cc_area = (cc.get("area_code") or None)
        if area_code:
            area = self._repo.get_org_area(area_code)
            if not area or not area.get("active", True):
                raise BudgetResponsibilityInvalidError(
                    "Área inexistente ou inativa no catálogo interno."
                )
            if area.get("unit_code") and str(area.get("unit_code")) != unit_id:
                raise BudgetResponsibilityInvalidError(
                    "Área incompatível com a unidade selecionada."
                )
            if cc_area and str(cc_area) != area_code:
                raise BudgetResponsibilityInvalidError(
                    "Área incompatível com o centro de custo selecionado."
                )
        elif cc_area:
            # Preenche área canônica do CC quando omitida
            area_code = str(cc_area)
        return {"unit": unit, "cost_center": cc, "area_id": area_code}

    def _normalize_module(self, module: str | None) -> str:
        value = (module or BUDGET_MODULE_CAPEX).strip().lower()
        if value not in ALLOWED_BUDGET_MODULES:
            raise BudgetResponsibilityInvalidError(
                "Nesta fase somente o módulo 'capex' é permitido."
            )
        return value

    def _normalize_type(self, responsibility_type: str | None) -> str:
        value = (responsibility_type or "").strip().lower()
        if value not in ALLOWED_RESPONSIBILITY_TYPES:
            raise BudgetResponsibilityInvalidError(
                "Tipo de responsabilidade inválido (use owner ou collaborator)."
            )
        return value

    def create_responsibility(self, actor: BudgetActor, body: dict[str, Any]) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        exercise_id = str(body.get("exercise_id") or "").strip()
        self._validate_exercise(exercise_id)
        module = self._normalize_module(body.get("module"))
        responsibility_type = self._normalize_type(body.get("responsibility_type"))
        user_sub = str(body.get("user_sub") or "").strip()
        if not user_sub or len(user_sub) < 3:
            raise BudgetResponsibilityInvalidError(
                "Identificador de usuário (sub) inválido. Selecione um usuário do diretório."
            )
        unit_id = str(body.get("unit_id") or "").strip()
        cost_center_id = str(body.get("cost_center_id") or "").strip()
        if not unit_id or not cost_center_id:
            raise BudgetResponsibilityInvalidError(
                "Unidade e centro de custo do catálogo são obrigatórios."
            )
        area_raw = body.get("area_id")
        org = self._validate_org_hierarchy(
            unit_id=unit_id,
            area_id=str(area_raw).strip() if area_raw else None,
            cost_center_id=cost_center_id,
        )
        valid_from = _parse_date(body.get("valid_from"), "valid_from")
        valid_until = _parse_date(body.get("valid_until"), "valid_until")
        if valid_from and valid_until and valid_until < valid_from:
            raise BudgetResponsibilityInvalidError(
                "Data final da vigência não pode ser anterior à inicial."
            )
        conflict = self._repo.find_active_budget_responsibility_conflict(
            exercise_id=exercise_id,
            module=module,
            user_sub=user_sub,
            cost_center_id=cost_center_id,
            unit_id=unit_id,
        )
        if conflict:
            raise BudgetResponsibilityConflictError(
                "Já existe responsabilidade ativa para este usuário, módulo e centro de custo."
            )
        created = self._repo.create_budget_responsibility(
            {
                "exercise_id": exercise_id,
                "module": module,
                "user_sub": user_sub,
                "user_name_snapshot": (str(body["user_name_snapshot"]).strip() if body.get("user_name_snapshot") else None),
                "user_email_snapshot": (str(body["user_email_snapshot"]).strip() if body.get("user_email_snapshot") else None),
                "unit_id": unit_id,
                "area_id": org["area_id"],
                "cost_center_id": cost_center_id,
                "responsibility_type": responsibility_type,
                "valid_from": valid_from,
                "valid_until": valid_until,
                "created_by": actor.user_id,
                "updated_by": actor.user_id,
            }
        )
        public = _public_row(created)
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type="budget_responsibility",
            entity_id=created["id"],
            action="responsibility.created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=public,
        )
        return public

    def list_responsibilities(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        module: str | None = None,
        user_sub: str | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        responsibility_type: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 50)))
        offset = (page - 1) * page_size
        module_norm = self._normalize_module(module) if module else None
        type_norm = (
            self._normalize_type(responsibility_type) if responsibility_type else None
        )
        items, total = self._repo.list_budget_responsibilities(
            exercise_id=exercise_id or None,
            module=module_norm,
            user_sub=(user_sub or None),
            unit_id=(unit_id or None),
            area_id=(area_id or None),
            cost_center_id=(cost_center_id or None),
            responsibility_type=type_norm,
            is_active=is_active,
            offset=offset,
            limit=page_size,
        )
        return {
            "items": [_public_row(i) for i in items],
            "pagination": PaginationEnvelopeBuilder.build(
                shape="paged_count",
                page=page,
                page_size=page_size,
                total=total,
                extra={"has_more": offset + len(items) < total},
            ),
        }

    def get_responsibility(self, actor: BudgetActor, responsibility_id: str) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        row = self._repo.get_budget_responsibility(responsibility_id)
        if not row:
            raise BudgetResponsibilityNotFoundError("Responsabilidade orçamentária não encontrada.")
        return _public_row(row)

    def update_responsibility(
        self, actor: BudgetActor, responsibility_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_budget_responsibility(responsibility_id)
        if not current:
            raise BudgetResponsibilityNotFoundError("Responsabilidade orçamentária não encontrada.")
        if not current.get("is_active"):
            raise BudgetResponsibilityInvalidError(
                "Responsabilidade inativa. Reative antes de alterar tipo ou vigência."
            )
        fields: dict[str, Any] = {"updated_by": actor.user_id}
        actions: list[str] = []
        if "responsibility_type" in body and body["responsibility_type"] is not None:
            fields["responsibility_type"] = self._normalize_type(body["responsibility_type"])
            if fields["responsibility_type"] != current.get("responsibility_type"):
                actions.append("responsibility.type_changed")
        if "valid_from" in body or "valid_until" in body:
            valid_from = _parse_date(
                body["valid_from"] if "valid_from" in body else current.get("valid_from"),
                "valid_from",
            )
            valid_until = _parse_date(
                body["valid_until"] if "valid_until" in body else current.get("valid_until"),
                "valid_until",
            )
            if valid_from and valid_until and valid_until < valid_from:
                raise BudgetResponsibilityInvalidError(
                    "Data final da vigência não pode ser anterior à inicial."
                )
            fields["valid_from"] = valid_from
            fields["valid_until"] = valid_until
            actions.append("responsibility.validity_changed")
        for snap_key in ("user_name_snapshot", "user_email_snapshot"):
            if snap_key in body:
                fields[snap_key] = (
                    str(body[snap_key]).strip() if body.get(snap_key) else None
                )
        updated = self._repo.update_budget_responsibility(responsibility_id, fields)
        public = _public_row(updated)
        before = _public_row(current)
        if not actions:
            actions = ["responsibility.updated"]
        for action in actions:
            self._repo.append_audit(
                exercise_id=current["exercise_id"],
                entity_type="budget_responsibility",
                entity_id=responsibility_id,
                action=action,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=before,
                after_state=public,
            )
        return public

    def deactivate_responsibility(
        self,
        actor: BudgetActor,
        responsibility_id: str,
        *,
        reason: str | None = None,
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_budget_responsibility(responsibility_id)
        if not current:
            raise BudgetResponsibilityNotFoundError("Responsabilidade orçamentária não encontrada.")
        if not current.get("is_active"):
            return _public_row(current)
        updated = self._repo.deactivate_budget_responsibility(
            responsibility_id,
            actor_id=actor.user_id,
            reason=(reason or "").strip() or None,
        )
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=current["exercise_id"],
            entity_type="budget_responsibility",
            entity_id=responsibility_id,
            action="responsibility.deactivated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public

    def reactivate_responsibility(
        self, actor: BudgetActor, responsibility_id: str
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_budget_responsibility(responsibility_id)
        if not current:
            raise BudgetResponsibilityNotFoundError("Responsabilidade orçamentária não encontrada.")
        if current.get("is_active"):
            return _public_row(current)
        self._validate_exercise(str(current["exercise_id"]))
        conflict = self._repo.find_active_budget_responsibility_conflict(
            exercise_id=str(current["exercise_id"]),
            module=str(current["module"]),
            user_sub=str(current["user_sub"]),
            cost_center_id=str(current["cost_center_id"]),
            unit_id=str(current.get("unit_id") or "") or None,
            exclude_id=responsibility_id,
        )
        if conflict:
            raise BudgetResponsibilityConflictError(
                "Reativação conflita com outro vínculo ativo para o mesmo usuário e centro de custo."
            )
        # Revalida catálogo
        self._validate_org_hierarchy(
            unit_id=str(current["unit_id"]),
            area_id=current.get("area_id"),
            cost_center_id=str(current["cost_center_id"]),
        )
        updated = self._repo.reactivate_budget_responsibility(
            responsibility_id, actor_id=actor.user_id
        )
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=current["exercise_id"],
            entity_type="budget_responsibility",
            entity_id=responsibility_id,
            action="responsibility.reactivated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public

    def list_my_responsibilities(
        self,
        actor: BudgetActor,
        *,
        module: str | None = None,
        exercise_id: str | None = None,
    ) -> dict[str, Any]:
        """Consulta pessoal — user_sub sempre do JWT (actor), nunca do body/query."""
        if not actor.user_id or actor.user_id == "unknown":
            raise BudgetResponsibilityForbiddenError(
                "Usuário autenticado obrigatório."
            )
        if "planejamento-orcamentario.access" not in actor.permissions and (
            "planejamento-orcamentario.admin" not in actor.permissions
        ):
            raise BudgetUserNotAuthorizedError(
                "Sem permissão de acesso ao Planejamento Orçamentário."
            )
        module_norm = self._normalize_module(module) if module else BUDGET_MODULE_CAPEX
        items = self._repo.list_budget_responsibilities_for_user(
            user_sub=actor.user_id,
            module=module_norm,
            exercise_id=exercise_id,
            active_only=True,
        )
        return {
            "user_sub": actor.user_id,
            "module": module_norm,
            "items": [_public_row(i) for i in items],
        }
