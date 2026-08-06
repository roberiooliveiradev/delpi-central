from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Path, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_FOLLOWUPS_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    COMMERCIAL_WORKLIST_PERMISSIONS,
)
from commercial_app.application.use_cases.manage_worklist import (
    CreateActivityInput,
    CreateTaskInput,
)
from commercial_app.composition.commercial_composer import build_manage_worklist_use_case
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.schemas.worklist_schemas import (
    CreateActivityBody,
    CreateTaskBody,
)

logger = logging.getLogger(__name__)

me_router = APIRouter(prefix="/me", tags=["Me / worklist"])
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])
activities_router = APIRouter(prefix="/activities", tags=["Activities"])


def _user_id(request: Request) -> str | None:
    return actor_sub_from_request(request)


def _use_case():
    return build_manage_worklist_use_case()


@me_router.get("/worklist", operation_id="get_my_worklist")
@require_any_permission(*COMMERCIAL_WORKLIST_PERMISSIONS)
def get_my_worklist(request: Request):
    try:
        user_id = _user_id(request)
        if not user_id:
            return fail("Usuário não identificado.", 401, operation_id="get_my_worklist")
        data = _use_case().get_worklist(user_id=user_id)
        return ok(data, message="Worklist carregada.", operation_id="get_my_worklist")
    except Exception:
        logger.exception("get_my_worklist_failed")
        return fail("Erro interno ao carregar worklist.", 500, operation_id="get_my_worklist")


@tasks_router.get("", operation_id="list_tasks")
@require_any_permission(*COMMERCIAL_WORKLIST_PERMISSIONS)
def list_tasks(
    request: Request,
    status: str | None = Query("open", description="Filtro de status; omita para todos abertos."),
):
    try:
        user_id = _user_id(request)
        if not user_id:
            return fail("Usuário não identificado.", 401, operation_id="list_tasks")
        items = _use_case().list_tasks(user_id=user_id, status=status)
        return ok(
            {"items": [item.to_dict() for item in items]},
            message="Tarefas carregadas.",
            operation_id="list_tasks",
        )
    except Exception:
        logger.exception("list_tasks_failed")
        return fail("Erro interno ao listar tarefas.", 500, operation_id="list_tasks")


@tasks_router.post("", operation_id="create_task")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS)
def create_task(request: Request, body: CreateTaskBody):
    try:
        user_id = _user_id(request)
        if not user_id:
            return fail("Usuário não identificado.", 401, operation_id="create_task")
        task = _use_case().create_task(
            user_id=user_id,
            data=CreateTaskInput(
                title=body.title,
                description=body.description,
                task_type=body.task_type,
                priority=body.priority,
                due_at=body.due_at,
                customer_code=body.customer_code,
                customer_store=body.customer_store,
            ),
        )
        return ok(task.to_dict(), message="Tarefa criada.", operation_id="create_task")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="create_task")
    except Exception:
        logger.exception("create_task_failed")
        return fail("Erro interno ao criar tarefa.", 500, operation_id="create_task")


@tasks_router.post("/{task_id}/complete", operation_id="complete_task")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS)
def complete_task(request: Request, task_id: UUID = Path(...)):
    try:
        user_id = _user_id(request)
        if not user_id:
            return fail("Usuário não identificado.", 401, operation_id="complete_task")
        task = _use_case().complete_task(user_id=user_id, task_id=task_id)
        return ok(task.to_dict(), message="Tarefa concluída.", operation_id="complete_task")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="complete_task")
    except Exception:
        logger.exception("complete_task_failed")
        return fail("Erro interno ao concluir tarefa.", 500, operation_id="complete_task")


@activities_router.post("", operation_id="create_activity")
@require_any_permission(*COMMERCIAL_FOLLOWUPS_PERMISSIONS)
def create_activity(request: Request, body: CreateActivityBody):
    try:
        user_id = _user_id(request)
        if not user_id:
            return fail("Usuário não identificado.", 401, operation_id="create_activity")
        activity = _use_case().create_activity(
            user_id=user_id,
            data=CreateActivityInput(
                activity_type=body.activity_type,
                subject=body.subject,
                body=body.body,
                occurred_at=body.occurred_at,
                customer_code=body.customer_code,
                customer_store=body.customer_store,
                task_id=body.task_id,
            ),
        )
        return ok(activity.to_dict(), message="Atividade registrada.", operation_id="create_activity")
    except ValueError as exc:
        return fail(str(exc), 422, operation_id="create_activity")
    except Exception:
        logger.exception("create_activity_failed")
        return fail("Erro interno ao registrar atividade.", 500, operation_id="create_activity")


@activities_router.get("", operation_id="list_customer_activities")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def list_customer_activities(
    request: Request,
    customer_code: str = Query(..., min_length=1),
    customer_store: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100),
):
    try:
        items = _use_case().list_customer_activities(
            customer_code=customer_code.strip(),
            customer_store=customer_store.strip(),
            limit=limit,
        )
        return ok(
            {"items": [item.to_dict() for item in items]},
            message="Atividades carregadas.",
            operation_id="list_customer_activities",
        )
    except Exception:
        logger.exception("list_customer_activities_failed")
        return fail(
            "Erro interno ao listar atividades.",
            500,
            operation_id="list_customer_activities",
        )
