"""Casos de uso — catálogo de categorias CAPEX (Fase 2A.3)."""

from __future__ import annotations

import re
from typing import Any

from app.application.services.planejamento_orcamentario.category_icon_storage import (
    CategoryIconStorage,
)
from app.application.use_cases.planejamento_orcamentario.budget_planning_use_cases import (
    BudgetActor,
)
from app.domain.services.planejamento_orcamentario.capex_category_constants import (
    ENTITY_TYPE_CAPEX_CATEGORY,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    BudgetDocumentNotFoundError,
    BudgetUserNotAuthorizedError,
    CapexCategoryConflictError,
    CapexCategoryInvalidError,
    CapexCategoryNotFoundError,
)
from app.domain.services.planejamento_orcamentario.org_cost_center_constants import (
    ALLOWED_COST_CENTER_ICON_KEYS,
    normalize_cost_center_icon_key,
)
from app.infrastructure.persistence.plugins.repositories.planejamento_orcamentario.postgres_budget_planning_repository import (
    PostgresBudgetPlanningRepository,
)

_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,79}$")


def _require_admin_or_scopes(actor: BudgetActor) -> None:
    if not (
        actor.permissions
        & {
            "planejamento-orcamentario.scopes.manage",
            "planejamento-orcamentario.admin",
        }
    ):
        raise BudgetUserNotAuthorizedError(
            "Sem permissão administrativa para gerenciar categorias CAPEX."
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
            "Sem permissão para consultar categorias CAPEX."
        )


def _public_row(row: dict[str, Any]) -> dict[str, Any]:
    icon_key = row.get("icon_key")
    icon_norm = str(icon_key).strip().lower() if icon_key else None
    if icon_norm and icon_norm not in ALLOWED_COST_CENTER_ICON_KEYS:
        icon_norm = None
    image_key = str(row.get("icon_image_key") or "").strip() or None
    keys = (
        "id",
        "code",
        "name",
        "description",
        "display_order",
        "is_active",
        "is_system_default",
        "created_by",
        "created_at",
        "updated_by",
        "updated_at",
        "deactivated_by",
        "deactivated_at",
    )
    out = {k: row.get(k) for k in keys}
    out["icon_key"] = icon_norm
    out["has_custom_icon"] = bool(image_key)
    out["icon_image_mime"] = row.get("icon_image_mime") if image_key else None
    return out


def _normalize_code(raw: Any) -> str:
    code = str(raw or "").strip().upper().replace(" ", "_").replace("-", "_")
    if not code:
        raise CapexCategoryInvalidError("Código da categoria é obrigatório.")
    if not _CODE_RE.match(code):
        raise CapexCategoryInvalidError(
            "Código inválido. Use letras maiúsculas, números e underscore (ex.: FERRAMENTAS)."
        )
    return code


def _normalize_icon_key(raw: Any) -> str | None:
    try:
        return normalize_cost_center_icon_key(raw)
    except ValueError as exc:
        raise CapexCategoryInvalidError(str(exc)) from exc


def _normalize_name(raw: Any) -> str:
    name = str(raw or "").strip()
    if not name:
        raise CapexCategoryInvalidError("Nome da categoria é obrigatório.")
    if len(name) > 200:
        raise CapexCategoryInvalidError("Nome da categoria deve ter no máximo 200 caracteres.")
    return name


class CapexCategoryUseCases:
    def __init__(
        self,
        repository: PostgresBudgetPlanningRepository | None = None,
        icon_storage: CategoryIconStorage | None = None,
    ) -> None:
        self._repo = repository or PostgresBudgetPlanningRepository()
        self._icons = icon_storage or CategoryIconStorage()

    def list_active_categories(self, actor: BudgetActor) -> dict[str, Any]:
        _require_access(actor)
        items = self._repo.list_capex_categories(is_active=True, q=None)
        return {"items": [_public_row(i) for i in items]}

    def list_admin_categories(
        self,
        actor: BudgetActor,
        *,
        is_active: bool | None = None,
        q: str | None = None,
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        items = self._repo.list_capex_categories(
            is_active=is_active,
            q=(q or "").strip() or None,
        )
        return {"items": [_public_row(i) for i in items]}

    def create_category(self, actor: BudgetActor, body: dict[str, Any]) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        code = _normalize_code(body.get("code"))
        name = _normalize_name(body.get("name"))
        description = body.get("description")
        if description is not None:
            description = str(description).strip() or None
        display_order = body.get("display_order")
        try:
            order = int(display_order) if display_order is not None else 0
        except (TypeError, ValueError) as exc:
            raise CapexCategoryInvalidError("Ordem de exibição inválida.") from exc

        icon_key = _normalize_icon_key(body.get("icon_key")) if "icon_key" in body else None

        if self._repo.get_capex_category_by_code(code):
            raise CapexCategoryConflictError(
                f"Já existe categoria com o código {code}."
            )

        created = self._repo.create_capex_category(
            {
                "code": code,
                "name": name,
                "description": description,
                "display_order": order,
                "icon_key": icon_key,
                "is_system_default": False,
                "created_by": actor.user_id,
                "updated_by": actor.user_id,
            }
        )
        public = _public_row(created)
        self._repo.append_audit(
            exercise_id=None,
            entity_type=ENTITY_TYPE_CAPEX_CATEGORY,
            entity_id=created["id"],
            action="capex_category.created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=None,
            after_state=public,
        )
        return public

    def update_category(
        self, actor: BudgetActor, category_id: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_capex_category(category_id)
        if not current:
            raise CapexCategoryNotFoundError("Categoria CAPEX não encontrada.")

        if "code" in body and body["code"] is not None:
            incoming = _normalize_code(body["code"])
            if incoming != current["code"]:
                raise CapexCategoryInvalidError(
                    "O código da categoria é imutável após a criação."
                )

        fields: dict[str, Any] = {"updated_by": actor.user_id}
        actions: list[str] = []

        if "name" in body and body["name"] is not None:
            fields["name"] = _normalize_name(body["name"])
            if fields["name"] != current.get("name"):
                actions.append("capex_category.updated")

        if "description" in body:
            desc = body["description"]
            fields["description"] = (
                None if desc is None else (str(desc).strip() or None)
            )
            if fields["description"] != current.get("description"):
                if "capex_category.updated" not in actions:
                    actions.append("capex_category.updated")

        if "display_order" in body and body["display_order"] is not None:
            try:
                fields["display_order"] = int(body["display_order"])
            except (TypeError, ValueError) as exc:
                raise CapexCategoryInvalidError("Ordem de exibição inválida.") from exc
            if fields["display_order"] != current.get("display_order"):
                actions.append("capex_category.order_changed")

        if "icon_key" in body:
            fields["icon_key"] = _normalize_icon_key(body.get("icon_key"))
            if fields["icon_key"] != (current.get("icon_key") or None):
                if "capex_category.updated" not in actions:
                    actions.append("capex_category.updated")

        if len(fields) == 1:
            return _public_row(current)

        updated = self._repo.update_capex_category(category_id, fields)
        public = _public_row(updated)
        before = _public_row(current)
        for action in actions or ["capex_category.updated"]:
            self._repo.append_audit(
                exercise_id=None,
                entity_type=ENTITY_TYPE_CAPEX_CATEGORY,
                entity_id=category_id,
                action=action,
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                before_state=before,
                after_state=public,
            )
        return public

    def deactivate_category(
        self, actor: BudgetActor, category_id: str, reason: str | None = None
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_capex_category(category_id)
        if not current:
            raise CapexCategoryNotFoundError("Categoria CAPEX não encontrada.")
        if not current.get("is_active"):
            raise CapexCategoryInvalidError("Categoria já está inativa.")
        updated = self._repo.deactivate_capex_category(
            category_id, actor_id=actor.user_id, reason=reason
        )
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=None,
            entity_type=ENTITY_TYPE_CAPEX_CATEGORY,
            entity_id=category_id,
            action="capex_category.deactivated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public

    def reactivate_category(self, actor: BudgetActor, category_id: str) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_capex_category(category_id)
        if not current:
            raise CapexCategoryNotFoundError("Categoria CAPEX não encontrada.")
        if current.get("is_active"):
            raise CapexCategoryInvalidError("Categoria já está ativa.")
        updated = self._repo.reactivate_capex_category(
            category_id, actor_id=actor.user_id
        )
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=None,
            entity_type=ENTITY_TYPE_CAPEX_CATEGORY,
            entity_id=category_id,
            action="capex_category.reactivated",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public

    def upload_icon_image(
        self,
        actor: BudgetActor,
        category_id: str,
        *,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_capex_category(category_id)
        if not current:
            raise CapexCategoryNotFoundError("Categoria CAPEX não encontrada.")
        storage_key, mime = self._icons.save(
            category_id=category_id,
            original_name=original_name,
            content=content,
            mime_type=mime_type,
        )
        previous_key = current.get("icon_image_key")
        updated = self._repo.update_capex_category(
            category_id,
            {
                "icon_image_key": storage_key,
                "icon_image_mime": mime,
                "updated_by": actor.user_id,
            },
        )
        if previous_key and previous_key != storage_key:
            self._icons.delete_file(category_id=category_id, storage_key=str(previous_key))
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=None,
            entity_type=ENTITY_TYPE_CAPEX_CATEGORY,
            entity_id=category_id,
            action="capex_category.icon_image_uploaded",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public

    def clear_icon_image(self, actor: BudgetActor, category_id: str) -> dict[str, Any]:
        _require_admin_or_scopes(actor)
        current = self._repo.get_capex_category(category_id)
        if not current:
            raise CapexCategoryNotFoundError("Categoria CAPEX não encontrada.")
        previous_key = current.get("icon_image_key")
        if not previous_key:
            return _public_row(current)
        updated = self._repo.update_capex_category(
            category_id,
            {
                "icon_image_key": None,
                "icon_image_mime": None,
                "updated_by": actor.user_id,
            },
        )
        self._icons.delete_file(category_id=category_id, storage_key=str(previous_key))
        public = _public_row(updated)
        self._repo.append_audit(
            exercise_id=None,
            entity_type=ENTITY_TYPE_CAPEX_CATEGORY,
            entity_id=category_id,
            action="capex_category.icon_image_cleared",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            before_state=_public_row(current),
            after_state=public,
        )
        return public

    def resolve_icon_image(self, actor: BudgetActor, category_id: str) -> dict[str, Any]:
        _require_access(actor)
        current = self._repo.get_capex_category(category_id)
        if not current:
            raise CapexCategoryNotFoundError("Categoria CAPEX não encontrada.")
        key = current.get("icon_image_key")
        if not key:
            raise BudgetDocumentNotFoundError("Categoria sem imagem de ícone.")
        path = self._icons.resolve_file(
            category_id=category_id, storage_key=str(key)
        )
        return {
            "path": path,
            "mime_type": current.get("icon_image_mime") or "application/octet-stream",
            "filename": str(key),
        }
