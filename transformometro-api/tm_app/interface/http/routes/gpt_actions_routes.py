"""HTTP surface for OpenAI Custom GPT Actions (compact OpenAPI facade)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.entities import parse_entity
from tm_app.application.gpt_actions.openapi_builder import build_gpt_actions_openapi
from tm_app.core.errors import format_api_error
from tm_app.core.responses import fail, ok

router = APIRouter(
    prefix="/transformometro/gpt-actions/v1",
    tags=["Transformômetro GPT Actions"],
)
logger = logging.getLogger(__name__)
_dispatch = GptActionsDispatchService()


class GptRecordBody(BaseModel):
    data: dict = Field(default_factory=dict)


class GptRecalculateBody(BaseModel):
    revisao_id: str | None = None
    processo_id: str | None = None
    competencia_inicio: str | None = None
    competencia_fim: str | None = None


class GptMeetingMinuteWorkflowBody(BaseModel):
    action: str
    reason: str | None = None


def _handle(exc: Exception):
    if isinstance(exc, GptActionsError):
        return fail(exc.message, exc.status_code, exc.data)
    if isinstance(exc, ValueError):
        return fail(str(exc), 400)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    logger.exception("gpt_actions_unhandled")
    return fail(format_api_error(exc), 500)


@router.get(
    "/openapi.json",
    operation_id="gpt_get_openapi_schema",
    summary="Public OpenAPI schema for Custom GPT import",
)
def gpt_get_openapi_schema():
    return build_gpt_actions_openapi()


@router.get(
    "/catalog",
    operation_id="gpt_get_catalog",
    summary="Catalog options for Transformômetro forms",
)
def gpt_get_catalog(request: Request):
    try:
        return ok(_dispatch.get_catalog(request), "Catálogo do Transformômetro.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/analysis",
    operation_id="gpt_analyze",
    summary="Analyze dashboard KPIs from snapshot/live cache",
)
def gpt_analyze(
    request: Request,
    view: str = Query(..., description="meta|summary|processes|instances|rows"),
    filial_id: str | None = None,
    setor_id: str | None = None,
    processo_id: str | None = None,
    revisao_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    limit: int | None = Query(default=None, ge=1, le=500),
):
    try:
        data = _dispatch.analyze(
            request,
            view=view,
            filial_id=filial_id,
            setor_id=setor_id,
            processo_id=processo_id,
            revisao_id=revisao_id,
            familia_processo=familia_processo,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            limit=limit,
        )
        return ok(data, "Análise do Transformômetro.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/records/{entity}",
    operation_id="gpt_search_records",
    summary="Search or list records by entity",
)
def gpt_search_records(
    entity: str,
    request: Request,
    parent_id: str | None = None,
    filial_id: str | None = None,
    setor_id: str | None = None,
    status: str | None = None,
    familia_processo: str | None = None,
    q: str | None = None,
    unit_code: str | None = None,
):
    try:
        parse_entity(entity)
        data = _dispatch.search_records(
            request,
            entity,
            parent_id=parent_id,
            filial_id=filial_id,
            setor_id=setor_id,
            status=status,
            familia_processo=familia_processo,
            q=q,
            unit_code=unit_code,
        )
        return ok(data, "Lista de registros.")
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/records/{entity}/{id}",
    operation_id="gpt_get_record",
    summary="Get one record by entity and id",
)
def gpt_get_record(entity: str, id: str, request: Request):
    try:
        return ok(_dispatch.get_record(request, entity, id), "Registro.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/records/{entity}",
    operation_id="gpt_create_record",
    summary="Create a Transformômetro record",
)
def gpt_create_record(entity: str, body: GptRecordBody, request: Request):
    try:
        result = _dispatch.create_record(request, entity, body.model_dump())
        data, message, status = result
        return ok(data, message, status)
    except Exception as exc:
        return _handle(exc)


@router.put(
    "/records/{entity}/{id}",
    operation_id="gpt_update_record",
    summary="Update a Transformômetro record",
)
def gpt_update_record(entity: str, id: str, body: GptRecordBody, request: Request):
    try:
        data, message = _dispatch.update_record(request, entity, id, body.model_dump())
        return ok(data, message)
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/records/{entity}/{id}",
    operation_id="gpt_delete_record",
    summary="Soft-delete a Transformômetro record",
)
def gpt_delete_record(entity: str, id: str, request: Request):
    try:
        data, message = _dispatch.delete_record(request, entity, id)
        return ok(data, message)
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/records/{entity}/{id}/duplicate",
    operation_id="gpt_duplicate_record",
    summary="Duplicate process, instance, or revision",
)
def gpt_duplicate_record(
    entity: str,
    id: str,
    request: Request,
    body: GptRecordBody | None = None,
):
    try:
        data, message, status = _dispatch.duplicate_record(
            request,
            entity,
            id,
            body.model_dump() if body else None,
        )
        return ok(data, message, status)
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/revisions/{id}/activate",
    operation_id="gpt_activate_revision",
    summary="Activate a revision as the operational current version",
)
def gpt_activate_revision(id: str, request: Request):
    try:
        return ok(
            _dispatch.activate_revision(request, id),
            "Revisão ativada.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/dashboard/recalculate",
    operation_id="gpt_recalculate_dashboard",
    summary="Recalculate materialised dashboard cache",
)
def gpt_recalculate_dashboard(
    request: Request,
    body: GptRecalculateBody | None = None,
):
    try:
        payload = body.model_dump() if body else {}
        result = _dispatch.recalculate_dashboard(
            request,
            revisao_id=payload.get("revisao_id"),
            processo_id=payload.get("processo_id"),
            competencia_inicio=payload.get("competencia_inicio"),
            competencia_fim=payload.get("competencia_fim"),
        )
        mode = result.get("mode")
        message = (
            "Cache do dashboard atualizado (incremental)."
            if mode == "incremental"
            else "Cache do dashboard atualizado (completo)."
        )
        return ok(result, message)
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/meeting-minutes/{id}/workflow",
    operation_id="gpt_meeting_minute_workflow",
    summary="Send, finalize, or cancel a meeting minute",
)
def gpt_meeting_minute_workflow(
    id: str,
    body: GptMeetingMinuteWorkflowBody,
    request: Request,
):
    try:
        return ok(
            _dispatch.meeting_minute_workflow(
                request,
                id,
                action=body.action,
                reason=body.reason,
            ),
            "Workflow de ata executado.",
        )
    except Exception as exc:
        return _handle(exc)
