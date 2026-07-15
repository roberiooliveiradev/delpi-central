"""Use cases administrativos — Guias e Procedimentos."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.application.services.guias_procedimentos.guide_html_sanitizer import (
    GuideHtmlSanitizer,
)
from app.domain.services.guias_procedimentos.exceptions import (
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.domain.services.guias_procedimentos.guide_validators import (
    DEPARTMENT_DESCRIPTION_MAX,
    DEPARTMENT_NAME_MAX,
    DEPARTMENT_SLUG_MAX,
    PROCEDURE_SLUG_MAX,
    PROCEDURE_SUMMARY_MAX,
    PROCEDURE_TITLE_MAX,
    normalize_optional_text,
    require_non_empty_text,
    validate_content_html_length,
    validate_icon,
    validate_order_index,
    validate_reading_time_minutes,
    validate_slug,
)


class GuiasProcedimentosAdminRepository(Protocol):
    def list_admin_departments(self) -> list[dict[str, Any]]: ...

    def get_department_by_id(self, department_id: str) -> dict[str, Any] | None: ...

    def create_department(self, **fields: Any) -> dict[str, Any]: ...

    def update_department(self, department_id: str, **fields: Any) -> dict[str, Any]: ...

    def list_admin_procedures(
        self,
        *,
        department_id: str | None = None,
        status: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]: ...

    def get_admin_procedure_by_id(self, procedure_id: str) -> dict[str, Any] | None: ...

    def create_procedure(self, **fields: Any) -> dict[str, Any]: ...

    def update_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]: ...

    def publish_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]: ...

    def unpublish_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]: ...

    def archive_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]: ...

    def restore_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]: ...


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _str_id(value: Any) -> str:
    return str(value)


def admin_department_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _str_id(row["id"]),
        "name": row["name"],
        "slug": row["slug"],
        "description": row.get("description") or "",
        "icon": row["icon"],
        "active": bool(row.get("active")),
        "order_index": int(row.get("order_index") or 0),
        "procedure_count": int(row.get("procedure_count") or 0),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "created_by_user_id": row.get("created_by_user_id"),
        "created_by_name": row.get("created_by_name"),
        "updated_by_user_id": row.get("updated_by_user_id"),
        "updated_by_name": row.get("updated_by_name"),
    }


def _department_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _str_id(row["department_id"]),
        "name": row["department_name"],
        "slug": row["department_slug"],
        "icon": row["department_icon"],
        "active": bool(row.get("department_active", True)),
    }


def admin_procedure_list_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _str_id(row["id"]),
        "title": row["title"],
        "slug": row["slug"],
        "summary": row.get("summary") or "",
        "status": row["status"],
        "reading_time_minutes": row.get("reading_time_minutes"),
        "order_index": int(row.get("order_index") or 0),
        "published_at": _iso(row.get("published_at")),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "created_by_user_id": row.get("created_by_user_id"),
        "created_by_name": row.get("created_by_name"),
        "updated_by_user_id": row.get("updated_by_user_id"),
        "updated_by_name": row.get("updated_by_name"),
        "published_by_user_id": row.get("published_by_user_id"),
        "published_by_name": row.get("published_by_name"),
        "archived_at": _iso(row.get("archived_at")),
        "archived_by_user_id": row.get("archived_by_user_id"),
        "archived_by_name": row.get("archived_by_name"),
        "department": _department_summary(row),
    }


def admin_procedure_detail(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **admin_procedure_list_item(row),
        "content_html": GuideHtmlSanitizer.sanitize(row.get("content_html") or ""),
    }


class ActorContext:
    def __init__(self, user_id: str | None, user_name: str | None) -> None:
        self.user_id = user_id
        self.user_name = user_name


# --- departments ---


class ListAdminDepartmentsUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self) -> list[dict[str, Any]]:
        return [
            admin_department_payload(row)
            for row in self._repository.list_admin_departments()
        ]


class GetAdminDepartmentUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, department_id: str) -> dict[str, Any]:
        row = self._repository.get_department_by_id(department_id)
        if row is None:
            raise GuiasNotFoundError("Departamento não encontrado.")
        return admin_department_payload(row)


class CreateDepartmentUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, payload: dict[str, Any], actor: ActorContext) -> dict[str, Any]:
        row = self._repository.create_department(
            name=require_non_empty_text(
                payload.get("name"), field="name", max_length=DEPARTMENT_NAME_MAX
            ),
            slug=validate_slug(
                payload.get("slug"), field="slug", max_length=DEPARTMENT_SLUG_MAX
            ),
            description=normalize_optional_text(
                payload.get("description"), field="description"
            )[:DEPARTMENT_DESCRIPTION_MAX],
            icon=validate_icon(payload.get("icon")),
            active=bool(payload.get("active", True)),
            order_index=validate_order_index(payload.get("order_index"), default=0),
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_department_payload(row)


class UpdateDepartmentUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(
        self,
        department_id: str,
        payload: dict[str, Any],
        actor: ActorContext,
    ) -> dict[str, Any]:
        existing = self._repository.get_department_by_id(department_id)
        if existing is None:
            raise GuiasNotFoundError("Departamento não encontrado.")
        row = self._repository.update_department(
            department_id,
            name=require_non_empty_text(
                payload.get("name"), field="name", max_length=DEPARTMENT_NAME_MAX
            ),
            slug=validate_slug(
                payload.get("slug"), field="slug", max_length=DEPARTMENT_SLUG_MAX
            ),
            description=normalize_optional_text(
                payload.get("description"), field="description"
            )[:DEPARTMENT_DESCRIPTION_MAX],
            icon=validate_icon(payload.get("icon"), default=existing["icon"]),
            active=bool(payload.get("active", existing.get("active", True))),
            order_index=validate_order_index(
                payload.get("order_index"),
                default=int(existing.get("order_index") or 0),
            ),
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_department_payload(row)


# --- procedures ---


class ListAdminProceduresUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        department_id: str | None = None,
        status: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        if status is not None and status not in {"draft", "published", "archived"}:
            raise GuiasValidationError("status inválido.")
        query = (q or "").strip() or None
        rows = self._repository.list_admin_procedures(
            department_id=department_id or None,
            status=status,
            q=query,
        )
        return [admin_procedure_list_item(row) for row in rows]


class GetAdminProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, procedure_id: str) -> dict[str, Any]:
        row = self._repository.get_admin_procedure_by_id(procedure_id)
        if row is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        return admin_procedure_detail(row)


class CreateProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, payload: dict[str, Any], actor: ActorContext) -> dict[str, Any]:
        department_id = str(payload.get("department_id") or "").strip()
        if not department_id:
            raise GuiasValidationError("department_id é obrigatório.")
        department = self._repository.get_department_by_id(department_id)
        if department is None:
            raise GuiasValidationError("department_id inexistente.")

        if payload.get("status") is not None and payload.get("status") != "draft":
            raise GuiasValidationError(
                "Novos procedimentos devem ser criados como draft. Use /publish para publicar."
            )

        html = GuideHtmlSanitizer.sanitize(
            normalize_optional_text(payload.get("content_html"), field="content_html")
        )
        html = validate_content_html_length(html)

        row = self._repository.create_procedure(
            department_id=department_id,
            title=require_non_empty_text(
                payload.get("title"), field="title", max_length=PROCEDURE_TITLE_MAX
            ),
            slug=validate_slug(
                payload.get("slug"), field="slug", max_length=PROCEDURE_SLUG_MAX
            ),
            summary=normalize_optional_text(
                payload.get("summary"), field="summary"
            )[:PROCEDURE_SUMMARY_MAX],
            content_html=html,
            reading_time_minutes=validate_reading_time_minutes(
                payload.get("reading_time_minutes")
            ),
            order_index=validate_order_index(payload.get("order_index"), default=0),
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_procedure_detail(row)


class UpdateProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(
        self,
        procedure_id: str,
        payload: dict[str, Any],
        actor: ActorContext,
    ) -> dict[str, Any]:
        existing = self._repository.get_admin_procedure_by_id(procedure_id)
        if existing is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")

        department_id = str(
            payload.get("department_id") or existing["department_id"]
        ).strip()
        department = self._repository.get_department_by_id(department_id)
        if department is None:
            raise GuiasValidationError("department_id inexistente.")

        if "status" in payload:
            raise GuiasValidationError(
                "Status não pode ser alterado por este endpoint. "
                "Use /publish, /unpublish, /archive ou /restore."
            )

        html = GuideHtmlSanitizer.sanitize(
            normalize_optional_text(
                payload.get("content_html", existing.get("content_html")),
                field="content_html",
            )
        )
        html = validate_content_html_length(html)

        row = self._repository.update_procedure(
            procedure_id,
            department_id=department_id,
            title=require_non_empty_text(
                payload.get("title", existing["title"]),
                field="title",
                max_length=PROCEDURE_TITLE_MAX,
            ),
            slug=validate_slug(
                payload.get("slug", existing["slug"]),
                field="slug",
                max_length=PROCEDURE_SLUG_MAX,
            ),
            summary=normalize_optional_text(
                payload.get("summary", existing.get("summary")),
                field="summary",
            )[:PROCEDURE_SUMMARY_MAX],
            content_html=html,
            reading_time_minutes=validate_reading_time_minutes(
                payload.get(
                    "reading_time_minutes",
                    existing.get("reading_time_minutes"),
                )
            ),
            order_index=validate_order_index(
                payload.get("order_index"),
                default=int(existing.get("order_index") or 0),
            ),
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_procedure_detail(row)


class PublishProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, procedure_id: str, actor: ActorContext) -> dict[str, Any]:
        existing = self._repository.get_admin_procedure_by_id(procedure_id)
        if existing is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if not existing.get("department_active"):
            raise GuiasValidationError(
                "Não é possível publicar: o departamento está inativo."
            )
        title = (existing.get("title") or "").strip()
        summary = (existing.get("summary") or "").strip()
        if not title or not summary:
            raise GuiasValidationError(
                "Não é possível publicar: título e resumo são obrigatórios."
            )
        html = GuideHtmlSanitizer.sanitize(existing.get("content_html") or "")
        if not html.strip():
            raise GuiasValidationError(
                "Não é possível publicar: content_html está vazio após sanitização."
            )
        # Idempotente se já published
        if existing.get("status") == "published":
            return admin_procedure_detail(existing)

        row = self._repository.publish_procedure(
            procedure_id,
            content_html=html,
            published_by_user_id=actor.user_id,
            published_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_procedure_detail(row)


class UnpublishProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, procedure_id: str, actor: ActorContext) -> dict[str, Any]:
        existing = self._repository.get_admin_procedure_by_id(procedure_id)
        if existing is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if existing.get("status") == "draft":
            return admin_procedure_detail(existing)
        if existing.get("status") == "archived":
            raise GuiasValidationError(
                "Procedimento arquivado. Use /restore antes de despublicar."
            )
        row = self._repository.unpublish_procedure(
            procedure_id,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_procedure_detail(row)


class ArchiveProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, procedure_id: str, actor: ActorContext) -> dict[str, Any]:
        existing = self._repository.get_admin_procedure_by_id(procedure_id)
        if existing is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if existing.get("status") == "archived":
            return admin_procedure_detail(existing)
        row = self._repository.archive_procedure(
            procedure_id,
            archived_by_user_id=actor.user_id,
            archived_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_procedure_detail(row)


class RestoreProcedureUseCase:
    def __init__(self, repository: GuiasProcedimentosAdminRepository) -> None:
        self._repository = repository

    def execute(self, procedure_id: str, actor: ActorContext) -> dict[str, Any]:
        existing = self._repository.get_admin_procedure_by_id(procedure_id)
        if existing is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if existing.get("status") != "archived":
            raise GuiasValidationError(
                "Somente procedimentos arquivados podem ser restaurados."
            )
        row = self._repository.restore_procedure(
            procedure_id,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return admin_procedure_detail(row)
