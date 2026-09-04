"""Casos de uso — consolidação gerencial CAPEX e exportação Excel (Fase 2D.1)."""

from __future__ import annotations

from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder

from datetime import date, datetime, timezone
from typing import Any

from app.application.services.planejamento_orcamentario.capex_consolidation_excel_builder import (
    build_capex_consolidation_workbook,
)
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.capex_consolidation_constants import (
    ALLOWED_GROUP_BY,
    AUDIT_CONSOLIDATION_EXPORT,
    AUDIT_CONSOLIDATION_SUMMARY,
    DETAILS_SORT_FIELDS,
    ENTITY_TYPE_CAPEX_CONSOLIDATION,
    GROUP_BY_AREA,
    GROUP_BY_CATEGORY,
    GROUP_BY_COST_CENTER,
    GROUP_BY_MONTH,
    GROUP_BY_ORIGIN,
    GROUP_BY_PLAN_STATUS,
    GROUP_BY_PRIORITY,
    GROUP_BY_UNIT,
)
from app.domain.services.planejamento_orcamentario.capex_consolidation_service import (
    build_detail_item,
    build_grouping,
    build_summary,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetExerciseNotFoundError,
    BudgetUserNotAuthorizedError,
    CapexConsolidationForbiddenError,
    CapexConsolidationInvalidError,
    CapexExportForbiddenError,
    CapexInvestmentCostCenterForbiddenError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_resolution import (
    authorized_unit_cost_center_pairs,
)
from app.domain.services.planejamento_orcamentario.responsibility_constants import (
    BUDGET_MODULE_CAPEX,
)
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)

PERM_ACCESS = "planejamento-orcamentario.access"
PERM_ADMIN = "planejamento-orcamentario.admin"
PERM_CONSOLIDATION = "planejamento-orcamentario.capex.consolidation.view"
PERM_EXPORT = "planejamento-orcamentario.capex.export"
PERM_APPROVE = "planejamento-orcamentario.capex.approve"
PERM_SUBMIT = "planejamento-orcamentario.capex.submit"


class CapexConsolidationUseCases:
    def __init__(self, repository: PostgresBudgetPlanningRepository) -> None:
        self._repo = repository

    def _is_admin(self, actor: BudgetActor) -> bool:
        return PERM_ADMIN in actor.permissions

    def _can_consolidate(self, actor: BudgetActor) -> bool:
        return PERM_CONSOLIDATION in actor.permissions or self._is_admin(actor)

    def _can_export(self, actor: BudgetActor) -> bool:
        return PERM_EXPORT in actor.permissions or self._is_admin(actor)

    def _has_base_access(self, actor: BudgetActor) -> bool:
        return bool(
            actor.permissions
            & {
                PERM_ACCESS,
                PERM_ADMIN,
                PERM_CONSOLIDATION,
                PERM_EXPORT,
                PERM_APPROVE,
                PERM_SUBMIT,
                "planejamento-orcamentario.guidance.view",
                "planejamento-orcamentario.guidance.manage",
                "planejamento-orcamentario.scopes.manage",
            }
        )

    def _require_base_access(self, actor: BudgetActor) -> None:
        if not self._has_base_access(actor):
            raise BudgetUserNotAuthorizedError(
                "Usuário sem permissão para o Planejamento Orçamentário."
            )

    def _require_consolidation(self, actor: BudgetActor) -> None:
        self._require_base_access(actor)
        # Gestor comum (só access/submit) pode ver consolidação do próprio escopo.
        # Consolidação ampla exige .consolidation.view ou admin.
        if self._can_consolidate(actor):
            return
        if PERM_ACCESS in actor.permissions or PERM_SUBMIT in actor.permissions:
            return
        raise CapexConsolidationForbiddenError(
            "Sem permissão para consolidação gerencial CAPEX."
        )

    def _require_export(self, actor: BudgetActor) -> None:
        self._require_base_access(actor)
        if not self._can_export(actor):
            raise CapexExportForbiddenError(
                "Sem permissão para exportar consolidação CAPEX."
            )

    def _authorized_cost_centers(
        self, actor: BudgetActor
    ) -> list[tuple[str, str]] | None:
        """None = sem restrição de CC (consolidação gerencial / admin)."""
        if self._can_consolidate(actor):
            return None
        rows = self._repo.list_budget_responsibilities_for_user(
            user_sub=actor.user_id,
            module=BUDGET_MODULE_CAPEX,
        )
        return authorized_unit_cost_center_pairs(rows)

    def _resolve_exercise(self, exercise_id: str | None, year: int | None) -> dict[str, Any]:
        if exercise_id:
            exercise = self._repo.get_exercise(exercise_id)
            if not exercise:
                raise BudgetExerciseNotFoundError("Exercício não encontrado.")
            return exercise
        if year is not None:
            exercise = self._repo.get_exercise_by_year(int(year))
            if not exercise:
                raise BudgetExerciseNotFoundError("Exercício não encontrado.")
            return exercise
        raise CapexConsolidationInvalidError(
            "Informe exercise_id ou year para a consolidação CAPEX."
        )

    def _normalize_filters(
        self,
        *,
        exercise_id: str,
        unit_id: str | None,
        area_id: str | None,
        cost_center_id: str | None,
        category_id: str | None,
        priority: str | None,
        origin: str | None,
        plan_status: str | None,
        required_date_from: str | None,
        required_date_to: str | None,
        unit_cost_center_pairs: list[tuple[str, str]] | None,
    ) -> dict[str, Any]:
        if cost_center_id and unit_cost_center_pairs is not None:
            if unit_id:
                if (unit_id, cost_center_id) not in unit_cost_center_pairs:
                    raise CapexInvestmentCostCenterForbiddenError(
                        "Centro de custo fora do escopo do usuário."
                    )
            elif not any(cc == cost_center_id for _, cc in unit_cost_center_pairs):
                raise CapexInvestmentCostCenterForbiddenError(
                    "Centro de custo fora do escopo do usuário."
                )
        return {
            "exercise_id": exercise_id,
            "unit_id": (unit_id or None),
            "area_id": (area_id or None),
            "cost_center_id": (cost_center_id or None),
            "category_id": (category_id or None),
            "priority": (priority or None),
            "origin": (origin or None),
            "plan_status": (plan_status or None),
            "required_date_from": (required_date_from or None),
            "required_date_to": (required_date_to or None),
            "unit_cost_center_pairs": unit_cost_center_pairs,
        }

    def _fetch_all_rows(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        items, _total = self._repo.list_capex_consolidation_rows(
            exercise_id=filters["exercise_id"],
            unit_id=filters.get("unit_id"),
            area_id=filters.get("area_id"),
            cost_center_id=filters.get("cost_center_id"),
            category_id=filters.get("category_id"),
            priority=filters.get("priority"),
            origin=filters.get("origin"),
            plan_status=filters.get("plan_status"),
            required_date_from=filters.get("required_date_from"),
            required_date_to=filters.get("required_date_to"),
            cost_center_ids=None,
            unit_cost_center_pairs=filters.get("unit_cost_center_pairs"),
            offset=None,
            limit=None,
        )
        return items

    def _public_filters(self, filters: dict[str, Any]) -> dict[str, Any]:
        out = {
            k: v
            for k, v in filters.items()
            if k != "unit_cost_center_pairs" and v is not None and v != ""
        }
        scoped = filters.get("unit_cost_center_pairs")
        if scoped is not None:
            out["scoped_to_responsibilities"] = True
            out["authorized_cost_center_count"] = len(scoped)
        return out

    def _prepare(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None,
        year: int | None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        plan_status: str | None = None,
        required_date_from: str | None = None,
        required_date_to: str | None = None,
        for_export: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        if for_export:
            self._require_export(actor)
        else:
            self._require_consolidation(actor)

        exercise = self._resolve_exercise(exercise_id, year)
        authorized = self._authorized_cost_centers(actor)
        if authorized is not None and not authorized:
            filters = self._normalize_filters(
                exercise_id=str(exercise["id"]),
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
                unit_cost_center_pairs=[],
            )
            return exercise, filters, []

        filters = self._normalize_filters(
            exercise_id=str(exercise["id"]),
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            priority=priority,
            origin=origin,
            plan_status=plan_status,
            required_date_from=required_date_from,
            required_date_to=required_date_to,
            unit_cost_center_pairs=authorized,
        )
        rows = self._fetch_all_rows(filters)
        return exercise, filters, rows

    def get_summary(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        year: int | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        plan_status: str | None = None,
        required_date_from: str | None = None,
        required_date_to: str | None = None,
        audit: bool = True,
    ) -> dict[str, Any]:
        exercise, filters, rows = self._prepare(
            actor,
            exercise_id=exercise_id,
            year=year,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            priority=priority,
            origin=origin,
            plan_status=plan_status,
            required_date_from=required_date_from,
            required_date_to=required_date_to,
        )
        summary = build_summary(rows)
        payload = {
            "exercise": {
                "id": exercise.get("id"),
                "year": exercise.get("year"),
                "name": exercise.get("name"),
                "status": exercise.get("status"),
            },
            "filters": self._public_filters(filters),
            "summary": summary,
        }
        if audit:
            self._repo.append_audit(
                exercise_id=str(exercise["id"]),
                entity_type=ENTITY_TYPE_CAPEX_CONSOLIDATION,
                entity_id=str(exercise["id"]),
                action=AUDIT_CONSOLIDATION_SUMMARY,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=None,
                after_state={
                    "filters": self._public_filters(filters),
                    "investment_count": summary["investment_count"],
                },
            )
        return payload

    def get_grouping(
        self,
        actor: BudgetActor,
        *,
        group_by: str,
        exercise_id: str | None = None,
        year: int | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        plan_status: str | None = None,
        required_date_from: str | None = None,
        required_date_to: str | None = None,
    ) -> dict[str, Any]:
        if group_by not in ALLOWED_GROUP_BY:
            raise CapexConsolidationInvalidError(
                f"Agrupamento inválido: {group_by}."
            )
        exercise, filters, rows = self._prepare(
            actor,
            exercise_id=exercise_id,
            year=year,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            priority=priority,
            origin=origin,
            plan_status=plan_status,
            required_date_from=required_date_from,
            required_date_to=required_date_to,
        )
        grouping = build_grouping(rows, group_by=group_by)
        return {
            "exercise": {
                "id": exercise.get("id"),
                "year": exercise.get("year"),
                "name": exercise.get("name"),
            },
            "filters": self._public_filters(filters),
            **grouping,
        }

    def list_details(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        year: int | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        plan_status: str | None = None,
        required_date_from: str | None = None,
        required_date_to: str | None = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "updated_at",
        sort_dir: str = "desc",
    ) -> dict[str, Any]:
        self._require_consolidation(actor)
        exercise = self._resolve_exercise(exercise_id, year)
        authorized = self._authorized_cost_centers(actor)
        if sort_by not in DETAILS_SORT_FIELDS:
            raise CapexConsolidationInvalidError("Campo de ordenação inválido.")
        if str(sort_dir).lower() not in {"asc", "desc"}:
            raise CapexConsolidationInvalidError("Direção de ordenação inválida.")
        page = max(1, int(page))
        page_size = min(max(1, int(page_size)), 200)
        offset = (page - 1) * page_size

        if authorized is not None and not authorized:
            return {
                "exercise": {
                    "id": exercise.get("id"),
                    "year": exercise.get("year"),
                    "name": exercise.get("name"),
                },
                "filters": self._public_filters(
                    self._normalize_filters(
                        exercise_id=str(exercise["id"]),
                        unit_id=unit_id,
                        area_id=area_id,
                        cost_center_id=cost_center_id,
                        category_id=category_id,
                        priority=priority,
                        origin=origin,
                        plan_status=plan_status,
                        required_date_from=required_date_from,
                        required_date_to=required_date_to,
                        unit_cost_center_pairs=[],
                    )
                ),
                "items": [],
                "pagination": PaginationEnvelopeBuilder.paged_count(
                page=page,
                page_size=page_size,
                total=0,
                total_pages=0,
            ),
            }

        filters = self._normalize_filters(
            exercise_id=str(exercise["id"]),
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            priority=priority,
            origin=origin,
            plan_status=plan_status,
            required_date_from=required_date_from,
            required_date_to=required_date_to,
            unit_cost_center_pairs=authorized,
        )
        rows, total = self._repo.list_capex_consolidation_rows(
            exercise_id=filters["exercise_id"],
            unit_id=filters.get("unit_id"),
            area_id=filters.get("area_id"),
            cost_center_id=filters.get("cost_center_id"),
            category_id=filters.get("category_id"),
            priority=filters.get("priority"),
            origin=filters.get("origin"),
            plan_status=filters.get("plan_status"),
            required_date_from=filters.get("required_date_from"),
            required_date_to=filters.get("required_date_to"),
            cost_center_ids=None,
            unit_cost_center_pairs=filters.get("unit_cost_center_pairs"),
            offset=offset,
            limit=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        items = [build_detail_item(r) for r in rows]
        total_pages = (total + page_size - 1) // page_size if total else 0
        return {
            "exercise": {
                "id": exercise.get("id"),
                "year": exercise.get("year"),
                "name": exercise.get("name"),
            },
            "filters": self._public_filters(filters),
            "items": items,
            "pagination": PaginationEnvelopeBuilder.paged_count(
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
        }

    def export_xlsx(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        year: int | None = None,
        unit_id: str | None = None,
        area_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        plan_status: str | None = None,
        required_date_from: str | None = None,
        required_date_to: str | None = None,
    ) -> dict[str, Any]:
        exercise, filters, rows = self._prepare(
            actor,
            exercise_id=exercise_id,
            year=year,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            priority=priority,
            origin=origin,
            plan_status=plan_status,
            required_date_from=required_date_from,
            required_date_to=required_date_to,
            for_export=True,
        )
        summary = build_summary(rows)
        details = [build_detail_item(r) for r in rows]
        by_cc = build_grouping(rows, group_by=GROUP_BY_COST_CENTER)["items"]
        by_cat = build_grouping(rows, group_by=GROUP_BY_CATEGORY)["items"]
        by_month = build_grouping(rows, group_by=GROUP_BY_MONTH)["items"]
        generated_at = datetime.now(timezone.utc)
        stream = build_capex_consolidation_workbook(
            exercise=exercise,
            filters=self._public_filters(filters),
            summary=summary,
            details=details,
            by_cost_center=by_cc,
            by_category=by_cat,
            by_month=by_month,
            generated_at=generated_at,
            generated_by=actor.user_name or actor.user_id,
        )
        exercise_year = exercise.get("year") or date.today().year
        filename = (
            f"planejamento-capex-{exercise_year}-"
            f"{generated_at.date().isoformat()}.xlsx"
        )
        self._repo.append_audit(
            exercise_id=str(exercise["id"]),
            entity_type=ENTITY_TYPE_CAPEX_CONSOLIDATION,
            entity_id=str(exercise["id"]),
            action=AUDIT_CONSOLIDATION_EXPORT,
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state={
                "filters": self._public_filters(filters),
                "exported_count": len(details),
                "filename": filename,
                "generated_at": generated_at.isoformat(timespec="seconds"),
            },
        )
        return {
            "filename": filename,
            "content_type": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            "stream": stream,
            "exported_count": len(details),
            "exercise_year": exercise_year,
        }


# Re-export group constants for router convenience
GROUP_ENDPOINTS = {
    "by-unit": GROUP_BY_UNIT,
    "by-area": GROUP_BY_AREA,
    "by-cost-center": GROUP_BY_COST_CENTER,
    "by-category": GROUP_BY_CATEGORY,
    "by-priority": GROUP_BY_PRIORITY,
    "by-origin": GROUP_BY_ORIGIN,
    "by-month": GROUP_BY_MONTH,
    "by-plan-status": GROUP_BY_PLAN_STATUS,
}
