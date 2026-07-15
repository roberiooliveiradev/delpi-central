"""Serialização e regras de leitura pública — Guias e Procedimentos."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.application.services.guias_procedimentos.guide_html_sanitizer import (
    GuideHtmlSanitizer,
)


class GuiasProcedimentosPublicRepository(Protocol):
    def list_active_departments_with_published_counts(self) -> list[dict[str, Any]]: ...

    def get_active_department_by_slug(self, slug: str) -> dict[str, Any] | None: ...

    def list_published_procedures_by_department_id(
        self,
        department_id: Any,
    ) -> list[dict[str, Any]]: ...

    def get_published_procedure_by_slug(self, slug: str) -> dict[str, Any] | None: ...


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _str_id(value: Any) -> str:
    return str(value)


def department_list_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _str_id(row["id"]),
        "name": row["name"],
        "slug": row["slug"],
        "description": row.get("description") or "",
        "icon": row["icon"],
        "order_index": int(row.get("order_index") or 0),
        "procedure_count": int(row.get("procedure_count") or 0),
    }


def procedure_summary_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _str_id(row["id"]),
        "title": row["title"],
        "slug": row["slug"],
        "summary": row.get("summary") or "",
        "reading_time_minutes": row.get("reading_time_minutes"),
        "order_index": int(row.get("order_index") or 0),
    }


def procedure_detail_payload(row: dict[str, Any]) -> dict[str, Any]:
    content_html = GuideHtmlSanitizer.sanitize(row.get("content_html") or "")
    return {
        "id": _str_id(row["id"]),
        "title": row["title"],
        "slug": row["slug"],
        "summary": row.get("summary") or "",
        "content_html": content_html,
        "reading_time_minutes": row.get("reading_time_minutes"),
        "order_index": int(row.get("order_index") or 0),
        "published_at": _iso(row.get("published_at")),
        "updated_at": _iso(row.get("updated_at")),
        "department": {
            "id": _str_id(row["department_id"]),
            "name": row["department_name"],
            "slug": row["department_slug"],
            "icon": row["department_icon"],
        },
    }


class ListGuiasDepartmentsUseCase:
    def __init__(self, repository: GuiasProcedimentosPublicRepository) -> None:
        self._repository = repository

    def execute(self) -> list[dict[str, Any]]:
        rows = self._repository.list_active_departments_with_published_counts()
        return [department_list_item(row) for row in rows]


class GetGuiasDepartmentBySlugUseCase:
    def __init__(self, repository: GuiasProcedimentosPublicRepository) -> None:
        self._repository = repository

    def execute(self, slug: str) -> dict[str, Any] | None:
        normalized = (slug or "").strip()
        if not normalized:
            return None
        department = self._repository.get_active_department_by_slug(normalized)
        if department is None:
            return None
        procedures = self._repository.list_published_procedures_by_department_id(
            department["id"]
        )
        return {
            **department_list_item(
                {
                    **department,
                    "procedure_count": len(procedures),
                }
            ),
            "procedures": [procedure_summary_item(row) for row in procedures],
        }


class GetGuiasProcedureBySlugUseCase:
    def __init__(self, repository: GuiasProcedimentosPublicRepository) -> None:
        self._repository = repository

    def execute(self, slug: str) -> dict[str, Any] | None:
        normalized = (slug or "").strip()
        if not normalized:
            return None
        row = self._repository.get_published_procedure_by_slug(normalized)
        if row is None:
            return None
        return procedure_detail_payload(row)
