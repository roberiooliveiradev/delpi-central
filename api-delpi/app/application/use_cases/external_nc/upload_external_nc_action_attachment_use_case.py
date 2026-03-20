# app/application/use_cases/external_nc/upload_external_nc_action_attachment_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.upload_external_nc_action_attachment_request import (
    UploadExternalNcActionAttachmentRequest,
)
from app.domain.entities.shared_quality.nonconformity_attachment import (
    NonconformityAttachment,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)
from app.domain.ports.external_nc.external_nonconformity_action_repository import (
    ExternalNonconformityActionRepositoryPort,
)
from app.domain.ports.shared_quality.attachment_repository import (
    AttachmentRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)


class UploadExternalNcActionAttachmentUseCase:
    def __init__(
        self,
        action_repository: ExternalNonconformityActionRepositoryPort,
        attachment_repository: AttachmentRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._action_repository = action_repository
        self._attachment_repository = attachment_repository
        self._audit_event_repository = audit_event_repository

    def execute(
        self,
        request: UploadExternalNcActionAttachmentRequest,
    ) -> NonconformityAttachment:
        self._validate_request(request)

        action = self._action_repository.get_by_id(request.action_id.strip())
        if action is None:
            raise ValueError("Ação não encontrada.")

        attachment = NonconformityAttachment(
            id=str(uuid4()),
            nc_type=None,
            nc_id=None,
            action_id=action.id,
            effectiveness_check_id=None,
            file_name=request.file_name.strip(),
            original_name=request.original_name.strip(),
            mime_type=request.mime_type.strip() if request.mime_type else None,
            size_bytes=request.size_bytes,
            storage_provider=request.storage_provider.strip(),
            storage_path=request.storage_path.strip(),
            checksum=request.checksum.strip() if request.checksum else None,
            uploaded_by_user_id=request.uploaded_by_user_id.strip(),
            uploaded_at=datetime.now(timezone.utc),
        )

        created = self._attachment_repository.create(attachment)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=action.nonconformity_id,
                event_type="action_attachment_added",
                actor_user_id=request.uploaded_by_user_id.strip(),
                payload_json={
                    "attachment_id": created.id,
                    "action_id": action.id,
                    "file_name": created.file_name,
                    "original_name": created.original_name,
                    "storage_provider": created.storage_provider,
                    "size_bytes": created.size_bytes,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return created

    def _validate_request(
        self,
        request: UploadExternalNcActionAttachmentRequest,
    ) -> None:
        if not request.action_id or not request.action_id.strip():
            raise ValueError("action_id é obrigatório.")

        if not request.file_name or not request.file_name.strip():
            raise ValueError("file_name é obrigatório.")

        if not request.original_name or not request.original_name.strip():
            raise ValueError("original_name é obrigatório.")

        if request.size_bytes < 0:
            raise ValueError("size_bytes não pode ser negativo.")

        if not request.storage_provider or not request.storage_provider.strip():
            raise ValueError("storage_provider é obrigatório.")

        if not request.storage_path or not request.storage_path.strip():
            raise ValueError("storage_path é obrigatório.")

        if not request.uploaded_by_user_id or not request.uploaded_by_user_id.strip():
            raise ValueError("uploaded_by_user_id é obrigatório.")