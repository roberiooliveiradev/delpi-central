from __future__ import annotations

from typing import Any
from uuid import uuid4

from requests_app.application.errors import ApplicationError
from requests_app.application.security.requests_permissions import (
    VALID_BRANCHES,
    actor_for,
    has_branch_access,
)
from requests_app.application.serializers import allowed_actions_for, serialize_request
from requests_app.domain.entities import Actor, Request, StatusHistoryEntry
from requests_app.domain.entities.files import RequestEvent
from requests_app.domain.exceptions import WorkflowEngineError
from requests_app.domain.ports import (
    IdempotencyRepositoryPort,
    RequestRepositoryPort,
    RequestTypeRepositoryPort,
)
from requests_app.domain.ports.file_repository_port import FileRepositoryPort
from requests_app.domain.services.workflow_engine import WorkflowEngine


def _normalize_branch(raw: Any) -> str | None:
    text = str(raw or "").strip()
    return text or None


def _validate_branch(
    *,
    actor: Actor,
    branch_code: str | None,
    branch_scope: str,
) -> str | None:
    scope = (branch_scope or "optional").strip()
    if scope == "none":
        return None
    if scope == "required" and not branch_code:
        raise ApplicationError(code="branch_required", status_code=422)
    if branch_code and branch_code not in VALID_BRANCHES:
        raise ApplicationError(code="branch_invalid", status_code=422)
    if branch_code and not has_branch_access(actor, branch_code):
        raise ApplicationError(code="branch_forbidden", status_code=403)
    return branch_code


class CreateRequestUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        idempotency: IdempotencyRepositoryPort,
        engine: WorkflowEngine | None = None,
        files: FileRepositoryPort | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._idempotency = idempotency
        self._engine = engine or WorkflowEngine()
        self._files = files

    def execute(
        self,
        *,
        user,
        type_code: str,
        payload: dict[str, Any] | None,
        branch_code: str | None = None,
        priority: str = "normal",
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key or not str(idempotency_key).strip():
            raise ApplicationError(code="idempotency_required", status_code=422)

        route = "POST /v1/requests"
        actor_id = str(getattr(user, "id", "") or "unknown")
        cached = self._idempotency.get(
            key=str(idempotency_key).strip(),
            route=route,
            actor_user_id=actor_id,
        )
        if cached is not None:
            return cached

        request_type = self._types.get_by_code(type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        if not request_type.active:
            raise ApplicationError(code="type_inactive", status_code=409)

        actor = actor_for(user, request_type)
        if not actor.has_create and not actor.has_manage:
            raise ApplicationError(code="create_forbidden", status_code=403)

        branch = _validate_branch(
            actor=actor,
            branch_code=_normalize_branch(branch_code),
            branch_scope=request_type.branch_scope,
        )
        if payload is None or not isinstance(payload, dict):
            raise ApplicationError(code="payload_required", status_code=422)

        workflow = request_type.workflow_definition or {}
        initial = str(workflow.get("initialStatus") or "submitted")
        request = Request(
            id=uuid4(),
            request_number=self._requests.next_request_number(),
            request_type_id=request_type.id,
            type_code=request_type.code,
            status=initial,
            priority=priority if priority in {"normal", "high", "urgent"} else "normal",
            branch_code=branch,
            created_by_user_id=actor.user_id,
            created_by_name=actor.user_name,
            payload=payload,
            version=1,
        )
        history = StatusHistoryEntry(
            from_status=None,
            to_status=initial,
            action="created",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
        )
        stored = self._requests.create(request, history=history)
        if self._files is not None:
            self._files.append_event(
                RequestEvent(
                    id=uuid4(),
                    request_id=stored.id,
                    event_type="created",
                    actor_user_id=actor.user_id,
                    actor_name=actor.user_name,
                    payload={"status": stored.status},
                )
            )
        actions = allowed_actions_for(
            stored, actor=actor, workflow=workflow, engine=self._engine
        )
        result = serialize_request(stored, allowed_actions=actions, workflow=workflow)
        self._idempotency.save(
            key=str(idempotency_key).strip(),
            route=route,
            actor_user_id=actor_id,
            response_snapshot=result,
        )
        return result


class ListMyRequestsUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        engine: WorkflowEngine | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._engine = engine or WorkflowEngine()

    def execute(
        self,
        *,
        user,
        type_code: str | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        actor = actor_for(user)
        if not actor.has_access and not actor.has_view_all and not actor.has_manage:
            # still allow if they have any create somewhere — module access
            from requests_app.application.security.requests_permissions import module_actor

            actor = module_actor(user)
            if not actor.has_access and not actor.has_view_all and not actor.has_manage:
                raise ApplicationError(code="forbidden", status_code=403)

        items, total = self._requests.list_mine(
            user_id=str(getattr(user, "id", "") or ""),
            type_code=type_code,
            status=status,
            branch_code=branch_code,
            page=page,
            page_size=page_size,
        )
        serialized = []
        for item in items:
            request_type = self._types.get_by_code(item.type_code)
            workflow = (request_type.workflow_definition if request_type else {}) or {}
            typed_actor = actor_for(user, request_type) if request_type else actor
            actions = allowed_actions_for(
                item, actor=typed_actor, workflow=workflow, engine=self._engine
            )
            serialized.append(
                serialize_request(item, allowed_actions=actions, workflow=workflow)
            )
        return {"items": serialized, "total": total, "page": page, "page_size": page_size}


class ListWorkQueueRequestsUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        engine: WorkflowEngine | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._engine = engine or WorkflowEngine()

    def execute(
        self,
        *,
        user,
        type_code: str | None = None,
        status: str | None = None,
        branch_code: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        active_types = self._types.list_active()
        processable: list[str] = []
        terminals_by_type: dict[str, set[str]] = {}
        for request_type in active_types:
            actor = actor_for(user, request_type)
            if actor.has_process or actor.has_view_all or actor.has_manage:
                processable.append(request_type.code)
                terminals_by_type[request_type.code] = set(
                    (request_type.workflow_definition or {}).get("terminalStatuses") or []
                )

        if type_code:
            if type_code not in processable:
                raise ApplicationError(code="forbidden", status_code=403)
            processable = [type_code]

        if not processable:
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        # exclude all terminals that appear in selected types
        excluded: set[str] = set()
        for code in processable:
            excluded |= terminals_by_type.get(code, set())

        if branch_code:
            sample_actor = actor_for(user, active_types[0] if active_types else None)
            if not has_branch_access(sample_actor, branch_code):
                raise ApplicationError(code="branch_forbidden", status_code=403)

        items, total = self._requests.list_work_queue(
            type_codes=processable,
            status=status,
            branch_code=branch_code,
            exclude_statuses=None if status else sorted(excluded),
            page=page,
            page_size=page_size,
        )
        serialized = []
        for item in items:
            request_type = self._types.get_by_code(item.type_code)
            workflow = (request_type.workflow_definition if request_type else {}) or {}
            typed_actor = actor_for(user, request_type) if request_type else actor_for(user)
            actions = allowed_actions_for(
                item, actor=typed_actor, workflow=workflow, engine=self._engine
            )
            serialized.append(
                serialize_request(item, allowed_actions=actions, workflow=workflow)
            )
        return {"items": serialized, "total": total, "page": page, "page_size": page_size}


class GetRequestUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        engine: WorkflowEngine | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._engine = engine or WorkflowEngine()

    def execute(self, *, user, request_id: str) -> dict[str, Any]:
        request = self._requests.get(request_id)
        if request is None:
            raise ApplicationError(code="not_found", status_code=404)
        request_type = self._types.get_by_code(request.type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        is_owner = request.created_by_user_id == actor.user_id
        if not (is_owner or actor.has_view_all or actor.has_process or actor.has_manage):
            raise ApplicationError(code="forbidden", status_code=403)
        if request.branch_code and not has_branch_access(actor, request.branch_code):
            if not is_owner:
                raise ApplicationError(code="branch_forbidden", status_code=403)
        workflow = request_type.workflow_definition or {}
        actions = allowed_actions_for(
            request, actor=actor, workflow=workflow, engine=self._engine
        )
        return serialize_request(request, allowed_actions=actions, workflow=workflow)


class UpdateRequestPayloadUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        idempotency: IdempotencyRepositoryPort,
        engine: WorkflowEngine | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._idempotency = idempotency
        self._engine = engine or WorkflowEngine()

    def execute(
        self,
        *,
        user,
        request_id: str,
        payload: dict[str, Any],
        expected_version: int | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key or not str(idempotency_key).strip():
            raise ApplicationError(code="idempotency_required", status_code=422)
        route = f"PATCH /v1/requests/{request_id}"
        actor_id = str(getattr(user, "id", "") or "unknown")
        cached = self._idempotency.get(
            key=str(idempotency_key).strip(),
            route=route,
            actor_user_id=actor_id,
        )
        if cached is not None:
            return cached

        request = self._requests.get(request_id)
        if request is None:
            raise ApplicationError(code="not_found", status_code=404)
        request_type = self._types.get_by_code(request.type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        workflow = request_type.workflow_definition or {}
        actions = allowed_actions_for(
            request, actor=actor, workflow=workflow, engine=self._engine
        )
        if "edit" not in actions:
            raise ApplicationError(code="edit_forbidden", status_code=403)
        if not isinstance(payload, dict):
            raise ApplicationError(code="payload_required", status_code=422)
        if expected_version is not None and request.version != expected_version:
            raise ApplicationError(code="stale_version", status_code=409)

        current_version = request.version
        updated = request
        updated.payload = payload
        updated.version = current_version + 1
        history = StatusHistoryEntry(
            from_status=request.status,
            to_status=request.status,
            action="edit",
            actor_user_id=actor.user_id,
            actor_name=actor.user_name,
            changes={"payload": True},
        )
        try:
            stored = self._requests.update(
                updated,
                history=history,
                expected_version=current_version,
            )
        except WorkflowEngineError as exc:
            raise ApplicationError(
                code=exc.code,
                status_code=exc.status_code,
                field=exc.field,
            ) from exc
        result = serialize_request(
            stored,
            allowed_actions=allowed_actions_for(
                stored, actor=actor, workflow=workflow, engine=self._engine
            ),
            workflow=workflow,
        )
        self._idempotency.save(
            key=str(idempotency_key).strip(),
            route=route,
            actor_user_id=actor_id,
            response_snapshot=result,
        )
        return result


class TransitionRequestUseCase:
    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        requests: RequestRepositoryPort,
        idempotency: IdempotencyRepositoryPort,
        engine: WorkflowEngine | None = None,
        files: FileRepositoryPort | None = None,
    ) -> None:
        self._types = types
        self._requests = requests
        self._idempotency = idempotency
        self._engine = engine or WorkflowEngine()
        self._files = files

    def execute(
        self,
        *,
        user,
        request_id: str,
        action: str,
        body: dict[str, Any] | None = None,
        expected_version: int | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        if not idempotency_key or not str(idempotency_key).strip():
            raise ApplicationError(code="idempotency_required", status_code=422)
        route = f"POST /v1/requests/{request_id}/transitions/{action}"
        actor_id = str(getattr(user, "id", "") or "unknown")
        cached = self._idempotency.get(
            key=str(idempotency_key).strip(),
            route=route,
            actor_user_id=actor_id,
        )
        if cached is not None:
            return cached

        request = self._requests.get(request_id)
        if request is None:
            raise ApplicationError(code="not_found", status_code=404)
        request_type = self._types.get_by_code(request.type_code)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        workflow = request_type.workflow_definition or {}
        try:
            result = self._engine.apply_transition(
                request=request,
                actor=actor,
                workflow=workflow,
                action=action,
                body=body or {},
                expected_version=expected_version
                if expected_version is not None
                else request.version,
            )
        except WorkflowEngineError as exc:
            raise ApplicationError(
                code=exc.code,
                status_code=exc.status_code,
                field=exc.field,
            ) from exc

        stored = self._requests.update(
            result.request,
            history=result.history,
            assignment=result.assignment,
            expected_version=request.version,
        )
        if self._files is not None:
            self._files.append_event(
                RequestEvent(
                    id=uuid4(),
                    request_id=stored.id,
                    event_type="transition",
                    actor_user_id=actor.user_id,
                    actor_name=actor.user_name,
                    payload={
                        "action": result.history.action,
                        "from_status": result.history.from_status,
                        "to_status": result.history.to_status,
                    },
                )
            )
        response = serialize_request(
            stored,
            allowed_actions=allowed_actions_for(
                stored, actor=actor, workflow=workflow, engine=self._engine
            ),
            workflow=workflow,
        )
        self._idempotency.save(
            key=str(idempotency_key).strip(),
            route=route,
            actor_user_id=actor_id,
            response_snapshot=response,
        )
        return response


class ListRequestTypesUseCase:
    def __init__(self, types: RequestTypeRepositoryPort) -> None:
        self._types = types

    def execute(self, *, user) -> dict[str, Any]:
        from requests_app.application.security.requests_permissions import module_actor
        from requests_app.application.serializers import serialize_request_type

        actor = module_actor(user)
        if not actor.has_access and not actor.has_view_all and not actor.has_manage:
            raise ApplicationError(code="forbidden", status_code=403)
        items = [serialize_request_type(item) for item in self._types.list_active()]
        return {"items": items}


class GetRequestTypeUseCase:
    def __init__(self, types: RequestTypeRepositoryPort) -> None:
        self._types = types

    def execute(self, *, user, code: str) -> dict[str, Any]:
        from requests_app.application.security.requests_permissions import module_actor
        from requests_app.application.serializers import serialize_request_type

        actor = module_actor(user)
        if not actor.has_access and not actor.has_view_all and not actor.has_manage:
            raise ApplicationError(code="forbidden", status_code=403)
        request_type = self._types.get_by_code(code)
        if request_type is None or not request_type.active:
            raise ApplicationError(code="type_not_found", status_code=404)
        return serialize_request_type(request_type)
