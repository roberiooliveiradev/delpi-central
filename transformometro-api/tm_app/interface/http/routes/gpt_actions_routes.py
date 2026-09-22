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
from tm_app.application.gpt_actions.governed_actions_facade import GovernedActionsFacade
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)
from tm_app.application.governed_writes.errors import GovernedWriteError
from tm_app.application.governed_writes.orchestrator import (
    MEETING_MANAGE_NON_ACT,
    GovernedWriteOrchestrator,
)
from tm_app.application.gpt_actions.process_context_service import ProcessContextService
from tm_app.application.gpt_actions.user_context_service import (
    AuthenticatedUserContext,
    UserContextService,
)
from tm_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    resolve_gpt_actions_server_url,
)
from tm_app.config import settings
from tm_app.core.auth_actor import actor_from_request
from tm_app.core.errors import public_error_parts
from tm_app.core.responses import fail, ok
from tm_app.infrastructure.gateways.core_person_profile_gateway import (
    CorePersonProfileGateway,
)

router = APIRouter(
    prefix="/transformometro/gpt-actions/v1",
    tags=["Transformômetro GPT Actions"],
)
logger = logging.getLogger(__name__)
_dispatch = GptActionsDispatchService()
_packages = GuidedImprovementPackageService(_dispatch)
_orchestrator = GovernedWriteOrchestrator(_dispatch, _packages)
_governed = GovernedActionsFacade(_orchestrator, _dispatch)
_process_context = ProcessContextService()
_user_context = UserContextService(
    person_profile_reader=CorePersonProfileGateway()
)

# LEGACY_TRANSITIONAL: still mounted for migration, excluded from Builder OpenAPI.
LEGACY_DIRECT_WRITE_OPERATION_IDS = frozenset(
    {
        "gpt_create_record",
        "gpt_update_record",
        "gpt_delete_record",
        "gpt_duplicate_record",
        "gpt_commit_improvement_package",
    }
)


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
    if isinstance(exc, GovernedWriteError):
        payload = dict(exc.data or {})
        payload.setdefault("error_code", exc.code)
        # Custom GPT disables Actions on opaque HTTP 404 — map to 400.
        status = 400 if exc.status_code == 404 else exc.status_code
        if exc.status_code == 404:
            payload.setdefault("not_found", True)
        return fail(exc.message, status, data=payload)
    if isinstance(exc, GptActionsError):
        status = 400 if exc.status_code == 404 else exc.status_code
        data = dict(exc.data or {})
        if exc.status_code == 404:
            data.setdefault("not_found", True)
        return fail(exc.message, status, data=data)
    status, message, data = public_error_parts(exc)
    if status >= 500 and data.get("error_kind") == "internal":
        logger.exception("gpt_actions_unhandled")
    elif isinstance(exc, KeyError):
        logger.exception("gpt_actions_key_error")
    return fail(message, status, data)


class GptPrepareRecordChangeBody(BaseModel):
    entity: str
    operation: str = Field(
        ...,
        description="create | update | delete | duplicate (entity must allow it).",
    )
    record_id: str | None = None
    changes: dict = Field(default_factory=dict)


class GptCommitProposalBody(BaseModel):
    proposal_handle: str
    confirmation: bool = False


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
    "/me",
    operation_id="gpt_get_my_context",
    summary="Minimal personal context for the authenticated user",
)
def gpt_get_my_context(request: Request):
    try:
        if getattr(request.state, "user", None) is None:
            return fail("Usuário não autenticado.", 401, {"error_kind": "authn"})
        authorization = str(request.headers.get("Authorization") or "").strip()
        if not authorization:
            return fail("Usuário não autenticado.", 401, {"error_kind": "authn"})
        _user_id, email, display_name = actor_from_request(request)
        return ok(
            _user_context.get_my_context(
                AuthenticatedUserContext(
                    display_name=display_name,
                    email=email,
                    authorization=authorization,
                )
            ),
            "Contexto pessoal do usuário autenticado.",
        )
    except Exception as exc:
        return _handle(exc)


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
    "/methodology-guide",
    operation_id="gpt_get_methodology_guide",
    summary="Read-only process methodology playbooks",
)
def gpt_get_methodology_guide(
    request: Request,
    method: str | None = Query(default=None, description="Optional methodology method id"),
    task: str | None = Query(default=None, description="Optional methodology task id"),
):
    try:
        data = _dispatch.get_methodology_guide(request, method=method, task=task)
        return ok(data, "Guia metodológico do TÉO (não é fato nem autorização).")
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
    "/records/prepare-change",
    operation_id="gpt_prepare_record_change",
    summary="PREPARE governed entity create/update/delete/duplicate (no write)",
)
def gpt_prepare_record_change(body: GptPrepareRecordChangeBody, request: Request):
    try:
        data = _governed.prepare_record_change(
            request,
            entity=body.entity,
            operation=body.operation,
            record_id=body.record_id,
            changes=body.changes,
        )
        return ok(data, "Proposal ready — show to user, then gpt_commit_proposal.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/proposals/commit",
    operation_id="gpt_commit_proposal",
    summary="COMMIT opaque proposal_handle after explicit confirmation",
)
def gpt_commit_proposal(body: GptCommitProposalBody, request: Request):
    try:
        data = _governed.commit_proposal(
            request,
            proposal_handle=body.proposal_handle,
            confirmation=body.confirmation,
        )
        return ok(data, "Proposal committed and verified.")
    except Exception as exc:
        return _handle(exc)


# --- LEGACY_TRANSITIONAL direct writes (excluded from Builder OpenAPI) --------


@router.post(
    "/records/{entity}",
    operation_id="gpt_create_record",
    summary="[LEGACY] Direct create — use prepare_record_change",
    include_in_schema=False,
)
def gpt_create_record(entity: str, body: GptRecordBody, request: Request):
    try:
        data = _governed.prepare_record_change(
            request,
            entity=entity,
            operation="create",
            changes=body.data,
        )
        return ok(
            data,
            "LEGACY: returned PREPARE proposal. Confirm then gpt_commit_proposal. "
            "Direct create removed from Builder surface.",
        )
    except Exception as exc:
        return _handle(exc)


@router.put(
    "/records/{entity}/{id}",
    operation_id="gpt_update_record",
    summary="[LEGACY] Direct update — use prepare_record_change",
    include_in_schema=False,
)
def gpt_update_record(entity: str, id: str, body: GptRecordBody, request: Request):
    try:
        data = _governed.prepare_record_change(
            request,
            entity=entity,
            operation="update",
            record_id=id,
            changes=body.data,
        )
        return ok(
            data,
            "LEGACY: returned PREPARE proposal. Confirm then gpt_commit_proposal.",
        )
    except Exception as exc:
        return _handle(exc)


@router.delete(
    "/records/{entity}/{id}",
    operation_id="gpt_delete_record",
    summary="[LEGACY] Direct delete — use prepare_record_change",
    include_in_schema=False,
)
def gpt_delete_record(entity: str, id: str, request: Request):
    try:
        data = _governed.prepare_record_change(
            request,
            entity=entity,
            operation="delete",
            record_id=id,
            changes={},
        )
        return ok(
            data,
            "LEGACY: returned PREPARE proposal. Confirm then gpt_commit_proposal.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/records/{entity}/{id}/duplicate",
    operation_id="gpt_duplicate_record",
    summary="[LEGACY] Direct duplicate — use prepare_record_change",
    include_in_schema=False,
)
def gpt_duplicate_record(
    entity: str,
    id: str,
    request: Request,
    body: GptRecordBody | None = None,
):
    try:
        data = _governed.prepare_record_change(
            request,
            entity=entity,
            operation="duplicate",
            record_id=id,
            changes=(body.data if body else {}),
        )
        return ok(
            data,
            "LEGACY: returned PREPARE proposal. Confirm then gpt_commit_proposal.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/revisions/{id}/activate",
    operation_id="gpt_activate_revision",
    summary="PREPARE revision activation (commit via gpt_commit_proposal)",
)
def gpt_activate_revision(id: str, request: Request):
    try:
        data = _governed.prepare_capability(
            request,
            capability="activate_revision",
            args={"id": id},
            operation_label="prepare_activate_revision",
        )
        return ok(data, "Activation proposal ready — then gpt_commit_proposal.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/dashboard/recalculate",
    operation_id="gpt_recalculate_dashboard",
    summary="PREPARE dashboard recalculation (commit via gpt_commit_proposal)",
)
def gpt_recalculate_dashboard(
    request: Request,
    body: GptRecalculateBody | None = None,
):
    try:
        payload = body.model_dump() if body else {}
        data = _governed.prepare_capability(
            request,
            capability="recalculate_dashboard",
            args=payload,
            operation_label="prepare_recalculate_dashboard",
        )
        return ok(data, "Recalculate proposal ready — then gpt_commit_proposal.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/meeting-minutes/{id}/workflow",
    operation_id="gpt_meeting_minute_workflow",
    summary="PREPARE meeting-minute workflow (commit via gpt_commit_proposal)",
)
def gpt_meeting_minute_workflow(
    id: str,
    body: GptMeetingMinuteWorkflowBody,
    request: Request,
):
    try:
        data = _governed.prepare_capability(
            request,
            capability="meeting_minute_workflow",
            args={"id": id, "action": body.action, "reason": body.reason},
            operation_label="prepare_meeting_minute_workflow",
        )
        return ok(data, "Workflow proposal ready — then gpt_commit_proposal.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/improvement-packages/validate",
    operation_id="gpt_validate_improvement_package",
    summary="PREPARE improvement package (proposal_handle when ready)",
)
def gpt_validate_improvement_package(
    body: GptValidateImprovementPackageBody, request: Request
):
    try:
        data = _governed.prepare_capability(
            request,
            capability="commit_improvement_package",
            args=body.model_dump(),
            operation_label="prepare_improvement_package",
        )
        ready = bool((data.get("proposal") or {}).get("ready", True))
        message = (
            "Package proposal ready — confirm then gpt_commit_proposal."
            if ready
            else "Package incomplete — see validation_result; ACT not allowed."
        )
        return ok(data, message)
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/improvement-packages",
    operation_id="gpt_commit_improvement_package",
    summary="[LEGACY] Prefer gpt_commit_proposal with package proposal_handle",
    include_in_schema=False,
)
def gpt_commit_improvement_package(body: GptImprovementPackageBody, request: Request):
    """LEGACY: if proposal_handle present in body, commit; else prepare only."""
    try:
        raw = body.model_dump()
        handle = str(raw.pop("proposal_handle", "") or "").strip()
        if handle:
            data = _governed.commit_proposal(
                request,
                proposal_handle=handle,
                confirmation=bool(raw.get("confirmation", True)),
            )
            return ok(data, "LEGACY package commit via proposal_handle.")
        data = _governed.prepare_capability(
            request,
            capability="commit_improvement_package",
            args=raw,
            operation_label="prepare_improvement_package",
        )
        return ok(
            data,
            "LEGACY: returned PREPARE proposal. Confirm then gpt_commit_proposal.",
        )
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
    summary="PREPARE evidence link/description/delete (commit via gpt_commit_proposal)",
)
def gpt_manage_evidence(request: Request, body: GptEvidenceManageBody):
    try:
        data = _governed.prepare_capability(
            request,
            capability="manage_evidence",
            args=body.model_dump(),
            operation_label="prepare_manage_evidence",
        )
        return ok(data, "Evidence proposal ready — then gpt_commit_proposal.")
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
    summary="PREPARE shared-resource cost adjustment (commit via gpt_commit_proposal)",
)
def gpt_adjust_shared_resource_cost(
    request: Request, body: GptAdjustSharedResourceCostBody
):
    try:
        data = _governed.prepare_capability(
            request,
            capability="adjust_shared_resource_cost",
            args=body.model_dump(),
            operation_label="prepare_adjust_shared_resource_cost",
        )
        return ok(data, "Cost adjustment proposal ready — then gpt_commit_proposal.")
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/meeting-minutes/manage",
    operation_id="gpt_meeting_minute_manage",
    summary="Meeting-minute extras: READ immediate; WRITE returns PREPARE proposal",
)
def gpt_meeting_minute_manage(request: Request, body: GptMeetingMinuteManageBody):
    try:
        action = str(body.action or "").strip()
        if action in MEETING_MANAGE_NON_ACT:
            return ok(
                _dispatch.manage_meeting_minute(
                    request,
                    action=body.action,
                    minute_id=body.minute_id,
                    payload=body.data,
                ),
                "Meeting-minute read/analysis.",
            )
        data = _governed.prepare_capability(
            request,
            capability="meeting_minute_manage",
            args={
                "action": body.action,
                "minute_id": body.minute_id,
                "data": body.data,
            },
            operation_label="prepare_meeting_minute_manage",
        )
        return ok(data, "Meeting-minute write proposal ready — then gpt_commit_proposal.")
    except Exception as exc:
        return _handle(exc)
