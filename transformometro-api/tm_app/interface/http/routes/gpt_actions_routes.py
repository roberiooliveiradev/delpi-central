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
    COLLABORATION_ACTION_TO_CAPABILITY,
    COLLABORATION_READ_ACTIONS,
    GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
    MEETING_MINUTE_ACTION_TO_CAPABILITY,
    MEETING_MINUTE_READ_ACTIONS,
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
from tm_app.infrastructure.diagnostic_composition import (
    build_diagnostic_write_stack,
)
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
_orchestrator = GovernedWriteOrchestrator(
    _dispatch,
    _packages,
    diagnostic_stack=build_diagnostic_write_stack(),
)
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

# Evidence change actions — map 1:1 onto the canonical manage_evidence
# ``operation`` vocabulary (binary transfer stays platform_blocked).
_EVIDENCE_CHANGE_ACTIONS = frozenset(
    {"create_link", "update_description", "delete"}
)


class GptRecordBody(BaseModel):
    data: dict = Field(default_factory=dict)


class GptGovernedOperationBody(BaseModel):
    """Unified special governed operations — action selects capability."""

    action: str = Field(
        ...,
        description=(
            "activate_revision | recalculate_dashboard | "
            "commit_improvement_package | adjust_shared_resource_cost | "
            "update_signature_profile | import_diagram_bpmn_xml"
        ),
    )
    id: str | None = None
    revisao_id: str | None = None
    processo_id: str | None = None
    competencia_inicio: str | None = None
    competencia_fim: str | None = None
    recurso_compartilhado_id: str | None = None
    valor_mensal: float | None = None
    vigente_desde: str | None = None
    observacoes: str | None = None
    process: dict | None = None
    instance: dict | None = None
    baseline: dict | None = None
    scenario: dict | None = None
    activate_scenario: bool = False
    recalculate: bool = False
    display_name: str | None = None
    xml: str | None = None
    commit_now: bool = False
    confirmation: bool = False
    idempotency_key: str | None = None


class GptEvidenceChangeBody(BaseModel):
    action: str = Field(
        ..., description="create_link | update_description | delete"
    )
    scope: str
    parent_id: str
    evidence_id: str | None = None
    url_externa: str | None = None
    descricao: str | None = None
    confirm_delete: bool = False
    commit_now: bool = False
    confirmation: bool = False
    idempotency_key: str | None = None


class GptMeetingMinuteReadBody(BaseModel):
    action: str = Field(
        ...,
        description=(
            "pending_signatures | audit | versions | participants | "
            "signers | generate_from_transcript"
        ),
    )
    minute_id: str | None = None
    data: dict = Field(default_factory=dict)


class GptMeetingMinuteChangeBody(BaseModel):
    action: str = Field(
        ...,
        description=(
            "send | finalize | cancel | refuse | resend | create_version | "
            "set_participants | set_signers (reason required for refuse)"
        ),
    )
    minute_id: str | None = None
    reason: str | None = None
    data: dict = Field(default_factory=dict)
    commit_now: bool = False
    confirmation: bool = False
    idempotency_key: str | None = None


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
    commit_now: bool = False
    confirmation: bool = False
    idempotency_key: str | None = None


class GptCommitProposalBody(BaseModel):
    proposal_handle: str
    confirmation: bool = False


class GptCollaborationChangeBody(BaseModel):
    action: str = Field(
        ...,
        description=(
            "create_task | update_task | complete_task | cancel_task | "
            "open_room | post_message | edit_message | delete_message | "
            "toggle_reaction | pin_message | unpin_message | mark_room_read"
        ),
    )
    task_id: str | None = None
    title: str | None = None
    description: str | None = None
    assignee_user_id: str | None = None
    due_date: str | None = None
    source_interaction_message_id: str | None = None
    processo_id: str | None = None
    room_id: str | None = None
    message_id: str | None = None
    content: str | None = None
    parent_id: str | None = None
    mentions: list | None = None
    reaction: str | None = None
    commit_now: bool = False
    confirmation: bool = False
    idempotency_key: str | None = None


def _idempotency_key_from_request(request: Request, body_key: str | None) -> str | None:
    header = str(request.headers.get("Idempotency-Key") or "").strip()
    if header:
        return header
    return str(body_key or "").strip() or None


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
        data = _user_context.get_my_context(
            AuthenticatedUserContext(
                display_name=display_name,
                email=email,
                authorization=authorization,
            )
        )
        data["signature_profile"] = _dispatch.my_signature_profile_or_none(
            request.state.user
        )
        return ok(data, "Contexto pessoal do usuário autenticado.")
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
    summary="Analyze dashboard KPIs and process/revision compute views",
)
def gpt_analyze(
    request: Request,
    view: str = Query(
        ...,
        description=(
            "meta|summary|processes|instances|rows|dashboard_summary_live|"
            "dashboard_process_ranking|dashboard_alerts|dashboard_evolution|"
            "dashboard_by_family|dashboard_due_dates|"
            "dashboard_strategic_indicators|processes_calculated|"
            "process_revision_comparison|impact_effort_matrix|"
            "decomposition_link_validation|decomposition_draft_suggestion|"
            "diagram_validation|diagram_bpmn_xml|"
            "revision_allocation_diagnostic|revision_diagram_merged|"
            "revision_decomposition_merged"
        ),
    ),
    filial_id: str | None = None,
    setor_id: str | None = None,
    processo_id: str | None = None,
    revisao_id: str | None = None,
    instancia_id: str | None = None,
    familia_processo: str | None = None,
    competencia: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    horizonte_meses: int | None = Query(default=None, ge=1, le=120),
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
            instancia_id=instancia_id,
            familia_processo=familia_processo,
            competencia=competencia,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
            horizonte_meses=horizonte_meses,
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
        parsed = parse_entity(entity)
        from tm_app.application.gpt_actions.capability_descriptors import (
            ENTITY_FILTERABLE_FIELDS,
        )

        filters = {
            "parent_id": parent_id,
            "instance_id": instance_id,
            "filial_id": filial_id,
            "setor_id": setor_id,
            "status": status,
            "familia_processo": familia_processo,
            "q": q,
            "unit_code": unit_code,
        }
        allowed = ENTITY_FILTERABLE_FIELDS.get(parsed.value, frozenset())
        provided = {
            key
            for key, value in filters.items()
            if value is not None and str(value).strip() != ""
        }
        bad = sorted(provided - allowed)
        if bad:
            raise GptActionsError(
                f"Disallowed filters for entity '{parsed.value}': {', '.join(bad)}.",
                400,
                data={"error_code": "INVALID_FIELD", "fields": bad},
            )
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
        from tm_app.application.gpt_actions.response_compact import project_get_record

        return ok(
            project_get_record(_dispatch.get_record(request, entity, id)),
            "Registro.",
        )
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
            commit_now=bool(body.commit_now),
            confirmation=bool(body.confirmation),
            idempotency_key=_idempotency_key_from_request(
                request, body.idempotency_key
            ),
        )
        if data.get("persisted"):
            return ok(data, "Change persisted and verified (commit_now).")
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
    "/governed-operations/prepare",
    operation_id="gpt_prepare_governed_operation",
    summary=(
        "PREPARE special governed operations — revision activation, "
        "dashboard recalculation, improvement package, shared-resource cost "
        "(commit via gpt_commit_proposal)"
    ),
)
def gpt_prepare_governed_operation(
    request: Request, body: GptGovernedOperationBody
):
    try:
        action_norm = str(body.action or "").strip().lower()
        capability = GOVERNED_OPERATION_ACTION_TO_CAPABILITY.get(action_norm)
        if capability is None:
            return fail(
                "Invalid governed-operation action. Allowed: "
                f"{sorted(GOVERNED_OPERATION_ACTION_TO_CAPABILITY)}.",
                400,
            )
        args = body.model_dump(
            exclude={"action", "commit_now", "confirmation", "idempotency_key"}
        )
        args["action"] = action_norm
        data = _governed.prepare_capability(
            request,
            capability=capability,
            args=args,
            operation_label="prepare_governed_operation",
            commit_now=bool(body.commit_now),
            confirmation=bool(body.confirmation),
            idempotency_key=_idempotency_key_from_request(
                request, body.idempotency_key
            ),
        )
        if data.get("persisted"):
            return ok(data, "Operation persisted and verified (commit_now).")
        ready = bool((data.get("proposal") or {}).get("ready", True))
        message = (
            "Operation proposal ready — confirm then gpt_commit_proposal."
            if ready
            else "Operation incomplete — see validation_result; ACT not allowed."
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
    operation_id="gpt_evidence_read",
    summary="READ evidence family (list process or revision evidence metadata)",
)
def gpt_evidence_read(
    request: Request,
    action: str = Query("list", description="list"),
    scope: str = Query(..., description="process|revision"),
    parent_id: str = Query(
        ..., description="processo_id when scope=process; revisao_id when scope=revision"
    ),
):
    try:
        action_norm = str(action or "").strip().lower()
        if action_norm != "list":
            return fail("Invalid evidence_read action. Allowed: ['list'].", 400)
        return ok(
            _dispatch.list_evidence(request, scope=scope, parent_id=parent_id),
            "Evidências listadas.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/evidence/prepare",
    operation_id="gpt_prepare_evidence_change",
    summary="PREPARE evidence link/description/delete (commit via gpt_commit_proposal)",
)
def gpt_prepare_evidence_change(request: Request, body: GptEvidenceChangeBody):
    try:
        action_norm = str(body.action or "").strip().lower()
        if action_norm not in _EVIDENCE_CHANGE_ACTIONS:
            return fail(
                "Invalid evidence action. Allowed: "
                f"{sorted(_EVIDENCE_CHANGE_ACTIONS)}.",
                400,
            )
        args = body.model_dump(
            exclude={"action", "commit_now", "confirmation", "idempotency_key"}
        )
        args["operation"] = action_norm
        data = _governed.prepare_capability(
            request,
            capability="manage_evidence",
            args=args,
            operation_label="prepare_evidence_change",
            commit_now=bool(body.commit_now),
            confirmation=bool(body.confirmation),
            idempotency_key=_idempotency_key_from_request(
                request, body.idempotency_key
            ),
        )
        if data.get("persisted"):
            return ok(data, "Evidence write persisted (commit_now).")
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
    "/meeting-minutes/read",
    operation_id="gpt_meeting_minute_read",
    summary="READ meeting-minute family (signatures|audit|versions|participants|signers|generate_from_transcript)",
)
def gpt_meeting_minute_read(request: Request, body: GptMeetingMinuteReadBody):
    try:
        action_norm = str(body.action or "").strip().lower()
        if action_norm not in MEETING_MINUTE_READ_ACTIONS:
            return fail(
                "Invalid meeting_minute_read action. Allowed: "
                f"{sorted(MEETING_MINUTE_READ_ACTIONS)}.",
                400,
            )
        return ok(
            _dispatch.manage_meeting_minute(
                request,
                action=action_norm,
                minute_id=body.minute_id,
                payload=body.data,
                read_only=True,
            ),
            "Meeting-minute read/analysis.",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/meeting-minutes/prepare",
    operation_id="gpt_prepare_meeting_minute_change",
    summary=(
        "PREPARE meeting-minute change — workflow transitions + manage "
        "writes (commit via gpt_commit_proposal)"
    ),
)
def gpt_prepare_meeting_minute_change(
    request: Request, body: GptMeetingMinuteChangeBody
):
    try:
        action_norm = str(body.action or "").strip().lower()
        capability = MEETING_MINUTE_ACTION_TO_CAPABILITY.get(action_norm)
        if capability is None:
            return fail(
                "Invalid meeting-minute action. Allowed: "
                f"{sorted(MEETING_MINUTE_ACTION_TO_CAPABILITY)}.",
                400,
            )
        if capability == "meeting_minute_workflow":
            args = {
                "id": body.minute_id,
                "action": action_norm,
                "reason": body.reason,
            }
        else:
            args = {
                "action": action_norm,
                "minute_id": body.minute_id,
                "data": body.data,
            }
        data = _governed.prepare_capability(
            request,
            capability=capability,
            args=args,
            operation_label="prepare_meeting_minute_change",
            commit_now=bool(body.commit_now),
            confirmation=bool(body.confirmation),
            idempotency_key=_idempotency_key_from_request(
                request, body.idempotency_key
            ),
        )
        if data.get("persisted"):
            return ok(data, "Meeting-minute write persisted (commit_now).")
        return ok(
            data, "Meeting-minute proposal ready — then gpt_commit_proposal."
        )
    except Exception as exc:
        return _handle(exc)


@router.get(
    "/collaboration",
    operation_id="gpt_collaboration_read",
    summary=(
        "READ collaboration family — tasks (my_tasks|task|process_tasks) "
        "and interaction rooms (rooms|room|messages|attachments metadata)"
    ),
)
def gpt_collaboration_read(
    request: Request,
    action: str = Query(
        ...,
        description=(
            "my_tasks | task | process_tasks | rooms | room | "
            "messages | attachments"
        ),
    ),
    task_id: str | None = Query(None),
    processo_id: str | None = Query(None),
    status: str = Query("pending"),
    room_id: str | None = Query(None),
    inbox_filter: str = Query("all"),
    limit: int = Query(50),
    before_id: str | None = Query(None),
):
    try:
        action_norm = str(action or "").strip().lower()
        if action_norm not in COLLABORATION_READ_ACTIONS:
            return fail(
                "Invalid collaboration_read action. Allowed: "
                f"{sorted(COLLABORATION_READ_ACTIONS)}.",
                400,
            )
        if action_norm == "my_tasks":
            return ok(
                _dispatch.list_my_tasks(request, status=status),
                "Tarefas do usuário autenticado.",
            )
        if action_norm == "process_tasks":
            if not str(processo_id or "").strip():
                return fail(
                    "processo_id is required for action 'process_tasks'.", 400
                )
            return ok(
                _dispatch.list_process_tasks(request, str(processo_id)),
                "Tarefas relacionadas ao processo.",
            )
        if action_norm == "task":
            if not str(task_id or "").strip():
                return fail("task_id is required for action 'task'.", 400)
            return ok(
                _dispatch.get_task(request, str(task_id)), "Tarefa carregada."
            )
        if action_norm == "rooms":
            return ok(
                _dispatch.list_rooms(request, inbox_filter=inbox_filter),
                "Salas de interação.",
            )
        if not str(room_id or "").strip():
            return fail(
                f"room_id is required for action '{action_norm}'.", 400
            )
        if action_norm == "room":
            return ok(_dispatch.get_room(request, str(room_id)), "Sala carregada.")
        if action_norm == "messages":
            return ok(
                _dispatch.list_room_messages(
                    request, str(room_id), limit=limit, before_id=before_id
                ),
                "Mensagens da sala.",
            )
        return ok(
            _dispatch.list_room_attachments(request, str(room_id)),
            "Metadados de anexos (binary transfer not on this surface).",
        )
    except Exception as exc:
        return _handle(exc)


@router.post(
    "/collaboration/prepare",
    operation_id="gpt_prepare_collaboration_change",
    summary=(
        "PREPARE collaboration change — task and room/message writes "
        "(commit via gpt_commit_proposal); execution_policy per action"
    ),
)
def gpt_prepare_collaboration_change(
    request: Request, body: GptCollaborationChangeBody
):
    try:
        action_norm = str(body.action or "").strip().lower()
        capability = COLLABORATION_ACTION_TO_CAPABILITY.get(action_norm)
        if capability is None:
            return fail(
                "Invalid collaboration action. Allowed: "
                f"{sorted(COLLABORATION_ACTION_TO_CAPABILITY)}.",
                400,
            )
        args = body.model_dump(
            exclude={"commit_now", "confirmation", "idempotency_key"}
        )
        args["action"] = action_norm
        data = _governed.prepare_capability(
            request,
            capability=capability,
            args=args,
            operation_label="prepare_collaboration_change",
            commit_now=bool(body.commit_now),
            confirmation=bool(body.confirmation),
            idempotency_key=_idempotency_key_from_request(
                request, body.idempotency_key
            ),
        )
        if data.get("persisted"):
            return ok(data, "Collaboration write persisted (commit_now).")
        return ok(
            data, "Collaboration proposal ready — then gpt_commit_proposal."
        )
    except Exception as exc:
        return _handle(exc)
