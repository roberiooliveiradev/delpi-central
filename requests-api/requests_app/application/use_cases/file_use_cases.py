from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from requests_app.application.errors import ApplicationError
from requests_app.application.security.requests_permissions import actor_for
from requests_app.application.services.attachment_storage import (
    ArtifactStorage,
    AttachmentStorage,
    StorageError,
)
from requests_app.core.serialize import json_safe
from requests_app.domain.entities.files import (
    RequestArtifact,
    RequestAttachment,
    RequestEvent,
)
from requests_app.domain.ports import RequestRepositoryPort, RequestTypeRepositoryPort
from requests_app.domain.ports.file_repository_port import FileRepositoryPort
from requests_app.domain.services.workflow_engine import WorkflowEngine


def _can_view_request(*, request, actor) -> bool:
    is_owner = request.created_by_user_id == actor.user_id
    return bool(is_owner or actor.has_view_all or actor.has_process or actor.has_manage)


def _is_terminal(request, workflow: dict[str, Any]) -> bool:
    terminals = set((workflow or {}).get("terminalStatuses") or [])
    return request.status in terminals


class FileUseCases:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        files: FileRepositoryPort,
        attachment_storage: AttachmentStorage | None = None,
        artifact_storage: ArtifactStorage | None = None,
        engine: WorkflowEngine | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._files = files
        self._attachments = attachment_storage or AttachmentStorage()
        self._artifacts = artifact_storage or ArtifactStorage()
        self._engine = engine or WorkflowEngine()

    def _load_request_context(self, *, user, request_id: str):
        request = self._requests.get(request_id)
        if request is None:
            raise ApplicationError(code="not_found", status_code=404)
        request_type = self._types.get_by_code(request.type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        if not _can_view_request(request=request, actor=actor):
            raise ApplicationError(code="forbidden", status_code=403)
        return request, request_type, actor

    def upload_attachment(
        self,
        *,
        user,
        request_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
    ) -> dict[str, Any]:
        request, request_type, actor = self._load_request_context(
            user=user, request_id=request_id
        )
        workflow = request_type.workflow_definition or {}
        is_owner = request.created_by_user_id == actor.user_id
        if _is_terminal(request, workflow):
            raise ApplicationError(code="upload_forbidden", status_code=403)
        if not (is_owner or actor.has_process or actor.has_manage):
            raise ApplicationError(code="upload_forbidden", status_code=403)
        try:
            stored = self._attachments.save(
                request_id=str(request.id),
                original_name=original_name,
                content=content,
                mime_type=mime_type,
            )
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=422, detail=str(exc)
            ) from exc

        attachment = self._files.create_attachment(
            RequestAttachment(
                id=uuid4(),
                request_id=request.id,
                original_name=stored.original_name,
                stored_name=stored.stored_name,
                storage_key=stored.storage_key,
                mime_type=stored.mime_type,
                size_bytes=stored.size_bytes,
                checksum_sha256=stored.checksum_sha256,
                created_by_user_id=actor.user_id,
                created_by_name=actor.user_name,
            )
        )
        self._files.append_event(
            RequestEvent(
                id=uuid4(),
                request_id=request.id,
                event_type="attachment_added",
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                payload={"attachment_id": str(attachment.id), "name": attachment.original_name},
            )
        )
        return json_safe(
            {
                "id": attachment.id,
                "request_id": attachment.request_id,
                "original_name": attachment.original_name,
                "mime_type": attachment.mime_type,
                "size_bytes": attachment.size_bytes,
                "checksum_sha256": attachment.checksum_sha256,
                "created_at": attachment.created_at,
            }
        )

    def list_attachments(self, *, user, request_id: str) -> dict[str, Any]:
        self._load_request_context(user=user, request_id=request_id)
        items = [
            json_safe(
                {
                    "id": item.id,
                    "request_id": item.request_id,
                    "original_name": item.original_name,
                    "mime_type": item.mime_type,
                    "size_bytes": item.size_bytes,
                    "created_by_name": item.created_by_name,
                    "created_at": item.created_at,
                }
            )
            for item in self._files.list_attachments(request_id)
        ]
        return {"items": items}

    def resolve_attachment_path(self, *, user, attachment_id: str) -> tuple[Path, RequestAttachment]:
        attachment = self._files.get_attachment(attachment_id)
        if attachment is None:
            raise ApplicationError(code="attachment_not_found", status_code=404)
        self._load_request_context(user=user, request_id=str(attachment.request_id))
        try:
            path = self._attachments.resolve_file(storage_key=attachment.storage_key)
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=404, detail=str(exc)
            ) from exc
        self._files.append_event(
            RequestEvent(
                id=uuid4(),
                request_id=attachment.request_id,
                event_type="attachment_downloaded",
                actor_user_id=str(getattr(user, "id", "") or ""),
                actor_name=str(getattr(user, "name", "") or ""),
                payload={"attachment_id": str(attachment.id)},
            )
        )
        return path, attachment

    def upload_artifact(
        self,
        *,
        user,
        request_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        artifact_kind: str = "generic",
    ) -> dict[str, Any]:
        request, request_type, actor = self._load_request_context(
            user=user, request_id=request_id
        )
        if not (actor.has_process or actor.has_manage):
            raise ApplicationError(code="upload_forbidden", status_code=403)
        try:
            stored = self._artifacts.save(
                request_id=str(request.id),
                original_name=original_name,
                content=content,
                mime_type=mime_type,
                artifact_kind=artifact_kind,
            )
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=422, detail=str(exc)
            ) from exc
        artifact = self._files.create_artifact(
            RequestArtifact(
                id=uuid4(),
                request_id=request.id,
                artifact_kind=artifact_kind or "generic",
                original_name=stored.original_name,
                stored_name=stored.stored_name,
                storage_key=stored.storage_key,
                mime_type=stored.mime_type,
                size_bytes=stored.size_bytes,
                checksum_sha256=stored.checksum_sha256,
                produced_by_user_id=actor.user_id,
                produced_by_name=actor.user_name,
            )
        )
        self._files.append_event(
            RequestEvent(
                id=uuid4(),
                request_id=request.id,
                event_type="artifact_added",
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                payload={
                    "artifact_id": str(artifact.id),
                    "kind": artifact.artifact_kind,
                    "name": artifact.original_name,
                },
            )
        )
        return json_safe(
            {
                "id": artifact.id,
                "request_id": artifact.request_id,
                "artifact_kind": artifact.artifact_kind,
                "original_name": artifact.original_name,
                "mime_type": artifact.mime_type,
                "size_bytes": artifact.size_bytes,
                "created_at": artifact.created_at,
            }
        )

    def list_artifacts(self, *, user, request_id: str) -> dict[str, Any]:
        self._load_request_context(user=user, request_id=request_id)
        items = [
            json_safe(
                {
                    "id": item.id,
                    "request_id": item.request_id,
                    "artifact_kind": item.artifact_kind,
                    "original_name": item.original_name,
                    "mime_type": item.mime_type,
                    "size_bytes": item.size_bytes,
                    "produced_by_name": item.produced_by_name,
                    "created_at": item.created_at,
                }
            )
            for item in self._files.list_artifacts(request_id)
        ]
        return {"items": items}

    def resolve_artifact_path(self, *, user, artifact_id: str) -> tuple[Path, RequestArtifact]:
        artifact = self._files.get_artifact(artifact_id)
        if artifact is None:
            raise ApplicationError(code="artifact_not_found", status_code=404)
        self._load_request_context(user=user, request_id=str(artifact.request_id))
        try:
            path = self._artifacts.resolve_file(storage_key=artifact.storage_key)
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=404, detail=str(exc)
            ) from exc
        self._files.append_event(
            RequestEvent(
                id=uuid4(),
                request_id=artifact.request_id,
                event_type="artifact_downloaded",
                actor_user_id=str(getattr(user, "id", "") or ""),
                actor_name=str(getattr(user, "name", "") or ""),
                payload={"artifact_id": str(artifact.id)},
            )
        )
        return path, artifact
