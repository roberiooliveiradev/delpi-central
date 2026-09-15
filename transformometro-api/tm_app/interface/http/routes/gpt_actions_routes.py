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
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)
from tm_app.application.gpt_actions.process_context_service import ProcessContextService
from tm_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    resolve_gpt_actions_server_url,
)
from tm_app.config import settings
from tm_app.core.errors import public_error_parts
from tm_app.core.responses import fail, ok

router = APIRouter(
    prefix="/transformometro/gpt-actions/v1",
    tags=["Transformômetro GPT Actions"],
)
logger = logging.getLogger(__name__)
_dispatch = GptActionsDispatchService()
_packages = GuidedImprovementPackageService(_dispatch)
_process_context = ProcessContextService()


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


class GptEvidenceManageBody(BaseModel):
    scope: str
    operation: str
    parent_id: str
    evidence_id: str | None = None
    url_externa: str | None = None
    descricao: str | None = None
    confirm_delete: bool = False


class GptAdjustSharedResourceCostBody(BaseModel):
    recurso_compartilhado_id: str
    valor_mensal: float
    vigente_desde: str
    observacoes: str | None = None


class GptMeetingMinuteManageBody(BaseModel):
    action: str
    minute_id: str | None = None
    data: dict = Field(default_factory=dict)


class GptImprovementPackageBody(BaseModel):
    """Runtime body stays loosely typed on purpose.

    Incomplete packages must reach GuidedImprovementPackageService so dry_run
    returns HTTP 200 + ready=false + missing[]. Nested Pydantic models would
    risk 422 before that checklist. Canonical nesting is projected via OpenAPI
    + registration_guide.package_hints (improvement_package_contract).
    """

    dry_run: bool = False
    activate_scenario: bool = False
    recalculate: bool = False
    process: dict = Field(default_factory=dict)
    instance: dict = Field(default_factory=dict)
    baseline: dict | None = None
    scenario: dict | None = None


class GptValidateImprovementPackageBody(BaseModel):
    """No-write package body. Write flags are not part of this contract.

    Extra keys (dry_run/activate_scenario/recalculate) are ignored.
    The route calls GuidedImprovementPackageService.validate only.
    """

    model_config = {"extra": "ignore"}

    process: dict = Field(default_factory=dict)
    instance: dict = Field(default_factory=dict)
    baseline: dict | None = None
    scenario: dict | None = None


def _handle(exc: Exception):
    status, message, data = public_error_parts(exc)
    if status >= 500 and data.get("error_kind") == "internal":
        logger.exception("gpt_actions_unhandled")
    elif isinstance(exc, KeyError):
        logger.exception("gpt_actions_key_error")
    return fail(message, status, data)


@router.get(
    "/openapi.json",
    operation_id="gpt_get_openapi_schema",
    summary="Public OpenAPI schema for Custom GPT import",
)
def gpt_get_openapi_schema():
    return build_gpt_actions_openapi(
        server_url=resolve_gpt_actions_server_url(
            public_base_url=settings.PUBLIC_BASE_URL,
            root_path=settings.TM_API_ROOT_PATH,
        )
    )


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
    "/process-context",
    operation_id="gpt_get_process_context",
    summary="Aggregated read-only process intelligence context",
)
def gpt_get_process_context(
    request: Request,
    process_id: str = Query(..., description="Master process UUID"),
    instance_id: str | None = None,
    revision_id: str | None = None,
):
    try:
        data = _process_context.get_context(
            request,
            process_id=process_id,
            instance_id=instance_id,
            revision_id=revision_id,
        )
        return ok(data, "Contexto de inteligência do processo.")
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
    instance_id: str | None = None,
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
            instance_id=instance_id,
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


@router.post(
    "/improvement-packages/validate",
    operation_id="gpt_validate_improvement_package",
    summary="Validate a guided improvement package without writing",
)
def gpt_validate_improvement_package(
    body: GptValidateImprovementPackageBody, request: Request
):
    try:
        data = _packages.validate(request, body.model_dump())
        message = (
            "Pacote pronto para commit."
            if data.get("ready")
            else "Pacote incompleto — veja missing."
        )
        return ok(data, message)
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/improvement-packages",
    operation_id="gpt_commit_improvement_package",
    summary="Commit a guided improvement package",
)
def gpt_commit_improvement_package(body: GptImprovementPackageBody, request: Request):
    try:
        data = _packages.commit(request, body.model_dump())
        if body.dry_run:
            message = (
                "Pacote pronto para commit."
                if data.get("ready")
                else "Pacote incompleto — veja missing."
            )
        else:
            message = "Pacote de melhoria gravado."
        return ok(data, message)
    except GptActionsError as exc:
        # Custom GPT often disables consequential Actions after opaque 404s.
        # Keep "not found" semantics in the body, but answer with 400.
        if exc.status_code == 404:
            logger.warning(
                "gpt_commit_improvement_package_not_found_as_400 message=%s",
                exc.message,
            )
            data = dict(exc.data or {})
            data.setdefault("not_found", True)
            return fail(exc.message, 400, data)
        return _handle(exc)
    except LookupError as exc:
        # KeyError is a LookupError subclass — do not remap programming bugs as not_found.
        if isinstance(exc, KeyError):
            return _handle(exc)
        logger.warning(
            "gpt_commit_improvement_package_lookup_as_400 message=%s",
            exc,
        )
        return fail(str(exc), 400, {"not_found": True})
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/evidence",
    operation_id="gpt_list_evidence",
    summary="List process or revision evidence metadata",
)
def gpt_list_evidence(
    request: Request,
    scope: str = Query(..., description="process|revision"),
    parent_id: str = Query(
        ..., description="processo_id when scope=process; revisao_id when scope=revision"
    ),
):
    try:
        return ok(
            _dispatch.list_evidence(request, scope=scope, parent_id=parent_id),
            "Evidências listadas.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/evidence/manage",
    operation_id="gpt_manage_evidence",
    summary="Create external-link evidence, update description, or delete",
)
def gpt_manage_evidence(request: Request, body: GptEvidenceManageBody):
    try:
        data = _dispatch.manage_evidence(
            request,
            scope=body.scope,
            operation=body.operation,
            parent_id=body.parent_id,
            evidence_id=body.evidence_id,
            url_externa=body.url_externa,
            descricao=body.descricao,
            confirm_delete=body.confirm_delete,
        )
        status = 201 if body.operation == "create_link" else 200
        return ok(data, "Evidência atualizada.", status)
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/processes/{processo_id}/timeline",
    operation_id="gpt_get_process_timeline",
    summary="Read process audit timeline",
)
def gpt_get_process_timeline(
    processo_id: str,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
):
    try:
        return ok(
            _dispatch.get_process_timeline(
                request, processo_id=processo_id, page=page, page_size=page_size
            ),
            "Linha do tempo do processo.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/shared-resources/adjust-cost",
    operation_id="gpt_adjust_shared_resource_cost",
    summary="Register shared-resource cost adjustment",
)
def gpt_adjust_shared_resource_cost(
    request: Request, body: GptAdjustSharedResourceCostBody
):
    try:
        return ok(
            _dispatch.adjust_shared_resource_cost(
                request,
                recurso_compartilhado_id=body.recurso_compartilhado_id,
                valor_mensal=body.valor_mensal,
                vigente_desde=body.vigente_desde,
                observacoes=body.observacoes,
            ),
            "Reajuste de custo registrado.",
            201,
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/meeting-minutes/manage",
    operation_id="gpt_meeting_minute_manage",
    summary="Meeting-minute extras without duplicating workflow send/finalize/cancel",
)
def gpt_meeting_minute_manage(request: Request, body: GptMeetingMinuteManageBody):
    try:
        return ok(
            _dispatch.manage_meeting_minute(
                request,
                action=body.action,
                minute_id=body.minute_id,
                payload=body.data,
            ),
            "Operação de ata executada.",
        )
    except Exception as exc:
        return _handle(exc)

