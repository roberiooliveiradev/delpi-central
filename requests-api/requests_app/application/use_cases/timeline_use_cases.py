from __future__ import annotations

from typing import Any
from uuid import uuid4

from requests_app.application.errors import ApplicationError
from requests_app.application.security.requests_permissions import actor_for
from requests_app.core.serialize import json_safe
from requests_app.domain.entities.files import RequestComment, RequestEvent
from requests_app.domain.ports import RequestRepositoryPort, RequestTypeRepositoryPort
from requests_app.domain.ports.file_repository_port import FileRepositoryPort


def _can_view(*, request, actor) -> bool:
    is_owner = request.created_by_user_id == actor.user_id
    return bool(is_owner or actor.has_view_all or actor.has_process or actor.has_manage)


class TimelineUseCases:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        files: FileRepositoryPort,
    ) -> None:
        self._types = types
        self._requests = requests
        self._files = files

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
        return request, actor

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
                for item in items
            ],
            "total": total,
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
        self._ctx(user=user, request_id=request_id)
        items, total = self._files.list_comments(
            request_id, page=page, page_size=page_size
        )
        return {
            "items": [
                json_safe(
                    {
                        "id": item.id,
                        "author_user_id": item.author_user_id,
                        "author_name": item.author_name,
                        "body": item.body,
                        "created_at": item.created_at,
                    }
                )
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def create_comment(self, *, user, request_id: str, body: str) -> dict[str, Any]:
        request, actor = self._ctx(user=user, request_id=request_id)
        text = (body or "").strip()
        if not text:
            raise ApplicationError(code="comment_required", status_code=422)
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
        return json_safe(
            {
                "id": comment.id,
                "author_user_id": comment.author_user_id,
                "author_name": comment.author_name,
                "body": comment.body,
                "created_at": comment.created_at,
            }
        )
