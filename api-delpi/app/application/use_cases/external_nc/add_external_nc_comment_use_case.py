# app/application/use_cases/external_nc/add_external_nc_comment_use_case.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.application.dto.external_nc.add_external_nc_comment_request import (
    AddExternalNcCommentRequest,
)
from app.domain.entities.shared_quality.nonconformity_comment import (
    NonconformityComment,
)
from app.domain.ports.external_nc.external_nonconformity_repository import (
    ExternalNonconformityRepositoryPort,
)
from app.domain.ports.shared_quality.audit_event_repository import (
    AuditEventRepositoryPort,
)
from app.domain.ports.shared_quality.comment_repository import (
    CommentRepositoryPort,
)
from app.domain.entities.shared_quality.nonconformity_audit_event import (
    NonconformityAuditEvent,
)


class AddExternalNcCommentUseCase:
    def __init__(
        self,
        repository: ExternalNonconformityRepositoryPort,
        comment_repository: CommentRepositoryPort,
        audit_event_repository: AuditEventRepositoryPort,
    ) -> None:
        self._repository = repository
        self._comment_repository = comment_repository
        self._audit_event_repository = audit_event_repository

    def execute(self, request: AddExternalNcCommentRequest) -> NonconformityComment:
        self._validate_request(request)

        entity = self._repository.get_by_id(request.nonconformity_id.strip())
        if entity is None:
            raise ValueError("Não conformidade externa não encontrada.")

        comment = NonconformityComment(
            id=str(uuid4()),
            nc_type="external_nonconformity",
            nc_id=entity.id,
            comment_type=request.comment_type.strip(),
            content=request.content.strip(),
            is_internal=request.is_internal,
            created_by_user_id=request.created_by_user_id.strip(),
            created_at=datetime.now(timezone.utc),
        )

        created = self._comment_repository.create(comment)

        self._audit_event_repository.create(
            NonconformityAuditEvent(
                id=str(uuid4()),
                entity_type="external_nonconformity",
                entity_id=entity.id,
                event_type="comment_added",
                actor_user_id=request.created_by_user_id.strip(),
                payload_json={
                    "comment_id": created.id,
                    "comment_type": created.comment_type,
                    "is_internal": created.is_internal,
                },
                created_at=datetime.now(timezone.utc),
            )
        )

        return created

    def _validate_request(self, request: AddExternalNcCommentRequest) -> None:
        if not request.nonconformity_id or not request.nonconformity_id.strip():
            raise ValueError("nonconformity_id é obrigatório.")

        if not request.comment_type or not request.comment_type.strip():
            raise ValueError("comment_type é obrigatório.")

        if not request.content or not request.content.strip():
            raise ValueError("content é obrigatório.")

        if not request.created_by_user_id or not request.created_by_user_id.strip():
            raise ValueError("created_by_user_id é obrigatório.")