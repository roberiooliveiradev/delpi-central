from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from pathlib import Path

from requests_app.application.errors import ApplicationError
from requests_app.application.security.requests_permissions import actor_for
from requests_app.application.services.attachment_storage import (
    AttachmentStorage,
    StorageError,
)
from requests_app.application.services.comment_body_policy import (
    assert_comment_body_media_policy,
)
from requests_app.application.services.requests_realtime_notify import (
    notify_request_timeline,
)
from requests_app.core.serialize import json_safe
from requests_app.domain.entities.files import (
    RequestComment,
    RequestCommentAttachment,
    RequestEvent,
)
from requests_app.domain.ports import RequestRepositoryPort, RequestTypeRepositoryPort
from requests_app.domain.ports.file_repository_port import FileRepositoryPort

logger = logging.getLogger(__name__)

# Access-log / conversation noise must not appear in the business timeline (Histórico).
TIMELINE_EXCLUDED_EVENT_TYPES = frozenset(
    {
        "attachment_downloaded",
        "artifact_downloaded",
        "commented",
        "comment_added",
    }
)


def _can_view(*, request, actor) -> bool:
    is_owner = request.created_by_user_id == actor.user_id
    return bool(is_owner or actor.has_view_all or actor.has_process or actor.has_manage)


def _safe_realtime(fn, **kwargs) -> None:
    try:
        fn(**kwargs)
    except Exception:  # noqa: BLE001
        logger.exception("requests_realtime_notify_failed")


class TimelineUseCases:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        files: FileRepositoryPort,
        attachment_storage: AttachmentStorage | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._files = files
        self._attachments = attachment_storage or AttachmentStorage()

    def _ctx(self, *, user, request_id: str):
        request = self._requests.get(request_id)
        if request is None:
            raise ApplicationError(code="not_found", status_code=404)
        request_type = self._types.get_by_code(request.type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        if not _can_view(request=request, actor=actor):
            raise ApplicationError(code="forbidden", status_code=403)
        return request, request_type, actor

    def _assert_conversation_mutable(self, *, request, request_type) -> None:
        workflow = request_type.workflow_definition or {}
        terminals = {
            str(item).strip()
            for item in (workflow.get("terminalStatuses") or [])
            if str(item).strip()
        }
        if request.status in terminals:
            raise ApplicationError(code="conversation_frozen", status_code=403)

    def _serialize_comment(self, comment: RequestComment, *, actor_user_id: str) -> dict[str, Any]:
        return json_safe(
            {
                "id": comment.id,
                "author_user_id": comment.author_user_id,
                "author_name": comment.author_name,
                "body": comment.body,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "is_mine": comment.author_user_id == actor_user_id,
            }
        )

    def list_events(
        self,
        *,
        user,
        request_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        self._ctx(user=user, request_id=request_id)
        items, total = self._files.list_events(
            request_id, page=page, page_size=page_size
        )
        visible = [
            item
            for item in items
            if str(item.event_type or "") not in TIMELINE_EXCLUDED_EVENT_TYPES
        ]
        # total reflects filtered page view; legacy noise rows stay in DB but hidden.
        excluded_on_page = len(items) - len(visible)
        return {
            "items": [
                json_safe(
                    {
                        "id": item.id,
                        "event_type": item.event_type,
                        "actor_user_id": item.actor_user_id,
                        "actor_name": item.actor_name,
                        "payload": item.payload,
                        "created_at": item.created_at,
                    }
                )
                for item in visible
            ],
            "total": max(total - excluded_on_page, len(visible)),
            "page": page,
            "page_size": page_size,
        }

    def list_comments(
        self,
        *,
        user,
        request_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        _request, _request_type, actor = self._ctx(user=user, request_id=request_id)
        items, total = self._files.list_comments(
            request_id, page=page, page_size=page_size
        )
        return {
            "items": [
                self._serialize_comment(item, actor_user_id=actor.user_id)
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def create_comment(
        self,
        *,
        user,
        request_id: str,
        body: str,
        actor_client_id: str | None = None,
    ) -> dict[str, Any]:
        request, request_type, actor = self._ctx(user=user, request_id=request_id)
        self._assert_conversation_mutable(request=request, request_type=request_type)
        text = (body or "").strip()
        if not text:
            raise ApplicationError(code="comment_required", status_code=422)
        assert_comment_body_media_policy(text)
        comment = self._files.create_comment(
            RequestComment(
                id=uuid4(),
                request_id=request.id,
                author_user_id=actor.user_id,
                author_name=actor.user_name,
                body=text,
            )
        )
        self._files.append_event(
            RequestEvent(
                id=uuid4(),
                request_id=request.id,
                event_type="commented",
                actor_user_id=actor.user_id,
                actor_name=actor.user_name,
                payload={"comment_id": str(comment.id)},
            )
        )
        _safe_realtime(
            notify_request_timeline,
            reason="comment.created",
            request_id=str(request.id),
            request_number=request.request_number,
            status=request.status,
            owner_user_id=request.created_by_user_id,
            actor_user_id=actor.user_id,
            actor_client_id=actor_client_id,
            notification={
                "title": "Novo comentário",
                "message": f"{actor.user_name} comentou em {request.request_number}.",
                "variant": "info",
            },
        )
        return self._serialize_comment(comment, actor_user_id=actor.user_id)

    def update_comment(
        self,
        *,
        user,
        request_id: str,
        comment_id: str,
        body: str,
        mark_as_edited: bool = True,
        actor_client_id: str | None = None,
    ) -> dict[str, Any]:
        request, request_type, actor = self._ctx(user=user, request_id=request_id)
        self._assert_conversation_mutable(request=request, request_type=request_type)
        comment = self._files.get_comment(comment_id)
        if comment is None or str(comment.request_id) != str(request.id):
            raise ApplicationError(code="not_found", status_code=404)
        is_author = comment.author_user_id == actor.user_id
        if not (is_author or actor.has_manage):
            raise ApplicationError(code="forbidden", status_code=403)
        text = (body or "").strip()
        if not text:
            raise ApplicationError(code="comment_required", status_code=422)
        assert_comment_body_media_policy(text)
        updated = self._files.update_comment_body(
            comment_id,
            body=text,
            touch_updated_at=bool(mark_as_edited),
        )
        if updated is None:
            raise ApplicationError(code="not_found", status_code=404)
        _safe_realtime(
            notify_request_timeline,
            reason="comment.updated",
            request_id=str(request.id),
            request_number=request.request_number,
            status=request.status,
            owner_user_id=request.created_by_user_id,
            actor_user_id=actor.user_id,
            actor_client_id=actor_client_id,
        )
        return self._serialize_comment(updated, actor_user_id=actor.user_id)

    def upload_comment_attachment(
        self,
        *,
        user,
        request_id: str,
        comment_id: str,
        original_name: str,
        content: bytes,
        mime_type: str | None,
        actor_client_id: str | None = None,
    ) -> dict[str, Any]:
        request, request_type, actor = self._ctx(user=user, request_id=request_id)
        self._assert_conversation_mutable(request=request, request_type=request_type)
        comment = self._files.get_comment(comment_id)
        if comment is None or str(comment.request_id) != str(request.id):
            raise ApplicationError(code="not_found", status_code=404)
        is_author = comment.author_user_id == actor.user_id
        if not (is_author or actor.has_manage):
            raise ApplicationError(code="upload_forbidden", status_code=403)
        try:
            stored = self._attachments.save(
                request_id=str(request.id),
                original_name=original_name,
                content=content,
                mime_type=mime_type,
                comment_id=str(comment.id),
            )
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=422, detail=str(exc)
            ) from exc
        attachment = self._files.create_comment_attachment(
            RequestCommentAttachment(
                id=uuid4(),
                request_id=request.id,
                comment_id=comment.id,
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
        _safe_realtime(
            notify_request_timeline,
            reason="comment.attachment.created",
            request_id=str(request.id),
            request_number=request.request_number,
            status=request.status,
            owner_user_id=request.created_by_user_id,
            actor_user_id=actor.user_id,
            actor_client_id=actor_client_id,
        )
        return json_safe(
            {
                "id": attachment.id,
                "request_id": attachment.request_id,
                "comment_id": attachment.comment_id,
                "original_name": attachment.original_name,
                "mime_type": attachment.mime_type,
                "size_bytes": attachment.size_bytes,
                "created_at": attachment.created_at,
            }
        )

    def list_comment_attachments(
        self, *, user, request_id: str, comment_id: str
    ) -> dict[str, Any]:
        request, _request_type, _actor = self._ctx(user=user, request_id=request_id)
        comment = self._files.get_comment(comment_id)
        if comment is None or str(comment.request_id) != str(request.id):
            raise ApplicationError(code="not_found", status_code=404)
        items = [
            json_safe(
                {
                    "id": item.id,
                    "request_id": item.request_id,
                    "comment_id": item.comment_id,
                    "original_name": item.original_name,
                    "mime_type": item.mime_type,
                    "size_bytes": item.size_bytes,
                    "created_at": item.created_at,
                }
            )
            for item in self._files.list_comment_attachments(comment_id)
        ]
        return {"items": items}

    def resolve_comment_attachment_path(
        self, *, user, request_id: str, comment_id: str, attachment_id: str
    ) -> tuple[Path, RequestCommentAttachment]:
        request, _request_type, _actor = self._ctx(user=user, request_id=request_id)
        comment = self._files.get_comment(comment_id)
        if comment is None or str(comment.request_id) != str(request.id):
            raise ApplicationError(code="not_found", status_code=404)
        attachment = self._files.get_comment_attachment(attachment_id)
        if attachment is None or str(attachment.comment_id) != str(comment.id):
            raise ApplicationError(code="attachment_not_found", status_code=404)
        try:
            path = self._attachments.resolve_file(storage_key=attachment.storage_key)
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=404, detail=str(exc)
            ) from exc
        return path, attachment

    def delete_comment_attachment(
        self,
        *,
        user,
        request_id: str,
        comment_id: str,
        attachment_id: str,
        actor_client_id: str | None = None,
    ) -> dict[str, Any]:
        request, request_type, actor = self._ctx(user=user, request_id=request_id)
        self._assert_conversation_mutable(request=request, request_type=request_type)
        comment = self._files.get_comment(comment_id)
        if comment is None or str(comment.request_id) != str(request.id):
            raise ApplicationError(code="not_found", status_code=404)
        attachment = self._files.get_comment_attachment(attachment_id)
        if attachment is None or str(attachment.comment_id) != str(comment.id):
            raise ApplicationError(code="attachment_not_found", status_code=404)
        is_author = comment.author_user_id == actor.user_id
        if not (is_author or actor.has_manage):
            raise ApplicationError(code="delete_forbidden", status_code=403)
        try:
            self._attachments.delete_file(storage_key=attachment.storage_key)
        except StorageError as exc:
            raise ApplicationError(
                code=exc.code, status_code=422, detail=str(exc)
            ) from exc
        deleted = self._files.delete_comment_attachment(attachment_id)
        if not deleted:
            raise ApplicationError(code="attachment_not_found", status_code=404)
        _safe_realtime(
            notify_request_timeline,
            reason="comment.attachment.removed",
            request_id=str(request.id),
            request_number=request.request_number,
            status=request.status,
            owner_user_id=request.created_by_user_id,
            actor_user_id=actor.user_id,
            actor_client_id=actor_client_id,
        )
        return json_safe(
            {
                "id": attachment.id,
                "request_id": attachment.request_id,
                "comment_id": attachment.comment_id,
                "original_name": attachment.original_name,
            }
        )
