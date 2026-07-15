"""Repositório — Guias e Procedimentos (público + admin)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.errors import ForeignKeyViolation, UniqueViolation

from app.domain.services.guias_procedimentos.exceptions import (
    GuiasConflictError,
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)


def _as_uuid(value: str, *, field: str = "id") -> UUID:
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise GuiasValidationError(f"{field} inválido.") from exc


class PostgresGuiasProcedimentosRepository(PluginBaseRepository):
    """Persistência do schema guias_procedimentos."""

    # ---- público ----

    def list_active_departments_with_published_counts(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                d.id,
                d.name,
                d.slug,
                d.description,
                d.icon,
                d.order_index,
                COUNT(p.id)::int AS procedure_count
            FROM guias_procedimentos.departments d
            LEFT JOIN guias_procedimentos.procedures p
                ON p.department_id = d.id
               AND p.status = 'published'
            WHERE d.active = TRUE
            GROUP BY d.id, d.name, d.slug, d.description, d.icon, d.order_index
            ORDER BY d.order_index ASC, d.name ASC
            """
        )

    def get_active_department_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT id, name, slug, description, icon, order_index
            FROM guias_procedimentos.departments
            WHERE slug = %s AND active = TRUE
            """,
            (slug,),
        )

    def list_published_procedures_by_department_id(
        self,
        department_id: Any,
    ) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT id, title, slug, summary, reading_time_minutes, order_index
            FROM guias_procedimentos.procedures
            WHERE department_id = %s AND status = 'published'
            ORDER BY order_index ASC, title ASC
            """,
            (department_id,),
        )

    def get_published_procedure_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT
                p.id, p.title, p.slug, p.summary, p.content_html,
                p.reading_time_minutes, p.order_index, p.published_at, p.updated_at,
                d.id AS department_id, d.name AS department_name,
                d.slug AS department_slug, d.icon AS department_icon
            FROM guias_procedimentos.procedures p
            INNER JOIN guias_procedimentos.departments d ON d.id = p.department_id
            WHERE p.slug = %s AND p.status = 'published' AND d.active = TRUE
            """,
            (slug,),
        )

    # ---- admin departments ----

    def list_admin_departments(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                d.id, d.name, d.slug, d.description, d.icon, d.active,
                d.order_index, d.created_at, d.updated_at,
                d.created_by_user_id, d.created_by_name,
                d.updated_by_user_id, d.updated_by_name,
                COUNT(p.id)::int AS procedure_count
            FROM guias_procedimentos.departments d
            LEFT JOIN guias_procedimentos.procedures p ON p.department_id = d.id
            GROUP BY
                d.id, d.name, d.slug, d.description, d.icon, d.active,
                d.order_index, d.created_at, d.updated_at,
                d.created_by_user_id, d.created_by_name,
                d.updated_by_user_id, d.updated_by_name
            ORDER BY d.order_index ASC, d.name ASC
            """
        )

    def get_department_by_id(self, department_id: str) -> dict[str, Any] | None:
        uid = _as_uuid(department_id, field="department_id")
        return self.fetch_one(
            """
            SELECT
                d.id, d.name, d.slug, d.description, d.icon, d.active,
                d.order_index, d.created_at, d.updated_at,
                d.created_by_user_id, d.created_by_name,
                d.updated_by_user_id, d.updated_by_name,
                (
                    SELECT COUNT(*)::int
                    FROM guias_procedimentos.procedures p
                    WHERE p.department_id = d.id
                ) AS procedure_count
            FROM guias_procedimentos.departments d
            WHERE d.id = %s
            """,
            (uid,),
        )

    def create_department(self, **fields: Any) -> dict[str, Any]:
        try:
            row = self.execute_returning_one(
                """
                INSERT INTO guias_procedimentos.departments (
                    name, slug, description, icon, active, order_index,
                    created_by_user_id, created_by_name,
                    updated_by_user_id, updated_by_name
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING
                    id, name, slug, description, icon, active, order_index,
                    created_at, updated_at,
                    created_by_user_id, created_by_name,
                    updated_by_user_id, updated_by_name
                """,
                (
                    fields["name"],
                    fields["slug"],
                    fields["description"],
                    fields["icon"],
                    fields["active"],
                    fields["order_index"],
                    fields.get("created_by_user_id"),
                    fields.get("created_by_name"),
                    fields.get("updated_by_user_id"),
                    fields.get("updated_by_name"),
                ),
            )
        except PluginsRepositoryError as exc:
            self._reraise_unique(exc, resource="departamento")
            raise
        if row is None:
            raise PluginsRepositoryError("Falha ao criar departamento.")
        row["procedure_count"] = 0
        return row

    def update_department(self, department_id: str, **fields: Any) -> dict[str, Any]:
        uid = _as_uuid(department_id, field="department_id")
        try:
            row = self.execute_returning_one(
                """
                UPDATE guias_procedimentos.departments
                SET
                    name = %s,
                    slug = %s,
                    description = %s,
                    icon = %s,
                    active = %s,
                    order_index = %s,
                    updated_at = NOW(),
                    updated_by_user_id = %s,
                    updated_by_name = %s
                WHERE id = %s
                RETURNING
                    id, name, slug, description, icon, active, order_index,
                    created_at, updated_at,
                    created_by_user_id, created_by_name,
                    updated_by_user_id, updated_by_name
                """,
                (
                    fields["name"],
                    fields["slug"],
                    fields["description"],
                    fields["icon"],
                    fields["active"],
                    fields["order_index"],
                    fields.get("updated_by_user_id"),
                    fields.get("updated_by_name"),
                    uid,
                ),
            )
        except PluginsRepositoryError as exc:
            self._reraise_unique(exc, resource="departamento")
            raise
        if row is None:
            raise GuiasNotFoundError("Departamento não encontrado.")
        counted = self.get_department_by_id(str(row["id"]))
        if counted is not None:
            row["procedure_count"] = counted.get("procedure_count", 0)
        else:
            row["procedure_count"] = 0
        return row

    # ---- admin procedures ----

    def list_admin_procedures(
        self,
        *,
        department_id: str | None = None,
        status: str | None = None,
        q: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = ["1=1"]
        params: list[Any] = []
        if department_id:
            clauses.append("p.department_id = %s")
            params.append(_as_uuid(department_id, field="department_id"))
        if status:
            clauses.append("p.status = %s")
            params.append(status)
        if q:
            clauses.append(
                "(p.title ILIKE %s OR p.slug ILIKE %s OR p.summary ILIKE %s)"
            )
            like = f"%{q}%"
            params.extend([like, like, like])
        where = " AND ".join(clauses)
        return self.fetch_all(
            f"""
            SELECT
                p.id, p.title, p.slug, p.summary, p.status,
                p.reading_time_minutes, p.order_index,
                p.published_at, p.updated_at, p.created_at,
                p.created_by_user_id, p.created_by_name,
                p.updated_by_user_id, p.updated_by_name,
                p.published_by_user_id, p.published_by_name,
                p.archived_at, p.archived_by_user_id, p.archived_by_name,
                d.id AS department_id, d.name AS department_name,
                d.slug AS department_slug, d.icon AS department_icon,
                d.active AS department_active
            FROM guias_procedimentos.procedures p
            INNER JOIN guias_procedimentos.departments d ON d.id = p.department_id
            WHERE {where}
            ORDER BY p.order_index ASC, p.title ASC
            """,
            tuple(params),
        )

    def get_admin_procedure_by_id(self, procedure_id: str) -> dict[str, Any] | None:
        uid = _as_uuid(procedure_id, field="procedure_id")
        return self.fetch_one(
            """
            SELECT
                p.id, p.department_id, p.title, p.slug, p.summary, p.content_html,
                p.status, p.reading_time_minutes, p.order_index,
                p.published_at, p.created_at, p.updated_at,
                p.created_by_user_id, p.created_by_name,
                p.updated_by_user_id, p.updated_by_name,
                p.published_by_user_id, p.published_by_name,
                p.archived_at, p.archived_by_user_id, p.archived_by_name,
                d.id AS department_id, d.name AS department_name,
                d.slug AS department_slug, d.icon AS department_icon,
                d.active AS department_active
            FROM guias_procedimentos.procedures p
            INNER JOIN guias_procedimentos.departments d ON d.id = p.department_id
            WHERE p.id = %s
            """,
            (uid,),
        )

    def create_procedure(self, **fields: Any) -> dict[str, Any]:
        try:
            row = self.execute_returning_one(
                """
                INSERT INTO guias_procedimentos.procedures (
                    department_id, title, slug, summary, content_html, status,
                    reading_time_minutes, order_index,
                    created_by_user_id, created_by_name,
                    updated_by_user_id, updated_by_name
                ) VALUES (
                    %s, %s, %s, %s, %s, 'draft', %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    _as_uuid(str(fields["department_id"]), field="department_id"),
                    fields["title"],
                    fields["slug"],
                    fields["summary"],
                    fields["content_html"],
                    fields.get("reading_time_minutes"),
                    fields["order_index"],
                    fields.get("created_by_user_id"),
                    fields.get("created_by_name"),
                    fields.get("updated_by_user_id"),
                    fields.get("updated_by_name"),
                ),
            )
        except PluginsRepositoryError as exc:
            self._reraise_fk_or_unique(exc)
            raise
        if row is None:
            raise PluginsRepositoryError("Falha ao criar procedimento.")
        detail = self.get_admin_procedure_by_id(str(row["id"]))
        if detail is None:
            raise PluginsRepositoryError("Procedimento criado não encontrado.")
        return detail

    def update_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        try:
            row = self.execute_returning_one(
                """
                UPDATE guias_procedimentos.procedures
                SET
                    department_id = %s,
                    title = %s,
                    slug = %s,
                    summary = %s,
                    content_html = %s,
                    reading_time_minutes = %s,
                    order_index = %s,
                    updated_at = NOW(),
                    updated_by_user_id = %s,
                    updated_by_name = %s
                WHERE id = %s
                RETURNING id
                """,
                (
                    _as_uuid(str(fields["department_id"]), field="department_id"),
                    fields["title"],
                    fields["slug"],
                    fields["summary"],
                    fields["content_html"],
                    fields.get("reading_time_minutes"),
                    fields["order_index"],
                    fields.get("updated_by_user_id"),
                    fields.get("updated_by_name"),
                    uid,
                ),
            )
        except PluginsRepositoryError as exc:
            self._reraise_fk_or_unique(exc)
            raise
        if row is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        detail = self.get_admin_procedure_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        return detail

    def publish_procedure(
        self,
        procedure_id: str,
        *,
        content_html: str,
        published_by_user_id: str | None,
        published_by_name: str | None,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedures
            SET
                status = 'published',
                content_html = %s,
                published_at = NOW(),
                published_by_user_id = %s,
                published_by_name = %s,
                archived_at = NULL,
                archived_by_user_id = NULL,
                archived_by_name = NULL,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s
            RETURNING id
            """,
            (
                content_html,
                published_by_user_id,
                published_by_name,
                updated_by_user_id,
                updated_by_name,
                uid,
            ),
        )
        if row is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        detail = self.get_admin_procedure_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        return detail

    def unpublish_procedure(
        self,
        procedure_id: str,
        *,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedures
            SET
                status = 'draft',
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s
            RETURNING id
            """,
            (updated_by_user_id, updated_by_name, uid),
        )
        if row is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        detail = self.get_admin_procedure_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        return detail

    def archive_procedure(
        self,
        procedure_id: str,
        *,
        archived_by_user_id: str | None,
        archived_by_name: str | None,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedures
            SET
                status = 'archived',
                archived_at = COALESCE(archived_at, NOW()),
                archived_by_user_id = COALESCE(%s, archived_by_user_id),
                archived_by_name = COALESCE(%s, archived_by_name),
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s
            RETURNING id
            """,
            (
                archived_by_user_id,
                archived_by_name,
                updated_by_user_id,
                updated_by_name,
                uid,
            ),
        )
        if row is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        detail = self.get_admin_procedure_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        return detail

    def restore_procedure(
        self,
        procedure_id: str,
        *,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedures
            SET
                status = 'draft',
                archived_at = NULL,
                archived_by_user_id = NULL,
                archived_by_name = NULL,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s
            RETURNING id
            """,
            (updated_by_user_id, updated_by_name, uid),
        )
        if row is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        detail = self.get_admin_procedure_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        return detail

    def _reraise_unique(
        self,
        exc: PluginsRepositoryError,
        *,
        resource: str,
    ) -> None:
        cause = exc.__cause__
        if isinstance(cause, UniqueViolation):
            raise GuiasConflictError(f"Já existe um {resource} com este slug.") from exc

    def _reraise_fk_or_unique(self, exc: PluginsRepositoryError) -> None:
        cause = exc.__cause__
        if isinstance(cause, UniqueViolation):
            raise GuiasConflictError("Já existe um procedimento com este slug.") from exc
        if isinstance(cause, ForeignKeyViolation):
            raise GuiasValidationError("department_id inexistente.") from exc

    # ---- media / attachments ----

    def get_procedure_access_row(self, procedure_id: str) -> dict[str, Any] | None:
        """Status do procedimento + departamento ativo (para gate de leitura)."""
        uid = _as_uuid(procedure_id, field="procedure_id")
        return self.fetch_one(
            """
            SELECT
                p.id,
                p.status,
                p.slug,
                d.active AS department_active
            FROM guias_procedimentos.procedures p
            INNER JOIN guias_procedimentos.departments d ON d.id = p.department_id
            WHERE p.id = %s
            """,
            (uid,),
        )

    def list_media_by_procedure_id(
        self,
        procedure_id: str,
        *,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        archived_clause = "" if include_archived else "AND archived_at IS NULL"
        return self.fetch_all(
            f"""
            SELECT
                id, procedure_id, media_kind, title, alt_text,
                original_filename, stored_name, mime_type, size_bytes,
                storage_subdir, external_url, external_provider,
                order_index, archived_at, created_at, updated_at,
                created_by_user_id, created_by_name,
                updated_by_user_id, updated_by_name
            FROM guias_procedimentos.procedure_media
            WHERE procedure_id = %s
            {archived_clause}
            ORDER BY order_index ASC, created_at ASC
            """,
            (uid,),
        )

    def get_media_by_id(self, media_id: str) -> dict[str, Any] | None:
        uid = _as_uuid(media_id, field="media_id")
        return self.fetch_one(
            """
            SELECT
                m.id, m.procedure_id, m.media_kind, m.title, m.alt_text,
                m.original_filename, m.stored_name, m.mime_type, m.size_bytes,
                m.storage_subdir, m.external_url, m.external_provider,
                m.order_index, m.archived_at, m.created_at, m.updated_at,
                m.created_by_user_id, m.created_by_name,
                m.updated_by_user_id, m.updated_by_name,
                p.status AS procedure_status,
                d.active AS department_active
            FROM guias_procedimentos.procedure_media m
            INNER JOIN guias_procedimentos.procedures p ON p.id = m.procedure_id
            INNER JOIN guias_procedimentos.departments d ON d.id = p.department_id
            WHERE m.id = %s
            """,
            (uid,),
        )

    def create_media(self, **fields: Any) -> dict[str, Any]:
        procedure_id = _as_uuid(str(fields["procedure_id"]), field="procedure_id")
        try:
            row = self.execute_returning_one(
                """
                INSERT INTO guias_procedimentos.procedure_media (
                    procedure_id, media_kind, title, alt_text,
                    original_filename, stored_name, mime_type, size_bytes,
                    storage_subdir, external_url, external_provider,
                    order_index,
                    created_by_user_id, created_by_name,
                    updated_by_user_id, updated_by_name
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s,
                    %s, %s,
                    %s, %s
                )
                RETURNING id
                """,
                (
                    procedure_id,
                    fields["media_kind"],
                    fields.get("title") or "",
                    fields.get("alt_text") or "",
                    fields.get("original_filename"),
                    fields.get("stored_name"),
                    fields.get("mime_type"),
                    fields.get("size_bytes"),
                    fields.get("storage_subdir"),
                    fields.get("external_url"),
                    fields.get("external_provider"),
                    int(fields.get("order_index") or 0),
                    fields.get("created_by_user_id"),
                    fields.get("created_by_name"),
                    fields.get("updated_by_user_id"),
                    fields.get("updated_by_name"),
                ),
            )
        except PluginsRepositoryError as exc:
            cause = exc.__cause__
            if isinstance(cause, ForeignKeyViolation):
                raise GuiasNotFoundError("Procedimento não encontrado.") from exc
            raise
        detail = self.get_media_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Mídia não encontrada.")
        return detail

    def update_media_metadata(
        self,
        media_id: str,
        *,
        title: str,
        alt_text: str,
        order_index: int,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(media_id, field="media_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedure_media
            SET
                title = %s,
                alt_text = %s,
                order_index = %s,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s AND archived_at IS NULL
            RETURNING id
            """,
            (title, alt_text, order_index, updated_by_user_id, updated_by_name, uid),
        )
        if row is None:
            raise GuiasNotFoundError("Mídia não encontrada.")
        detail = self.get_media_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Mídia não encontrada.")
        return detail

    def archive_media(
        self,
        media_id: str,
        *,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(media_id, field="media_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedure_media
            SET
                archived_at = COALESCE(archived_at, NOW()),
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s
            RETURNING id
            """,
            (updated_by_user_id, updated_by_name, uid),
        )
        if row is None:
            raise GuiasNotFoundError("Mídia não encontrada.")
        detail = self.get_media_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Mídia não encontrada.")
        return detail

    def list_attachments_by_procedure_id(
        self,
        procedure_id: str,
        *,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        uid = _as_uuid(procedure_id, field="procedure_id")
        archived_clause = "" if include_archived else "AND archived_at IS NULL"
        return self.fetch_all(
            f"""
            SELECT
                id, procedure_id, title, original_filename, stored_name,
                mime_type, size_bytes, order_index, archived_at,
                created_at, updated_at,
                created_by_user_id, created_by_name,
                updated_by_user_id, updated_by_name
            FROM guias_procedimentos.procedure_attachments
            WHERE procedure_id = %s
            {archived_clause}
            ORDER BY order_index ASC, created_at ASC
            """,
            (uid,),
        )

    def get_attachment_by_id(self, attachment_id: str) -> dict[str, Any] | None:
        uid = _as_uuid(attachment_id, field="attachment_id")
        return self.fetch_one(
            """
            SELECT
                a.id, a.procedure_id, a.title, a.original_filename, a.stored_name,
                a.mime_type, a.size_bytes, a.order_index, a.archived_at,
                a.created_at, a.updated_at,
                a.created_by_user_id, a.created_by_name,
                a.updated_by_user_id, a.updated_by_name,
                p.status AS procedure_status,
                d.active AS department_active
            FROM guias_procedimentos.procedure_attachments a
            INNER JOIN guias_procedimentos.procedures p ON p.id = a.procedure_id
            INNER JOIN guias_procedimentos.departments d ON d.id = p.department_id
            WHERE a.id = %s
            """,
            (uid,),
        )

    def create_attachment(self, **fields: Any) -> dict[str, Any]:
        procedure_id = _as_uuid(str(fields["procedure_id"]), field="procedure_id")
        try:
            row = self.execute_returning_one(
                """
                INSERT INTO guias_procedimentos.procedure_attachments (
                    procedure_id, title, original_filename, stored_name,
                    mime_type, size_bytes, order_index,
                    created_by_user_id, created_by_name,
                    updated_by_user_id, updated_by_name
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s
                )
                RETURNING id
                """,
                (
                    procedure_id,
                    fields.get("title") or "",
                    fields["original_filename"],
                    fields["stored_name"],
                    fields["mime_type"],
                    fields["size_bytes"],
                    int(fields.get("order_index") or 0),
                    fields.get("created_by_user_id"),
                    fields.get("created_by_name"),
                    fields.get("updated_by_user_id"),
                    fields.get("updated_by_name"),
                ),
            )
        except PluginsRepositoryError as exc:
            cause = exc.__cause__
            if isinstance(cause, ForeignKeyViolation):
                raise GuiasNotFoundError("Procedimento não encontrado.") from exc
            raise
        detail = self.get_attachment_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Anexo não encontrado.")
        return detail

    def update_attachment_metadata(
        self,
        attachment_id: str,
        *,
        title: str,
        order_index: int,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(attachment_id, field="attachment_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedure_attachments
            SET
                title = %s,
                order_index = %s,
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s AND archived_at IS NULL
            RETURNING id
            """,
            (title, order_index, updated_by_user_id, updated_by_name, uid),
        )
        if row is None:
            raise GuiasNotFoundError("Anexo não encontrado.")
        detail = self.get_attachment_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Anexo não encontrado.")
        return detail

    def archive_attachment(
        self,
        attachment_id: str,
        *,
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        uid = _as_uuid(attachment_id, field="attachment_id")
        row = self.execute_returning_one(
            """
            UPDATE guias_procedimentos.procedure_attachments
            SET
                archived_at = COALESCE(archived_at, NOW()),
                updated_at = NOW(),
                updated_by_user_id = %s,
                updated_by_name = %s
            WHERE id = %s
            RETURNING id
            """,
            (updated_by_user_id, updated_by_name, uid),
        )
        if row is None:
            raise GuiasNotFoundError("Anexo não encontrado.")
        detail = self.get_attachment_by_id(str(row["id"]))
        if detail is None:
            raise GuiasNotFoundError("Anexo não encontrado.")
        return detail
