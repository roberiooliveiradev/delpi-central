from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.application.use_cases.list_my_task_items import ListMyTaskItemsUseCase
from tm_app.application.use_cases.manage_transformometro_tasks import TaskCommandUseCases
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.persistence.repositories.task_repository import TaskRepository

router = APIRouter(prefix="/transformometro", tags=["Transformômetro Tasks"])
_commands = TaskCommandUseCases(TaskRepository())
_minutes = MeetingMinutesService()
_list_items = ListMyTaskItemsUseCase(_commands, _minutes.pending_signatures)


class CreateTaskBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    assignee_user_id: str | None = None
    due_date: str | None = None


class UpdateTaskBody(CreateTaskBody):
    pass


def _handle(exc: Exception):
    if isinstance(exc, AuthorizationDenied):
        return fail(str(exc), exc.status_code)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, RuntimeError) and str(exc) == "OUTCOME_VERIFICATION_FAILED":
        return fail("A gravação não confirmou o estado esperado.", 409)
    raise exc


@router.get("/my-tasks", operation_id="list_my_transformometro_tasks")
def list_my_tasks(request: Request, status: str = "pending"):
    try:
        return ok(_list_items.execute(request.state.user, status=status))
    except Exception as exc:
        return _handle(exc)


@router.post("/tasks", operation_id="create_transformometro_task")
def create_task(request: Request, body: CreateTaskBody):
    try:
        return ok(
            _commands.create(
                request.state.user,
                title=body.title,
                description=body.description,
                assignee_user_id=body.assignee_user_id,
                due_date=body.due_date,
            ).to_dict(),
            status_code=201,
        )
    except Exception as exc:
        return _handle(exc)


@router.get("/tasks/{task_id}", operation_id="get_transformometro_task")
def get_task(request: Request, task_id: str):
    try:
        return ok(_commands.get(request.state.user, task_id).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.patch("/tasks/{task_id}", operation_id="update_transformometro_task")
def update_task(request: Request, task_id: str, body: UpdateTaskBody):
    try:
        return ok(
            _commands.update(
                request.state.user,
                task_id,
                title=body.title,
                description=body.description,
                assignee_user_id=body.assignee_user_id,
                due_date=body.due_date,
            ).to_dict()
        )
    except Exception as exc:
        return _handle(exc)


@router.post("/tasks/{task_id}/complete", operation_id="complete_transformometro_task")
def complete_task(request: Request, task_id: str):
    try:
        return ok(_commands.complete(request.state.user, task_id).to_dict())
    except Exception as exc:
        return _handle(exc)


@router.post("/tasks/{task_id}/cancel", operation_id="cancel_transformometro_task")
def cancel_task(request: Request, task_id: str):
    try:
        return ok(_commands.cancel(request.state.user, task_id).to_dict())
    except Exception as exc:
        return _handle(exc)
