"""Use cases de mídias e anexos — Guias e Procedimentos."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.application.services.guias_procedimentos.guide_media_storage import (
    GuiasMediaStorageError,
    GuiasProcedimentosMediaStorage,
    validate_external_video_url,
)
from app.application.use_cases.guias_procedimentos.admin_guias_use_cases import (
    ActorContext,
)
from app.domain.services.guias_procedimentos.exceptions import (
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.domain.services.guias_procedimentos.guide_validators import (
    validate_order_index,
)


class GuiasMediaRepository(Protocol):
    def get_procedure_access_row(self, procedure_id: str) -> dict[str, Any] | None: ...

    def get_admin_procedure_by_id(self, procedure_id: str) -> dict[str, Any] | None: ...

    def list_media_by_procedure_id(
        self,
        procedure_id: str,
        *,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]: ...

    def get_media_by_id(self, media_id: str) -> dict[str, Any] | None: ...

    def create_media(self, **fields: Any) -> dict[str, Any]: ...

    def update_media_metadata(self, media_id: str, **fields: Any) -> dict[str, Any]: ...

    def archive_media(self, media_id: str, **fields: Any) -> dict[str, Any]: ...

    def list_attachments_by_procedure_id(
        self,
        procedure_id: str,
        *,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]: ...

    def get_attachment_by_id(self, attachment_id: str) -> dict[str, Any] | None: ...

    def create_attachment(self, **fields: Any) -> dict[str, Any]: ...

    def update_attachment_metadata(
        self, attachment_id: str, **fields: Any
    ) -> dict[str, Any]: ...

    def archive_attachment(self, attachment_id: str, **fields: Any) -> dict[str, Any]: ...


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _str_id(value: Any) -> str:
    return str(value)


def media_payload(row: dict[str, Any]) -> dict[str, Any]:
    media_id = _str_id(row["id"])
    kind = row["media_kind"]
    payload: dict[str, Any] = {
        "id": media_id,
        "procedure_id": _str_id(row["procedure_id"]),
        "media_kind": kind,
        "title": row.get("title") or "",
        "alt_text": row.get("alt_text") or "",
        "original_filename": row.get("original_filename"),
        "stored_name": row.get("stored_name"),
        "mime_type": row.get("mime_type"),
        "size_bytes": row.get("size_bytes"),
        "storage_subdir": row.get("storage_subdir"),
        "external_url": row.get("external_url"),
        "external_provider": row.get("external_provider"),
        "order_index": int(row.get("order_index") or 0),
        "archived_at": _iso(row.get("archived_at")),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "created_by_user_id": row.get("created_by_user_id"),
        "created_by_name": row.get("created_by_name"),
        "updated_by_user_id": row.get("updated_by_user_id"),
        "updated_by_name": row.get("updated_by_name"),
    }
    if kind in {"image", "video_file"}:
        payload["file_path"] = f"/guias-procedimentos/media/{media_id}/file"
    return payload


def attachment_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _str_id(row["id"]),
        "procedure_id": _str_id(row["procedure_id"]),
        "title": row.get("title") or "",
        "original_filename": row.get("original_filename"),
        "stored_name": row.get("stored_name"),
        "mime_type": row.get("mime_type"),
        "size_bytes": row.get("size_bytes"),
        "order_index": int(row.get("order_index") or 0),
        "archived_at": _iso(row.get("archived_at")),
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "created_by_user_id": row.get("created_by_user_id"),
        "created_by_name": row.get("created_by_name"),
        "updated_by_user_id": row.get("updated_by_user_id"),
        "updated_by_name": row.get("updated_by_name"),
        "download_path": f"/guias-procedimentos/attachments/{row['id']}/file",
    }


def assert_can_read_asset(
    row: dict[str, Any],
    *,
    can_manage: bool,
) -> None:
    """Leitura: published+dept ativo para .access; draft/arquivo também para .manage."""
    if row.get("archived_at") is not None and not can_manage:
        raise GuiasNotFoundError("Recurso não encontrado.")
    status = str(row.get("procedure_status") or "")
    dept_active = bool(row.get("department_active"))
    if can_manage:
        return
    if status == "published" and dept_active:
        return
    raise GuiasNotFoundError("Recurso não encontrado.")


class ListAdminProcedureMediaUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(self, procedure_id: str) -> list[dict[str, Any]]:
        if self._repo.get_admin_procedure_by_id(procedure_id) is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        rows = self._repo.list_media_by_procedure_id(
            procedure_id, include_archived=False
        )
        return [media_payload(row) for row in rows]


class ListAdminProcedureAttachmentsUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(self, procedure_id: str) -> list[dict[str, Any]]:
        if self._repo.get_admin_procedure_by_id(procedure_id) is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        rows = self._repo.list_attachments_by_procedure_id(
            procedure_id, include_archived=False
        )
        return [attachment_payload(row) for row in rows]


class ListReadableProcedureMediaUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        procedure_id: str,
        *,
        can_manage: bool,
    ) -> list[dict[str, Any]]:
        access = self._repo.get_procedure_access_row(procedure_id)
        if access is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if not can_manage:
            if access.get("status") != "published" or not access.get("department_active"):
                raise GuiasNotFoundError("Procedimento não encontrado.")
        rows = self._repo.list_media_by_procedure_id(
            procedure_id, include_archived=False
        )
        return [media_payload(row) for row in rows]


class ListReadableProcedureAttachmentsUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        procedure_id: str,
        *,
        can_manage: bool,
    ) -> list[dict[str, Any]]:
        access = self._repo.get_procedure_access_row(procedure_id)
        if access is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if not can_manage:
            if access.get("status") != "published" or not access.get("department_active"):
                raise GuiasNotFoundError("Procedimento não encontrado.")
        rows = self._repo.list_attachments_by_procedure_id(
            procedure_id, include_archived=False
        )
        return [attachment_payload(row) for row in rows]


class UploadProcedureImageUseCase:
    def __init__(
        self,
        repo: GuiasMediaRepository,
        storage: GuiasProcedimentosMediaStorage | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage or GuiasProcedimentosMediaStorage()

    def execute(
        self,
        procedure_id: str,
        *,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        title: str = "",
        alt_text: str = "",
        order_index: int = 0,
        actor: ActorContext,
    ) -> dict[str, Any]:
        if self._repo.get_admin_procedure_by_id(procedure_id) is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        order_index = validate_order_index(order_index)
        try:
            saved = self._storage.save(
                procedure_id=procedure_id,
                kind="image",
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except GuiasMediaStorageError as exc:
            raise GuiasValidationError(str(exc)) from exc

        row = self._repo.create_media(
            procedure_id=procedure_id,
            media_kind="image",
            title=(title or "").strip()[:300],
            alt_text=(alt_text or "").strip()[:500],
            original_filename=(original_name or "")[:500],
            stored_name=saved["stored_name"],
            mime_type=saved["mime_type"],
            size_bytes=saved["size_bytes"],
            storage_subdir=saved["storage_subdir"],
            order_index=order_index,
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return media_payload(row)


class UploadProcedureVideoUseCase:
    def __init__(
        self,
        repo: GuiasMediaRepository,
        storage: GuiasProcedimentosMediaStorage | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage or GuiasProcedimentosMediaStorage()

    def execute(
        self,
        procedure_id: str,
        *,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        title: str = "",
        order_index: int = 0,
        actor: ActorContext,
    ) -> dict[str, Any]:
        if self._repo.get_admin_procedure_by_id(procedure_id) is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        order_index = validate_order_index(order_index)
        try:
            saved = self._storage.save(
                procedure_id=procedure_id,
                kind="video_file",
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except GuiasMediaStorageError as exc:
            raise GuiasValidationError(str(exc)) from exc

        row = self._repo.create_media(
            procedure_id=procedure_id,
            media_kind="video_file",
            title=(title or "").strip()[:300],
            alt_text="",
            original_filename=(original_name or "")[:500],
            stored_name=saved["stored_name"],
            mime_type=saved["mime_type"],
            size_bytes=saved["size_bytes"],
            storage_subdir=saved["storage_subdir"],
            order_index=order_index,
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return media_payload(row)


class CreateExternalVideoUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        procedure_id: str,
        *,
        url: str,
        title: str = "",
        order_index: int = 0,
        actor: ActorContext,
    ) -> dict[str, Any]:
        if self._repo.get_admin_procedure_by_id(procedure_id) is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        order_index = validate_order_index(order_index)
        try:
            normalized_url, provider = validate_external_video_url(url)
        except GuiasMediaStorageError as exc:
            raise GuiasValidationError(str(exc)) from exc

        row = self._repo.create_media(
            procedure_id=procedure_id,
            media_kind="video_external",
            title=(title or "").strip()[:300],
            alt_text="",
            external_url=normalized_url,
            external_provider=provider,
            order_index=order_index,
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return media_payload(row)


class UploadProcedureAttachmentUseCase:
    def __init__(
        self,
        repo: GuiasMediaRepository,
        storage: GuiasProcedimentosMediaStorage | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage or GuiasProcedimentosMediaStorage()

    def execute(
        self,
        procedure_id: str,
        *,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        title: str = "",
        order_index: int = 0,
        actor: ActorContext,
    ) -> dict[str, Any]:
        if self._repo.get_admin_procedure_by_id(procedure_id) is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        order_index = validate_order_index(order_index)
        try:
            saved = self._storage.save(
                procedure_id=procedure_id,
                kind="attachment",
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except GuiasMediaStorageError as exc:
            raise GuiasValidationError(str(exc)) from exc

        row = self._repo.create_attachment(
            procedure_id=procedure_id,
            title=(title or "").strip()[:300],
            original_filename=(original_name or "")[:500],
            stored_name=saved["stored_name"],
            mime_type=saved["mime_type"],
            size_bytes=saved["size_bytes"],
            order_index=order_index,
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return attachment_payload(row)


class UpdateMediaMetadataUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        media_id: str,
        *,
        title: str,
        alt_text: str,
        order_index: int,
        actor: ActorContext,
    ) -> dict[str, Any]:
        order_index = validate_order_index(order_index)
        row = self._repo.update_media_metadata(
            media_id,
            title=(title or "").strip()[:300],
            alt_text=(alt_text or "").strip()[:500],
            order_index=order_index,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return media_payload(row)


class ArchiveMediaUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(self, media_id: str, *, actor: ActorContext) -> dict[str, Any]:
        row = self._repo.archive_media(
            media_id,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return media_payload(row)


class UpdateAttachmentMetadataUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(
        self,
        attachment_id: str,
        *,
        title: str,
        order_index: int,
        actor: ActorContext,
    ) -> dict[str, Any]:
        order_index = validate_order_index(order_index)
        row = self._repo.update_attachment_metadata(
            attachment_id,
            title=(title or "").strip()[:300],
            order_index=order_index,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return attachment_payload(row)


class ArchiveAttachmentUseCase:
    def __init__(self, repo: GuiasMediaRepository) -> None:
        self._repo = repo

    def execute(self, attachment_id: str, *, actor: ActorContext) -> dict[str, Any]:
        row = self._repo.archive_attachment(
            attachment_id,
            updated_by_user_id=actor.user_id,
            updated_by_name=actor.user_name,
        )
        return attachment_payload(row)


class ResolveMediaFileUseCase:
    def __init__(
        self,
        repo: GuiasMediaRepository,
        storage: GuiasProcedimentosMediaStorage | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage or GuiasProcedimentosMediaStorage()

    def execute(
        self,
        media_id: str,
        *,
        can_manage: bool,
    ) -> dict[str, Any]:
        row = self._repo.get_media_by_id(media_id)
        if row is None:
            raise GuiasNotFoundError("Mídia não encontrada.")
        assert_can_read_asset(row, can_manage=can_manage)
        if row.get("media_kind") == "video_external":
            raise GuiasValidationError("Vídeo externo não possui arquivo para download.")
        if not row.get("stored_name") or not row.get("storage_subdir"):
            raise GuiasNotFoundError("Arquivo não encontrado.")
        path = self._storage.resolve_file(
            procedure_id=str(row["procedure_id"]),
            storage_subdir=str(row["storage_subdir"]),
            stored_name=str(row["stored_name"]),
        )
        return {
            "path": path,
            "mime_type": row.get("mime_type") or "application/octet-stream",
            "filename": row.get("original_filename") or row.get("stored_name"),
            "media_kind": row.get("media_kind"),
        }


class ResolveAttachmentFileUseCase:
    def __init__(
        self,
        repo: GuiasMediaRepository,
        storage: GuiasProcedimentosMediaStorage | None = None,
    ) -> None:
        self._repo = repo
        self._storage = storage or GuiasProcedimentosMediaStorage()

    def execute(
        self,
        attachment_id: str,
        *,
        can_manage: bool,
    ) -> dict[str, Any]:
        row = self._repo.get_attachment_by_id(attachment_id)
        if row is None:
            raise GuiasNotFoundError("Anexo não encontrado.")
        assert_can_read_asset(row, can_manage=can_manage)
        path = self._storage.resolve_file(
            procedure_id=str(row["procedure_id"]),
            storage_subdir="attachments",
            stored_name=str(row["stored_name"]),
        )
        return {
            "path": path,
            "mime_type": row.get("mime_type") or "application/octet-stream",
            "filename": row.get("original_filename") or row.get("stored_name"),
        }
