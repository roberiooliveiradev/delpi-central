"""Casos de uso — itens de investimento CAPEX (Fase 2B.1)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.acknowledgement_guard import (
    BudgetGuidanceAcknowledgementGuard,
)
from app.domain.services.planejamento_orcamentario.capex_investment_constants import (
    ALLOWED_CLASSIFICATIONS,
    ALLOWED_ORIGINS,
    ALLOWED_PRIORITIES,
    ALLOWED_SHIFTS,
    ALLOWED_STATUSES,
    COMPLETENESS_FIELDS,
    DEFAULT_CURRENCY,
    ENTITY_TYPE_CAPEX_INVESTMENT,
    STATUS_ARCHIVED,
    STATUS_DRAFT,
)
from app.domain.services.planejamento_orcamentario.capex_plan_guard import (
    assert_plan_allows_mutation,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetCostCenterAmbiguousError,
    BudgetCostCenterInvalidError,
    BudgetCostCenterNotFoundError,
    BudgetGuidanceAcknowledgementRequiredError,
    BudgetResponsibilityForbiddenError,
    BudgetUserNotAuthorizedError,
    CapexInvestmentArchivedError,
    CapexInvestmentCategoryInvalidError,
    CapexInvestmentCostCenterForbiddenError,
    CapexInvestmentDateInvalidError,
    CapexInvestmentInvalidError,
    CapexInvestmentNotFoundError,
    CapexInvestmentStatusInvalidError,
    CapexInvestmentValueInvalidError,
    CapexInvestmentVersionConflictError,
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


def _require_access(actor: BudgetActor) -> None:
    allowed = {
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.admin",
        "planejamento-orcamentario.guidance.view",
        "planejamento-orcamentario.guidance.manage",
        "planejamento-orcamentario.scopes.manage",
    }
    if not (actor.permissions & allowed):
        raise BudgetUserNotAuthorizedError(
            "Sem permissão de acesso ao planejamento orçamentário."
        )


def _is_admin(actor: BudgetActor) -> bool:
    return "planejamento-orcamentario.admin" in actor.permissions


def _parse_date(value: Any, field: str) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise CapexInvestmentDateInvalidError(
            f"Data inválida em {field}."
        ) from exc


def _parse_amount(value: Any, *, allow_empty: bool = True) -> Decimal | None:
    if value is None or value == "":
        if allow_empty:
            return None
        raise CapexInvestmentValueInvalidError("Valor estimado é obrigatório.")
    try:
        amount = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError) as exc:
        raise CapexInvestmentValueInvalidError("Valor estimado inválido.") from exc
    if amount <= 0:
        raise CapexInvestmentValueInvalidError(
            "Valor estimado deve ser maior que zero."
        )
    return amount.quantize(Decimal("0.01"))


def _normalize_enum(
    value: Any,
    *,
    allowed: frozenset[str],
    field: str,
    error_cls: type[Exception] = CapexInvestmentInvalidError,
) -> str | None:
    if value is None or value == "":
        return None
    norm = str(value).strip().lower()
    # prioridade/classificação/turno são dígitos — preservar forma canônica
    if field in {"priority", "classification", "shift"}:
        norm = str(value).strip()
    if norm not in allowed:
        raise error_cls(f"Valor inválido em {field}.")
    return norm


def _compute_completeness(row: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for field in COMPLETENESS_FIELDS:
        value = row.get(field)
        if field == "estimated_amount":
            if value is None or value == "":
                missing.append(field)
                continue
            try:
                if Decimal(str(value)) <= 0:
                    missing.append(field)
            except (InvalidOperation, ValueError):
                missing.append(field)
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return {"is_complete": len(missing) == 0, "missing_fields": missing}


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "exercise_id",
        "unit_id",
        "area_id",
        "cost_center_id",
        "category_id",
        "accounting_account_code",
        "description",
        "justification",
        "probable_supplier_name",
        "probable_supplier_code",
        "estimated_amount",
        "currency",
        "required_date",
        "priority",
        "origin",
        "classification",
        "shift",
        "application",
        "observations",
        "status",
        "version",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "archived_by",
        "archived_at",
    )
    out = {k: row.get(k) for k in keys}
    amount = out.get("estimated_amount")
    if amount is not None and not isinstance(amount, str):
        out["estimated_amount"] = str(amount)
    completeness = _compute_completeness(row)
    out["is_complete"] = completeness["is_complete"]
    out["missing_fields"] = completeness["missing_fields"]
    return out


class CapexInvestmentUseCases:
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

    def _resolve_org_from_cc(
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
            raise CapexInvestmentInvalidError(str(exc)) from exc
        except (BudgetCostCenterNotFoundError, BudgetCostCenterInvalidError) as exc:
            raise CapexInvestmentCostCenterForbiddenError(str(exc)) from exc
        unit = str(cc.get("unit_code") or cc.get("branch") or "").strip()
        if not unit:
            raise CapexInvestmentInvalidError(
                "Centro de custo sem unidade associada no catálogo."
            )
        area_id = cc.get("area_code")
        if area_id:
            area_id = str(area_id)
        return {"unit_id": unit, "area_id": area_id, "cost_center": cc}

    def _validate_category(self, category_id: str | None) -> dict[str, Any] | None:
        if not category_id:
            return None
        cat = self._repo.get_capex_category(str(category_id).strip())
        if not cat:
            raise CapexInvestmentCategoryInvalidError(
                "Categoria CAPEX inexistente."
            )
        if not cat.get("is_active"):
            raise CapexInvestmentCategoryInvalidError(
                "Categoria CAPEX inativa não pode ser usada em novos investimentos."
            )
        return cat

    def _authorized_cost_centers(
        self, actor: BudgetActor, *, exercise_id: str | None
    ) -> list[tuple[str, str]] | None:
        """None = admin (sem restrição de CC). Caso contrário, pares (filial, código)."""
        if _is_admin(actor):
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

    def _assert_can_view(self, actor: BudgetActor, row: dict[str, Any]) -> None:
        if _is_admin(actor):
            return
        try:
            self._assert_responsibility(
                actor,
                exercise_id=str(row["exercise_id"]),
                cost_center_id=str(row["cost_center_id"]),
                unit_id=str(row.get("unit_id") or "") or None,
            )
        except CapexInvestmentCostCenterForbiddenError:
            # IDOR: não revelar existência
            raise CapexInvestmentNotFoundError(
                "Investimento CAPEX não encontrado."
            ) from None

    def create_investment(self, actor: BudgetActor, body: dict[str, Any]) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)

        exercise_id = str(body.get("exercise_id") or "").strip()
        cost_center_id = str(body.get("cost_center_id") or "").strip()
        unit_id_raw = str(body.get("unit_id") or "").strip() or None
        if not exercise_id or not cost_center_id:
            raise CapexInvestmentInvalidError(
                "Exercício e centro de custo são obrigatórios."
            )

        ctx = self._assert_responsibility(
            actor,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=unit_id_raw,
        )
        org = self._resolve_org_from_cc(cost_center_id, unit_id=unit_id_raw)
        assert_plan_allows_mutation(
            self._repo,
            exercise_id=exercise_id,
            cost_center_id=cost_center_id,
            unit_id=org["unit_id"],
        )
        # Preferir unidade/área do catálogo; se cliente enviar, validar consistência
        if body.get("unit_id") and str(body["unit_id"]).strip() != org["unit_id"]:
            raise CapexInvestmentInvalidError(
                "Unidade incompatível com o centro de custo selecionado."
            )
        if body.get("area_id") and org["area_id"] and str(body["area_id"]).strip() != org["area_id"]:
            raise CapexInvestmentInvalidError(
                "Área incompatível com o centro de custo selecionado."
            )

        category_id = (str(body["category_id"]).strip() if body.get("category_id") else None)
        self._validate_category(category_id)

        amount = _parse_amount(body.get("estimated_amount"), allow_empty=True)
        required_date = _parse_date(body.get("required_date"), "required_date")
        priority = _normalize_enum(
            body.get("priority"), allowed=ALLOWED_PRIORITIES, field="priority"
        )
        origin = _normalize_enum(
            body.get("origin"), allowed=ALLOWED_ORIGINS, field="origin"
        )
        if origin:
            origin = origin  # already national|imported
        classification = _normalize_enum(
            body.get("classification"),
            allowed=ALLOWED_CLASSIFICATIONS,
            field="classification",
        )
        shift = _normalize_enum(
            body.get("shift"), allowed=ALLOWED_SHIFTS, field="shift"
        )

        description = (str(body["description"]).strip() if body.get("description") else None) or None
        payload = {
            "exercise_id": exercise_id,
            "unit_id": org["unit_id"],
            "area_id": org["area_id"]
            or (str(body["area_id"]).strip() if body.get("area_id") else None),
            "cost_center_id": cost_center_id,
            "category_id": category_id,
            "accounting_account_code": (
                str(body["accounting_account_code"]).strip()
                if body.get("accounting_account_code")
                else None
            )
            or None,
            "description": description,
            "justification": (
                str(body["justification"]).strip() if body.get("justification") else None
            )
            or None,
            "probable_supplier_name": (
                str(body["probable_supplier_name"]).strip()
                if body.get("probable_supplier_name")
                else None
            )
            or None,
            "probable_supplier_code": (
                str(body["probable_supplier_code"]).strip()
                if body.get("probable_supplier_code")
                else None
            )
            or None,
            "estimated_amount": amount,
            "currency": (str(body.get("currency") or DEFAULT_CURRENCY).strip().upper() or DEFAULT_CURRENCY),
            "required_date": required_date,
            "priority": priority,
            "origin": origin,
            "classification": classification,
            "shift": shift,
            "application": (
                str(body["application"]).strip() if body.get("application") else None
            )
            or None,
            "observations": (
                str(body["observations"]).strip() if body.get("observations") else None
            )
            or None,
            "status": STATUS_DRAFT,
            "created_by": actor.user_id,
            "updated_by": actor.user_id,
        }
        if len(payload["currency"]) != 3:
            raise CapexInvestmentInvalidError("Moeda inválida (use código ISO de 3 letras).")

        created = self._repo.create_capex_investment(payload)
        public = _public_row(created)
        self._repo.append_audit(
            exercise_id=exercise_id,
            entity_type=ENTITY_TYPE_CAPEX_INVESTMENT,
            entity_id=created["id"],
            action="capex_investment.created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=public,
        )
        # contexto do guard usado (auditoria leve do exercício)
        _ = ctx
        return public

    def get_investment(self, actor: BudgetActor, investment_id: str) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        row = self._repo.get_capex_investment(investment_id)
        if not row:
            raise CapexInvestmentNotFoundError("Investimento CAPEX não encontrado.")
        self._assert_can_view(actor, row)
        return _public_row(row)

    def list_investments(
        self,
        actor: BudgetActor,
        *,
        exercise_id: str | None = None,
        cost_center_id: str | None = None,
        category_id: str | None = None,
        priority: str | None = None,
        origin: str | None = None,
        status: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)

        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 50)))
        offset = (page - 1) * page_size

        if status and status not in ALLOWED_STATUSES:
            raise CapexInvestmentStatusInvalidError("Status de filtro inválido.")
        priority_norm = _normalize_enum(
            priority, allowed=ALLOWED_PRIORITIES, field="priority"
        ) if priority else None
        origin_norm = _normalize_enum(
            origin, allowed=ALLOWED_ORIGINS, field="origin"
        ) if origin else None

        # Escopo: sem exercício explícito, usa ativo se possível
        exercise_filter = (exercise_id or "").strip() or None
        if not exercise_filter:
            active = self._repo.get_active_exercise()
            exercise_filter = str(active["id"]) if active else None

        allowed_pairs = self._authorized_cost_centers(actor, exercise_id=exercise_filter)
        if allowed_pairs is not None and len(allowed_pairs) == 0:
            return {
                "items": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": 0,
                    "has_more": False,
                },
            }

        if cost_center_id and not self._pair_authorized(
            allowed_pairs, cost_center_id=cost_center_id
        ):
            raise CapexInvestmentCostCenterForbiddenError(
                "Sem responsabilidade orçamentária para o centro de custo filtrado."
            )

        items, total = self._repo.list_capex_investments(
            exercise_id=exercise_filter,
            cost_center_id=cost_center_id or None,
            category_id=category_id or None,
            priority=priority_norm,
            origin=origin_norm,
            status=status or None,
            q=(q or "").strip() or None,
            cost_center_ids=None,
            unit_cost_center_pairs=allowed_pairs,
            offset=offset,
            limit=page_size,
        )
        return {
            "items": [_public_row(i) for i in items],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "has_more": offset + len(items) < total,
            },
        }

    def update_investment(
        self, actor: BudgetActor, investment_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)

        current = self._repo.get_capex_investment(investment_id)
        if not current:
            raise CapexInvestmentNotFoundError("Investimento CAPEX não encontrado.")
        if str(current.get("status")) == STATUS_ARCHIVED:
            raise CapexInvestmentArchivedError(
                "Investimento arquivado não pode ser editado."
            )

        # Responsabilidade no CC atual
        self._assert_responsibility(
            actor,
            exercise_id=str(current["exercise_id"]),
            cost_center_id=str(current["cost_center_id"]),
            unit_id=str(current.get("unit_id") or "") or None,
        )
        assert_plan_allows_mutation(
            self._repo,
            exercise_id=str(current["exercise_id"]),
            cost_center_id=str(current["cost_center_id"]),
            unit_id=str(current.get("unit_id") or "") or None,
        )

        if "version" not in body or body["version"] is None:
            raise CapexInvestmentVersionConflictError(
                "Versão atual (version) é obrigatória para atualização."
            )
        try:
            expected_version = int(body["version"])
        except (TypeError, ValueError) as exc:
            raise CapexInvestmentVersionConflictError(
                "Versão inválida para atualização."
            ) from exc

        fields: dict[str, Any] = {"updated_by": actor.user_id}
        actions: list[str] = []

        # Troca de centro de custo
        if "cost_center_id" in body and body["cost_center_id"] is not None:
            new_cc = str(body["cost_center_id"]).strip()
            new_unit = (
                str(body["unit_id"]).strip()
                if body.get("unit_id")
                else str(current.get("unit_id") or "").strip() or None
            )
            if new_cc != str(current["cost_center_id"]) or (
                new_unit and new_unit != str(current.get("unit_id") or "")
            ):
                self._assert_responsibility(
                    actor,
                    exercise_id=str(current["exercise_id"]),
                    cost_center_id=new_cc,
                    unit_id=new_unit,
                )
                org = self._resolve_org_from_cc(new_cc, unit_id=new_unit)
                assert_plan_allows_mutation(
                    self._repo,
                    exercise_id=str(current["exercise_id"]),
                    cost_center_id=new_cc,
                    unit_id=org["unit_id"],
                )
                fields["cost_center_id"] = new_cc
                fields["unit_id"] = org["unit_id"]
                fields["area_id"] = org["area_id"]
                actions.append("capex_investment.cost_center_changed")

        if "category_id" in body:
            cat_raw = body["category_id"]
            category_id = str(cat_raw).strip() if cat_raw else None
            if category_id != current.get("category_id"):
                self._validate_category(category_id)
                fields["category_id"] = category_id
                actions.append("capex_investment.category_changed")

        if "description" in body:
            fields["description"] = (
                str(body["description"]).strip() if body["description"] else None
            ) or None
        if "justification" in body:
            fields["justification"] = (
                str(body["justification"]).strip() if body["justification"] else None
            ) or None
        if "probable_supplier_name" in body:
            fields["probable_supplier_name"] = (
                str(body["probable_supplier_name"]).strip()
                if body["probable_supplier_name"]
                else None
            ) or None
        if "probable_supplier_code" in body:
            fields["probable_supplier_code"] = (
                str(body["probable_supplier_code"]).strip()
                if body["probable_supplier_code"]
                else None
            ) or None
        if "observations" in body:
            fields["observations"] = (
                str(body["observations"]).strip() if body["observations"] else None
            ) or None
        if "application" in body:
            fields["application"] = (
                str(body["application"]).strip() if body["application"] else None
            ) or None
        if "accounting_account_code" in body:
            fields["accounting_account_code"] = (
                str(body["accounting_account_code"]).strip()
                if body["accounting_account_code"]
                else None
            ) or None

        if "estimated_amount" in body:
            amount = _parse_amount(body.get("estimated_amount"), allow_empty=True)
            fields["estimated_amount"] = amount
            prev = current.get("estimated_amount")
            prev_dec = Decimal(str(prev)) if prev is not None else None
            if prev_dec != amount:
                actions.append("capex_investment.amount_changed")

        if "required_date" in body:
            required_date = _parse_date(body.get("required_date"), "required_date")
            fields["required_date"] = required_date
            prev_d = current.get("required_date")
            prev_s = str(prev_d)[:10] if prev_d else None
            new_s = required_date.isoformat() if required_date else None
            if prev_s != new_s:
                actions.append("capex_investment.date_changed")

        if "priority" in body:
            fields["priority"] = _normalize_enum(
                body.get("priority"), allowed=ALLOWED_PRIORITIES, field="priority"
            )
        if "origin" in body:
            fields["origin"] = _normalize_enum(
                body.get("origin"), allowed=ALLOWED_ORIGINS, field="origin"
            )
        if "classification" in body:
            fields["classification"] = _normalize_enum(
                body.get("classification"),
                allowed=ALLOWED_CLASSIFICATIONS,
                field="classification",
            )
        if "shift" in body:
            fields["shift"] = _normalize_enum(
                body.get("shift"), allowed=ALLOWED_SHIFTS, field="shift"
            )
        if "currency" in body and body["currency"]:
            currency = str(body["currency"]).strip().upper()
            if len(currency) != 3:
                raise CapexInvestmentInvalidError("Moeda inválida.")
            fields["currency"] = currency

        try:
            updated = self._repo.update_capex_investment(
                investment_id,
                fields,
                expected_version=expected_version,
            )
        except PluginsRepositoryError as exc:
            msg = str(exc)
            if "version" in msg.lower() or "conflito" in msg.lower():
                self._repo.append_audit(
                    exercise_id=str(current["exercise_id"]),
                    entity_type=ENTITY_TYPE_CAPEX_INVESTMENT,
                    entity_id=investment_id,
                    action="capex_investment.version_conflict",
                    actor_user_id=actor.user_id,
                    actor_name=actor.user_name,
                    before_state=_public_row(current),
                    after_state={"attempted_version": expected_version},
                )
                raise CapexInvestmentVersionConflictError(
                    "Versão desatualizada. Recarregue o investimento e tente novamente."
                ) from exc
            raise CapexInvestmentInvalidError(msg) from exc

        public = _public_row(updated)
        before = _public_row(current)
        for action in actions or ["capex_investment.updated"]:
            self._repo.append_audit(
                exercise_id=str(updated["exercise_id"]),
                entity_type=ENTITY_TYPE_CAPEX_INVESTMENT,
                entity_id=investment_id,
                action=action,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=before,
                after_state=public,
            )
        return public

    def archive_investment(
        self, actor: BudgetActor, investment_id: str, reason: str | None = None
    ) -> dict[str, Any]:
        _require_access(actor)
        self._assert_unlocked(actor)
        current = self._repo.get_capex_investment(investment_id)
        if not current:
            raise CapexInvestmentNotFoundError("Investimento CAPEX não encontrado.")
        if str(current.get("status")) == STATUS_ARCHIVED:
            raise CapexInvestmentArchivedError("Investimento já está arquivado.")
        self._assert_responsibility(
            actor,
            exercise_id=str(current["exercise_id"]),
            cost_center_id=str(current["cost_center_id"]),
            unit_id=str(current.get("unit_id") or "") or None,
        )
        assert_plan_allows_mutation(
            self._repo,
            exercise_id=str(current["exercise_id"]),
            cost_center_id=str(current["cost_center_id"]),
            unit_id=str(current.get("unit_id") or "") or None,
        )
        updated = self._repo.archive_capex_investment(
            investment_id, actor_id=actor.user_id, reason=reason
        )
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=str(current["exercise_id"]),
            entity_type=ENTITY_TYPE_CAPEX_INVESTMENT,
            entity_id=investment_id,
            action="capex_investment.archived",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public


# re-export for tests that may patch acknowledgement
__all__ = [
    "CapexInvestmentUseCases",
    "BudgetGuidanceAcknowledgementRequiredError",
]
