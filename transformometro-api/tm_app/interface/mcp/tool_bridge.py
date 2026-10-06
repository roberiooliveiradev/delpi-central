"""Bridge MCP tools → governed writes + existing GPT Actions services.

Rebuilds a Starlette Request from delpi_auth context so AuthZ helpers that
read ``request.state.user`` keep working without duplicating RBAC.

Material writes: PREPARE → opaque proposal_handle → commit_proposal
(no model-trusted mutation; capability comes from the stored proposal).
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from fastapi.responses import JSONResponse
from mcp.types import CallToolResult
from starlette.requests import Request

from delpi_mcp.errors import kind_for_http_status, mcp_tool_result
from delpi_mcp.identity import (
    build_mcp_request as _shared_build_request,
    current_mcp_context,
    require_mcp_context,
)
from tm_app.application.governed_writes.confirmation_policy import AUTO_ACT
from tm_app.application.governed_writes.errors import (
    OUTCOME_VERIFICATION_FAILED,
    PREPARE_PERSISTED_STATE_VIOLATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    COLLABORATION_ACTION_TO_CAPABILITY,
    COLLABORATION_READ_ACTIONS,
    GOVERNED_OPERATION_ACTION_TO_CAPABILITY,
    INTERACTION_ROOM_ACTION_TO_CAPABILITY,
    MEETING_MANAGE_NON_ACT,
    MEETING_MANAGE_READ_ACTIONS,
    MEETING_MINUTE_ACTION_TO_CAPABILITY,
    MEETING_MINUTE_READ_ACTIONS,
    TASK_ACTION_TO_CAPABILITY,
    GovernedWriteOrchestrator,
)
from tm_app.application.governed_writes.diagnostic_capabilities import (
    MANAGE_ACTIONS,
    SERVER_GENERATED_ID_FIELD,
    require_prepare_authz,
)
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.governed_actions_facade import GovernedActionsFacade
from tm_app.application.gpt_actions.improvement_package_service import (
    GuidedImprovementPackageService,
)
from tm_app.application.gpt_actions.process_context_service import ProcessContextService
from tm_app.application.use_cases.diagnostic_read import (
    DiagnosticReadError,
    GetDiagnostic,
    ListDiagnosticsByRevision,
)
from tm_app.application.gpt_actions.user_context_service import (
    AuthenticatedUserContext,
    UserContextService,
)
from tm_app.infrastructure.diagnostic_composition import (
    build_diagnostic_write_stack,
)
from tm_app.infrastructure.gateways.core_person_profile_gateway import (
    CorePersonProfileGateway,
)
from tm_app.interface.diagnostic_projection import (
    project_read_context,
    project_revision,
    project_summary,
)
from tm_app.interface.mcp.constants import (
    ACT_TOOL_CAPABILITY,
    PREPARE_TOOL_CAPABILITY,
)
from tm_app.interface.mcp.oauth_contract import mcp_www_authenticate_meta

logger = logging.getLogger(__name__)

_dispatch = GptActionsDispatchService()
_packages = GuidedImprovementPackageService(_dispatch)
# One canonical Diagnostic composition shared by governed writes AND reads —
# no second repository/read authority for the MCP surface.
_diagnostic_stack = build_diagnostic_write_stack()
_orchestrator = GovernedWriteOrchestrator(
    _dispatch,
    _packages,
    diagnostic_stack=_diagnostic_stack,
)
_governed = GovernedActionsFacade(orchestrator=_orchestrator, dispatch=_dispatch)
_process_context = ProcessContextService()
_user_context = UserContextService(person_profile_reader=CorePersonProfileGateway())

_ERROR_KIND_BY_CODE = {
    "unauthenticated": "unauthenticated",
    "forbidden": "forbidden",
    "validation": "validation",
    "not_found": "not_found",
    "conflict": "conflict",
    "business_rule": "business_rule",
    "proposal_required": "proposal_required",
    "proposal_not_found": "proposal_not_found",
    "proposal_expired": "proposal_expired",
    "proposal_stale": "proposal_stale",
    "proposal_mismatch": "proposal_mismatch",
    "proposal_actor_mismatch": "proposal_actor_mismatch",
    "outcome_verification_failed": "outcome_verification_failed",
    "internal": "internal",
}


def build_mcp_request() -> Request:
    """Rebuild the adapter Request from the delpi_auth-established context.

    S4: context snapshot + scope reconstruction delegated to
    delpi_mcp.identity; missing user fails closed with the same
    PermissionError("Unauthorized") the error adapter maps to 401.
    """
    context = require_mcp_context()
    return _shared_build_request(
        context=context,
        server=("transformometro-api", 443),
        client=("127.0.0.1", 0),
    )


def _ok_result(data: Any, message: str = "ok") -> CallToolResult:
    payload = {"success": True, "message": message, "data": data}
    return mcp_tool_result(payload, is_error=False)


def _error_result(
    message: str,
    *,
    status_code: int = 400,
    data: dict | None = None,
    error_code: str | None = None,
) -> CallToolResult:
    err_data = dict(data or {})
    if error_code:
        err_data.setdefault("error_code", error_code)
        err_data.setdefault("error_kind", _ERROR_KIND_BY_CODE.get(error_code, error_code))
    elif "error_kind" not in err_data:
        err_data["error_kind"] = "client"
    payload = {
        "success": False,
        "message": message,
        "data": err_data,
        "status_code": status_code,
    }
    meta = None
    if status_code == 401:
        meta = mcp_www_authenticate_meta(
            error="invalid_token",
            error_description="Authentication required",
        )
    return mcp_tool_result(payload, is_error=True, meta=meta)


def handle_tool_error(exc: Exception) -> CallToolResult:
    if isinstance(exc, PermissionError):
        msg = str(exc) or "Unauthorized"
        if msg == "Unauthorized":
            return _error_result(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        return _error_result(
            "Forbidden", status_code=403, error_code="forbidden", data={"error_kind": "authz"}
        )
    if isinstance(exc, DiagnosticReadError):
        # Canonical read-use-case errors: preserve semantic code, map to a
        # governed-stable kind. Never fall through to generic LookupError.
        status = 400
        if exc.code in (
            "diagnostic.not_found",
            "diagnostic.revision_not_found",
        ):
            status = 404
        elif exc.code == "diagnostic.read_integrity_error":
            status = 409
        return _error_result(
            str(exc),
            status_code=status,
            error_code="not_found" if status == 404 else ("conflict" if status == 409 else "validation"),
            data={"error_code": exc.code},
        )
    if isinstance(exc, GovernedWriteError):
        return _error_result(
            exc.message,
            status_code=exc.status_code,
            data=dict(exc.data or {}),
            error_code=exc.code,
        )
    if isinstance(exc, GptActionsError):
        code = kind_for_http_status(exc.status_code, server_error="validation")
        return _error_result(
            exc.message,
            status_code=exc.status_code,
            data=dict(exc.data or {}) or {"error_kind": "client"},
            error_code=code,
        )
    if isinstance(exc, (ValueError, LookupError)) and not isinstance(exc, KeyError):
        return _error_result(
            str(exc), status_code=400, error_code="validation", data={"error_kind": "validation"}
        )
    if isinstance(exc, JSONResponse):
        return _error_result(
            "Acesso negado.", status_code=403, error_code="forbidden", data={"error_kind": "authz"}
        )
    logger.exception("teo_mcp_tool_unhandled")
    return _error_result(
        "Erro interno do servidor.",
        status_code=500,
        error_code="internal",
        data={"error_kind": "internal", "error_type": type(exc).__name__},
    )


def _prepared_message(data: dict[str, Any]) -> str:
    """Policy-aware PREPARE response copy (payload remains authoritative)."""
    prop = data.get("proposal") if isinstance(data.get("proposal"), dict) else {}
    if prop and not prop.get("act_allowed", True):
        return "Proposal prepared but not ready for commit (see validation_result)."
    if prop.get("execution_policy") == AUTO_ACT:
        return (
            "Governed auto_act proposal prepared. Proceed with "
            "commit_proposal — no additional user confirmation required."
        )
    return (
        "Governed destructive proposal prepared. One explicit user "
        "confirmation is required before commit_proposal."
    )


def _prepare(capability: str, args: dict[str, Any]) -> CallToolResult:
    """Pure MCP PREPARE — never invokes ACT.

    ``commit_now``/``confirmation``/``idempotency_key`` belong to the
    GPT Actions HTTP additive contract (``GovernedActionsFacade``), not
    to the MCP surface; they are intentionally absent here so no caller
    can collapse PREPARE into ACT through this boundary.
    """
    try:
        request = build_mcp_request()
        data = _governed.prepare_capability(
            request,
            capability=capability,
            args=args,
            operation_label=f"prepare_{capability}",
        )
        if data.get("persisted"):
            raise GovernedWriteError(
                "MCP PREPARE contract violation: prepare reported "
                "persisted=true — business outcome NOT declared.",
                code=PREPARE_PERSISTED_STATE_VIOLATION,
                status_code=500,
            )
        return _ok_result(data, _prepared_message(data))
    except Exception as exc:
        return handle_tool_error(exc)


def _act(capability: str, proposal_handle: str | None) -> CallToolResult:
    """Internal ACT by known capability (legacy test helpers). Prefer commit_proposal."""
    try:
        request = build_mcp_request()
        data = _orchestrator.act(
            request, capability=capability, proposal_handle=proposal_handle
        )
        if not data.get("verified"):
            return _error_result(
                "Write may have occurred but outcome was not verified.",
                status_code=409,
                error_code=OUTCOME_VERIFICATION_FAILED,
                data={"capability": capability, "result": data},
            )
        return _ok_result(data, "Write verified against authoritative read-back.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- READ tools -----------------------------------------------------------


def tool_get_my_context() -> CallToolResult:
    try:
        context = require_mcp_context()
        if not context.authorization:
            raise PermissionError("Unauthorized")
        user = context.user
        authorization = context.authorization
        email = getattr(user, "email", None)
        display_name = getattr(user, "name", None) or email
        data = _user_context.get_my_context(
            AuthenticatedUserContext(
                display_name=str(display_name or ""),
                email=str(email or ""),
                authorization=authorization,
            )
        )
        return _ok_result(data, "Contexto pessoal do usuário autenticado.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_get_methodology_guide(
    method: str | None = None,
    task: str | None = None,
) -> CallToolResult:
    """READ-only methodology. Same view gate as other Transformômetro reads.

    The playbook does not grant extra data and does not authorize writes.
    """
    try:
        request = build_mcp_request()
        data = _dispatch.get_methodology_guide(request, method=method, task=task)
        return _ok_result(data, "Guia metodológico do TÉO (não é fato nem autorização).")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_get_catalog() -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.get_catalog(request, transport="mcp"),
            "Catálogo do Transformômetro.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_get_process_context(
    process_id: str,
    instance_id: str | None = None,
    revision_id: str | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        data = _process_context.get_context(
            request,
            process_id=process_id,
            instance_id=instance_id,
            revision_id=revision_id,
        )
        return _ok_result(data, "Contexto de inteligência do processo.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_analyze(
    view: str,
    filial_id: str | None = None,
    setor_id: str | None = None,
    processo_id: str | None = None,
    revisao_id: str | None = None,
    familia_processo: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    limit: int | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
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
        return _ok_result(data, "Análise do Transformômetro.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_search_records(
    entity: str,
    parent_id: str | None = None,
    instance_id: str | None = None,
    filial_id: str | None = None,
    setor_id: str | None = None,
    status: str | None = None,
    familia_processo: str | None = None,
    q: str | None = None,
    unit_code: str | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
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
        return _ok_result(data, "Lista de registros.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_get_record(entity: str, id: str) -> CallToolResult:
    try:
        from tm_app.application.gpt_actions.response_compact import project_get_record

        request = build_mcp_request()
        return _ok_result(
            project_get_record(_dispatch.get_record(request, entity, id)),
            "Registro.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_evidence_read(
    action: str,
    scope: str | None = None,
    parent_id: str | None = None,
) -> CallToolResult:
    """READ: evidence metadata (action=list). Binary payloads are
    platform_blocked on this surface."""
    try:
        action_norm = str(action or "").strip().lower()
        if action_norm != "list":
            return _error_result(
                f"Unknown evidence_read action '{action_norm}'. "
                "Allowed: ['list'].",
                status_code=400,
                error_code="validation",
            )
        missing = [
            field
            for field, value in (("scope", scope), ("parent_id", parent_id))
            if not str(value or "").strip()
        ]
        if missing:
            return _error_result(
                f"Missing required field(s) for action 'list': "
                f"{', '.join(missing)}.",
                status_code=400,
                error_code="validation",
            )
        request = build_mcp_request()
        return _ok_result(
            _dispatch.list_evidence(
                request, scope=str(scope), parent_id=str(parent_id)
            ),
            "Evidências listadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_list_evidence(scope: str, parent_id: str) -> CallToolResult:
    """LEGACY alias — use evidence_read(action=list)."""
    return tool_evidence_read("list", scope=scope, parent_id=parent_id)


def tool_get_process_timeline(
    processo_id: str, page: int = 1, page_size: int = 100
) -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.get_process_timeline(
                request, processo_id=processo_id, page=page, page_size=page_size
            ),
            "Linha do tempo do processo.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# meeting_minute family — READ/analyze side. Transcript generation is a
# non-persisting analysis action on the same tool (never PREPARE/ACT).
# Canonical action set: MEETING_MINUTE_READ_ACTIONS (orchestrator).


def tool_meeting_minute_read(
    action: str,
    minute_id: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    """READ/analysis meeting-minute actions (no PREPARE/ACT persistence)."""
    try:
        action_norm = str(action or "").strip()
        if action_norm not in MEETING_MINUTE_READ_ACTIONS:
            return _error_result(
                f"Action '{action_norm}' is not a READ meeting-minute action. "
                "Allowed: "
                f"{sorted(MEETING_MINUTE_READ_ACTIONS)}. Writes use "
                "prepare_meeting_minute_change (then commit_proposal per "
                "execution_policy).",
                status_code=400,
                error_code="validation",
            )
        request = build_mcp_request()
        return _ok_result(
            _dispatch.manage_meeting_minute(
                request,
                action=action_norm,
                minute_id=minute_id,
                payload=data or {},
            ),
            "Meeting minute read.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_generate_from_transcript(
    minute_id: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    """LEGACY alias — use meeting_minute_read(action=generate_from_transcript)."""
    return tool_meeting_minute_read(
        "generate_from_transcript", minute_id=minute_id, data=data
    )


# --- PREPARE tools --------------------------------------------------------


def tool_prepare_record_change(
    entity: str,
    operation: str,
    record_id: str | None = None,
    changes: dict | None = None,
) -> CallToolResult:
    """Generic ENTITY prepare (create|update|delete|duplicate) → proposal_handle.

    Pure PREPARE on the MCP surface — the additive ``commit_now`` contract
    is GPT-Actions-HTTP-only and is not reachable from this boundary.
    """
    try:
        request = build_mcp_request()
        data = _governed.prepare_record_change(
            request,
            entity=entity,
            operation=operation,
            record_id=record_id,
            changes=changes or {},
        )
        if data.get("persisted"):
            raise GovernedWriteError(
                "MCP PREPARE contract violation: prepare reported "
                "persisted=true — business outcome NOT declared.",
                code=PREPARE_PERSISTED_STATE_VIOLATION,
                status_code=500,
            )
        return _ok_result(data, _prepared_message(data))
    except Exception as exc:
        return handle_tool_error(exc)


def tool_commit_proposal(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    """Common governed commit: opaque handle only; capability from stored proposal."""
    try:
        request = build_mcp_request()
        data = _governed.commit_proposal(
            request,
            proposal_handle=proposal_handle,
            confirmation=confirmation,
        )
        post = data.get("postcondition") or {}
        if not post.get("verified"):
            return _error_result(
                "Write may have occurred but outcome was not verified.",
                status_code=409,
                error_code=OUTCOME_VERIFICATION_FAILED,
                data=data,
            )
        return _ok_result(data, "Write verified against authoritative read-back.")
    except Exception as exc:
        return handle_tool_error(exc)


# Legacy bridge helpers (not registered as MCP tools) — delegate to V2 surface.


def tool_prepare_create_record(entity: str, data: dict | None = None) -> CallToolResult:
    return tool_prepare_record_change(
        entity=entity, operation="create", changes=data or {}
    )


def tool_prepare_update_record(
    entity: str, id: str, data: dict | None = None
) -> CallToolResult:
    return tool_prepare_record_change(
        entity=entity, operation="update", record_id=id, changes=data or {}
    )


def tool_prepare_delete_record(entity: str, id: str) -> CallToolResult:
    return tool_prepare_record_change(entity=entity, operation="delete", record_id=id)


def tool_prepare_duplicate_record(
    entity: str, id: str, data: dict | None = None
) -> CallToolResult:
    return tool_prepare_record_change(
        entity=entity, operation="duplicate", record_id=id, changes=data or {}
    )


# --- Semantic family: special governed operations ------------------------
# One-shot domain writes (revision lifecycle, dashboard recompute,
# improvement package commit, shared-resource cost). Closed action enum;
# each action resolves to its canonical capability (and its own
# execution_policy) — the family is a transport grouping, not a proxy.

_GOVERNED_OPERATION_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "activate_revision": ("id",),
    "adjust_shared_resource_cost": (
        "recurso_compartilhado_id",
        "valor_mensal",
        "vigente_desde",
    ),
    # recalculate_dashboard accepts revisao_id OR processo_id, and
    # commit_improvement_package completeness is owned by the package
    # validator — both report missing fields via the ready=false
    # checklist proposal, not a transport error.
}


def tool_prepare_governed_operation(
    action: str,
    id: str | None = None,
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
    recurso_compartilhado_id: str | None = None,
    valor_mensal: float | None = None,
    vigente_desde: str | None = None,
    observacoes: str | None = None,
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
    activate_scenario: bool = False,
    recalculate: bool = False,
) -> CallToolResult:
    """PREPARE only — one of the closed special governed operations."""
    action_norm = str(action or "").strip()
    capability = GOVERNED_OPERATION_ACTION_TO_CAPABILITY.get(action_norm)
    if capability is None:
        return _error_result(
            f"Unknown governed operation '{action_norm}'. Allowed: "
            f"{sorted(GOVERNED_OPERATION_ACTION_TO_CAPABILITY)}.",
            status_code=400,
            error_code="validation",
        )
    args = {
        "id": id,
        "revisao_id": revisao_id,
        "processo_id": processo_id,
        "competencia_inicio": competencia_inicio,
        "competencia_fim": competencia_fim,
        "recurso_compartilhado_id": recurso_compartilhado_id,
        "valor_mensal": valor_mensal,
        "vigente_desde": vigente_desde,
        "observacoes": observacoes,
        "process": process or {},
        "instance": instance or {},
        "baseline": baseline,
        "scenario": scenario,
        "activate_scenario": activate_scenario,
        "recalculate": recalculate,
    }
    missing = [
        field
        for field in _GOVERNED_OPERATION_REQUIRED_FIELDS.get(
            action_norm, ()
        )
        if args.get(field) in (None, "", {})
    ]
    if missing:
        return _error_result(
            f"Missing required field(s) for '{action_norm}': "
            f"{', '.join(missing)}.",
            status_code=400,
            error_code="validation",
        )
    return _prepare(capability, args)


def tool_prepare_activate_revision(id: str) -> CallToolResult:
    """LEGACY alias — use prepare_governed_operation(activate_revision)."""
    return tool_prepare_governed_operation("activate_revision", id=id)


def tool_prepare_recalculate_dashboard(
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
) -> CallToolResult:
    """LEGACY alias — use prepare_governed_operation(recalculate_dashboard)."""
    return tool_prepare_governed_operation(
        "recalculate_dashboard",
        revisao_id=revisao_id,
        processo_id=processo_id,
        competencia_inicio=competencia_inicio,
        competencia_fim=competencia_fim,
    )


def tool_prepare_improvement_package(
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
    activate_scenario: bool = False,
    recalculate: bool = False,
) -> CallToolResult:
    """LEGACY alias — prepare_governed_operation(commit_improvement_package)."""
    return tool_prepare_governed_operation(
        "commit_improvement_package",
        process=process,
        instance=instance,
        baseline=baseline,
        scenario=scenario,
        activate_scenario=activate_scenario,
        recalculate=recalculate,
    )


def tool_prepare_adjust_shared_resource_cost(
    recurso_compartilhado_id: str,
    valor_mensal: float,
    vigente_desde: str,
    observacoes: str | None = None,
) -> CallToolResult:
    """LEGACY alias — prepare_governed_operation(adjust_shared_resource_cost)."""
    return tool_prepare_governed_operation(
        "adjust_shared_resource_cost",
        recurso_compartilhado_id=recurso_compartilhado_id,
        valor_mensal=valor_mensal,
        vigente_desde=vigente_desde,
        observacoes=observacoes,
    )


# --- Semantic family: evidence (structured metadata only) -----------------

_EVIDENCE_WRITE_ACTIONS = frozenset(
    {"create_link", "update_description", "delete"}
)


def tool_prepare_evidence_change(
    action: str,
    scope: str,
    parent_id: str,
    evidence_id: str | None = None,
    url_externa: str | None = None,
    descricao: str | None = None,
    confirm_delete: bool = False,
) -> CallToolResult:
    """PREPARE only — evidence create_link|update_description|delete."""
    action_norm = str(action or "").strip()
    if action_norm not in _EVIDENCE_WRITE_ACTIONS:
        return _error_result(
            f"Unknown evidence action '{action_norm}'. "
            f"Allowed: {sorted(_EVIDENCE_WRITE_ACTIONS)}.",
            status_code=400,
            error_code="validation",
        )
    missing = [
        field
        for field, value in (("scope", scope), ("parent_id", parent_id))
        if not str(value or "").strip()
    ]
    if missing:
        return _error_result(
            f"Missing required field(s): {', '.join(missing)}.",
            status_code=400,
            error_code="validation",
        )
    return _prepare(
        "manage_evidence",
        {
            "scope": scope,
            "operation": action_norm,
            "parent_id": parent_id,
            "evidence_id": evidence_id,
            "url_externa": url_externa,
            "descricao": descricao,
            "confirm_delete": confirm_delete,
        },
    )


def tool_prepare_manage_evidence(
    scope: str,
    operation: str,
    parent_id: str,
    evidence_id: str | None = None,
    url_externa: str | None = None,
    descricao: str | None = None,
    confirm_delete: bool = False,
) -> CallToolResult:
    """LEGACY alias — use prepare_evidence_change(action=operation)."""
    return tool_prepare_evidence_change(
        operation,
        scope=scope,
        parent_id=parent_id,
        evidence_id=evidence_id,
        url_externa=url_externa,
        descricao=descricao,
        confirm_delete=confirm_delete,
    )


# --- Semantic family: meeting minutes --------------------------------------
# One PREPARE surface for workflow transitions (send|finalize|cancel) and
# manage writes (resend|create_version|set_participants|set_signers).
# READ/analyze actions are rejected here with a pointer to
# meeting_minute_read.

def tool_prepare_meeting_minute_change(
    action: str,
    minute_id: str | None = None,
    reason: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    """PREPARE only — closed meeting-minute write action enum."""
    action_norm = str(action or "").strip()
    capability = MEETING_MINUTE_ACTION_TO_CAPABILITY.get(action_norm)
    if capability is None:
        return _error_result(
            f"Unknown meeting-minute write action '{action_norm}'. Allowed: "
            f"{sorted(MEETING_MINUTE_ACTION_TO_CAPABILITY)}. READ/analyze "
            "actions use meeting_minute_read.",
            status_code=400,
            error_code="validation",
        )
    if not str(minute_id or "").strip():
        return _error_result(
            "minute_id is required for meeting-minute writes.",
            status_code=400,
            error_code="validation",
        )
    if capability == "meeting_minute_workflow":
        return _prepare(
            capability,
            {"id": minute_id, "action": action_norm, "reason": reason},
        )
    return _prepare(
        capability,
        {
            "action": action_norm,
            "minute_id": minute_id,
            "data": data or {},
        },
    )


def tool_prepare_meeting_minute_workflow(
    id: str, action: str, reason: str | None = None
) -> CallToolResult:
    """LEGACY alias — use prepare_meeting_minute_change."""
    return tool_prepare_meeting_minute_change(
        action, minute_id=id, reason=reason
    )


def tool_prepare_meeting_minute_manage(
    action: str,
    minute_id: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    """LEGACY alias — use prepare_meeting_minute_change."""
    action_norm = str(action or "").strip()
    if action_norm in MEETING_MANAGE_NON_ACT:
        return _error_result(
            f"Action '{action_norm}' is not an ACT write. "
            "Use meeting_minute_read.",
            status_code=400,
            error_code="validation",
        )
    return tool_prepare_meeting_minute_change(
        action_norm, minute_id=minute_id, data=data
    )


# --- Semantic family: collaboration -----------------------------------------
# Transformômetro tasks (TaskCommandUseCases) + interaction rooms/messages
# (InteractionRoomUseCases) share one governed surface. The ``action``
# argument selects the semantic capability — and therefore the canonical
# execution_policy (auto_act vs confirm_before_act) — per action.

_COLLABORATION_READ_ACTIONS = COLLABORATION_READ_ACTIONS


def tool_collaboration_read(
    action: str,
    task_id: str | None = None,
    processo_id: str | None = None,
    status: str = "pending",
    room_id: str | None = None,
    inbox_filter: str = "all",
    limit: int = 50,
    before_id: str | None = None,
) -> CallToolResult:
    """READ: tasks (my_tasks|task|process_tasks) and rooms
    (rooms|room|messages|attachments metadata)."""
    try:
        action_norm = str(action or "").strip().lower()
        if action_norm not in _COLLABORATION_READ_ACTIONS:
            return _error_result(
                f"Unknown collaboration_read action '{action_norm}'. "
                f"Allowed: {sorted(_COLLABORATION_READ_ACTIONS)}.",
                status_code=400,
                error_code="validation",
            )
        request = build_mcp_request()
        if action_norm == "my_tasks":
            return _ok_result(
                _dispatch.list_my_tasks(request, status=status),
                "Tarefas do usuário autenticado.",
            )
        if action_norm == "process_tasks":
            if not str(processo_id or "").strip():
                return _error_result(
                    "processo_id is required for action 'process_tasks'.",
                    status_code=400,
                    error_code="validation",
                )
            return _ok_result(
                _dispatch.list_process_tasks(request, str(processo_id)),
                "Tarefas relacionadas ao processo.",
            )
        if action_norm == "task":
            if not str(task_id or "").strip():
                return _error_result(
                    "task_id is required for action 'task'.",
                    status_code=400,
                    error_code="validation",
                )
            return _ok_result(
                _dispatch.get_task(request, str(task_id)), "Tarefa carregada."
            )
        if action_norm == "rooms":
            return _ok_result(
                _dispatch.list_rooms(request, inbox_filter=inbox_filter),
                "Salas de interação.",
            )
        if not str(room_id or "").strip():
            return _error_result(
                f"room_id is required for action '{action_norm}'.",
                status_code=400,
                error_code="validation",
            )
        if action_norm == "room":
            return _ok_result(
                _dispatch.get_room(request, str(room_id)), "Sala carregada."
            )
        if action_norm == "messages":
            return _ok_result(
                _dispatch.list_room_messages(
                    request,
                    str(room_id),
                    limit=int(limit),
                    before_id=before_id,
                ),
                "Mensagens da sala.",
            )
        return _ok_result(
            _dispatch.list_room_attachments(request, str(room_id)),
            "Metadados de anexos da sala.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_prepare_collaboration_change(
    action: str,
    task_id: str | None = None,
    title: str | None = None,
    description: str | None = None,
    assignee_user_id: str | None = None,
    due_date: str | None = None,
    source_interaction_message_id: str | None = None,
    processo_id: str | None = None,
    room_id: str | None = None,
    message_id: str | None = None,
    content: str | None = None,
    parent_id: str | None = None,
    mentions: list | None = None,
    reaction: str | None = None,
) -> CallToolResult:
    """PREPARE only — task + room/message writes via canonical use cases.

    Binary attachment upload/download is NOT exposed on this surface —
    no file transport exists in MCP/ChatGPT (platform_blocked).
    """
    action_norm = str(action or "").strip().lower()
    capability = COLLABORATION_ACTION_TO_CAPABILITY.get(action_norm)
    if capability is None:
        return _error_result(
            f"Unknown collaboration action '{action_norm}'. Allowed: "
            f"{sorted(COLLABORATION_ACTION_TO_CAPABILITY)}.",
            status_code=400,
            error_code="validation",
        )
    return _prepare(
        capability,
        {
            "action": action_norm,
            "task_id": task_id,
            "title": title,
            "description": description,
            "assignee_user_id": assignee_user_id,
            "due_date": due_date,
            "source_interaction_message_id": source_interaction_message_id,
            "processo_id": processo_id,
            "room_id": room_id,
            "message_id": message_id,
            "content": content,
            "parent_id": parent_id,
            "mentions": mentions,
            "reaction": reaction,
        },
    )


# Legacy transport wrappers — names tombstoned from the tool surface;
# kept for internal callers/tests. Translate old action vocabularies to
# the canonical family actions.

_LEGACY_TASK_READ_ACTION = {"mine": "my_tasks", "related": "process_tasks", "get": "task"}
_LEGACY_ROOM_READ_ACTION = {"list": "rooms", "get": "room"}
_LEGACY_TASK_WRITE_ACTION = {
    "create": "create_task",
    "update": "update_task",
    "complete": "complete_task",
    "cancel": "cancel_task",
}
_LEGACY_ROOM_WRITE_ACTION = {
    "open": "open_room",
    "post_message": "post_message",
    "edit_message": "edit_message",
    "delete_message": "delete_message",
    "reaction": "toggle_reaction",
    "pin": "pin_message",
    "unpin": "unpin_message",
    "mark_read": "mark_room_read",
}


def tool_task_read(
    action: str,
    task_id: str | None = None,
    processo_id: str | None = None,
    status: str = "pending",
) -> CallToolResult:
    """LEGACY alias — use collaboration_read."""
    action_norm = _LEGACY_TASK_READ_ACTION.get(str(action or "").strip().lower())
    if action_norm is None:
        return _error_result(
            f"Unknown task_read action '{action}'. Allowed: "
            f"{sorted(_LEGACY_TASK_READ_ACTION)}. This tool is tombstoned — "
            "use collaboration_read.",
            status_code=400,
            error_code="validation",
        )
    return tool_collaboration_read(
        action_norm, task_id=task_id, processo_id=processo_id, status=status
    )


def tool_interaction_room_read(
    action: str,
    room_id: str | None = None,
    inbox_filter: str = "all",
    limit: int = 50,
    before_id: str | None = None,
) -> CallToolResult:
    """LEGACY alias — use collaboration_read."""
    raw = str(action or "").strip().lower()
    action_norm = _LEGACY_ROOM_READ_ACTION.get(raw, raw)
    if action_norm not in {"rooms", "room", "messages", "attachments"}:
        return _error_result(
            f"Unknown interaction_room_read action '{action}'. This tool is "
            "tombstoned — use collaboration_read.",
            status_code=400,
            error_code="validation",
        )
    return tool_collaboration_read(
        action_norm,
        room_id=room_id,
        inbox_filter=inbox_filter,
        limit=limit,
        before_id=before_id,
    )


def tool_prepare_task(
    action: str,
    task_id: str | None = None,
    title: str | None = None,
    description: str | None = None,
    assignee_user_id: str | None = None,
    due_date: str | None = None,
    source_interaction_message_id: str | None = None,
) -> CallToolResult:
    """LEGACY alias — use prepare_collaboration_change."""
    action_norm = _LEGACY_TASK_WRITE_ACTION.get(str(action or "").strip().lower())
    if action_norm is None:
        return _error_result(
            f"Unknown task action '{action}'. Allowed: "
            f"{sorted(_LEGACY_TASK_WRITE_ACTION)}. This tool is tombstoned — "
            "use prepare_collaboration_change.",
            status_code=400,
            error_code="validation",
        )
    return tool_prepare_collaboration_change(
        action_norm,
        task_id=task_id,
        title=title,
        description=description,
        assignee_user_id=assignee_user_id,
        due_date=due_date,
        source_interaction_message_id=source_interaction_message_id,
    )


def tool_prepare_interaction_room(
    action: str,
    processo_id: str | None = None,
    room_id: str | None = None,
    message_id: str | None = None,
    content: str | None = None,
    parent_id: str | None = None,
    mentions: list | None = None,
    reaction: str | None = None,
) -> CallToolResult:
    """LEGACY alias — use prepare_collaboration_change."""
    raw = str(action or "").strip().lower()
    action_norm = _LEGACY_ROOM_WRITE_ACTION.get(raw)
    if action_norm is None:
        return _error_result(
            f"Unknown interaction-room action '{action}'. Allowed: "
            f"{sorted(_LEGACY_ROOM_WRITE_ACTION)}. This tool is tombstoned — "
            "use prepare_collaboration_change.",
            status_code=400,
            error_code="validation",
        )
    return tool_prepare_collaboration_change(
        action_norm,
        processo_id=processo_id,
        room_id=room_id,
        message_id=message_id,
        content=content,
        parent_id=parent_id,
        mentions=mentions,
        reaction=reaction,
    )


# --- Diagnostic V1 (MCP-native): canonical READ use cases + governed PREPARE ---

# Server-generated ids for additive manage actions — canonical policy lives
# in diagnostic_capabilities; this alias keeps the boundary readable.
_DIAGNOSTIC_ADDITIVE_ID_FIELD = SERVER_GENERATED_ID_FIELD

# Transport projections shared with the Portal HTTP surface — single source:
# tm_app/interface/diagnostic_projection.py.


_DIAGNOSTIC_READ_ACTIONS = frozenset({"get", "by_revision"})


def tool_diagnostic_read(
    action: str,
    diagnostic_id: str | None = None,
    revision_id: str | None = None,
) -> CallToolResult:
    """READ: canonical Diagnostic get|by_revision — projections of
    GetDiagnostic / ListDiagnosticsByRevision."""
    try:
        action_norm = str(action or "").strip().lower()
        request = build_mcp_request()
        # Same canonical end-user gate as writes: authenticated,
        # principal_type==user, transformometro.access. No local RBAC.
        require_prepare_authz(request)
        if action_norm == "get":
            if not str(diagnostic_id or "").strip():
                return _error_result(
                    "diagnostic_id is required for action 'get'.",
                    status_code=400,
                    error_code="validation",
                )
            ctx = GetDiagnostic(
                _diagnostic_stack.diagnostics,
                _diagnostic_stack.revisions,
                _diagnostic_stack.evidence,
            ).execute(str(diagnostic_id))
            return _ok_result(
                project_read_context(ctx), "Diagnostic carregado."
            )
        if action_norm == "by_revision":
            if not str(revision_id or "").strip():
                return _error_result(
                    "revision_id is required for action 'by_revision'.",
                    status_code=400,
                    error_code="validation",
                )
            result = ListDiagnosticsByRevision(
                _diagnostic_stack.diagnostics,
                _diagnostic_stack.revisions,
            ).execute(str(revision_id))
            items = [project_summary(item) for item in result.items]
            payload = {
                "revision": project_revision(result.revision),
                "items": items,
            }
            return _ok_result(
                payload, "Diagnostics da revisão carregados."
            )
        return _error_result(
            f"Unknown diagnostic_read action '{action_norm}'. "
            f"Allowed: {sorted(_DIAGNOSTIC_READ_ACTIONS)}.",
            status_code=400,
            error_code="validation",
        )
    except Exception as exc:  # noqa: BLE001
        return handle_tool_error(exc)


def tool_get_diagnostic(diagnostic_id: str) -> CallToolResult:
    """LEGACY alias — use diagnostic_read(action=get)."""
    return tool_diagnostic_read("get", diagnostic_id=diagnostic_id)


def tool_list_diagnostics_by_revision(revision_id: str) -> CallToolResult:
    """LEGACY alias — use diagnostic_read(action=by_revision)."""
    return tool_diagnostic_read("by_revision", revision_id=revision_id)


def tool_prepare_diagnostic_change(
    action: str,
    diagnostic_id: str | None = None,
    revision_id: str | None = None,
    problem_statement: str | None = None,
    provenance: dict | None = None,
    payload: dict | None = None,
) -> CallToolResult:
    """PREPARE only — action=create or one of the canonical manage actions.

    Entity ids are generated server-side; the caller must never supply
    them. Policy: create → auto_act; manage actions → confirm_before_act.
    """
    action_norm = str(action or "").strip()
    if action_norm == "create":
        missing = [
            field
            for field, value in (
                ("revision_id", revision_id),
                ("problem_statement", problem_statement),
            )
            if not str(value or "").strip()
        ]
        if missing:
            return _error_result(
                f"Missing required field(s) for action 'create': "
                f"{', '.join(missing)}.",
                status_code=400,
                error_code="validation",
            )
        args = {
            "diagnostic_id": str(uuid4()),
            "revision_id": revision_id,
            "problem_statement": problem_statement,
            "provenance": provenance,
        }
        return _prepare("create_diagnostic", args)
    if action_norm not in MANAGE_ACTIONS:
        return _error_result(
            f"Unknown Diagnostic action '{action_norm}'. Allowed: create, "
            f"{', '.join(sorted(MANAGE_ACTIONS))}.",
            status_code=400,
            error_code="validation",
        )
    if not str(diagnostic_id or "").strip():
        return _error_result(
            f"diagnostic_id is required for action '{action_norm}'.",
            status_code=400,
            error_code="validation",
        )
    body = dict(payload or {})
    id_field = _DIAGNOSTIC_ADDITIVE_ID_FIELD.get(action_norm)
    if id_field is not None:
        if id_field in body:
            return _error_result(
                f"'{id_field}' is server-generated for action "
                f"'{action_norm}' and must not be supplied by the caller.",
                status_code=400,
                error_code="validation",
            )
        body[id_field] = str(uuid4())
    return _prepare(
        "manage_diagnostic",
        {
            "diagnostic_id": diagnostic_id,
            "action": action_norm,
            "payload": body,
        },
    )


def tool_prepare_create_diagnostic(
    revision_id: str,
    problem_statement: str,
    provenance: dict | None = None,
) -> CallToolResult:
    """LEGACY alias — use prepare_diagnostic_change(action=create)."""
    return tool_prepare_diagnostic_change(
        "create",
        revision_id=revision_id,
        problem_statement=problem_statement,
        provenance=provenance,
    )


def tool_prepare_manage_diagnostic(
    diagnostic_id: str,
    action: str,
    payload: dict | None = None,
) -> CallToolResult:
    """LEGACY alias — use prepare_diagnostic_change(action=<manage action>)."""
    return tool_prepare_diagnostic_change(
        action, diagnostic_id=diagnostic_id, payload=payload
    )


# --- Legacy ACT helpers (delegate to common commit; not MCP-registered) ---


def tool_act_create_record(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_update_record(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_delete_record(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_duplicate_record(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_activate_revision(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_recalculate_dashboard(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_meeting_minute_workflow(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_commit_improvement_package(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_manage_evidence(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_adjust_shared_resource_cost(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


def tool_act_meeting_minute_manage(
    proposal_handle: str, confirmation: bool
) -> CallToolResult:
    return tool_commit_proposal(proposal_handle, confirmation=confirmation)


# Back-compat aliases used by older smoke tests (map to prepare/act semantics).
def tool_validate_improvement_package(
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
) -> CallToolResult:
    return tool_prepare_improvement_package(
        process=process,
        instance=instance,
        baseline=baseline,
        scenario=scenario,
    )


def tool_commit_improvement_package(
    proposal_handle: str | None = None,
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
    dry_run: bool = False,
    activate_scenario: bool = False,
    recalculate: bool = False,
    confirmation: bool = False,
) -> CallToolResult:
    """ACT requires proposal_handle. dry_run without handle re-prepares only."""
    if proposal_handle:
        return tool_act_commit_improvement_package(
            proposal_handle, confirmation=confirmation
        )
    if dry_run:
        return tool_prepare_improvement_package(
            process=process,
            instance=instance,
            baseline=baseline,
            scenario=scenario,
            activate_scenario=activate_scenario,
            recalculate=recalculate,
        )
    return _error_result(
        "proposal_handle is required for commit ACT. "
        "Call prepare_improvement_package first.",
        status_code=400,
        error_code="proposal_required",
    )


def tool_manage_evidence(
    scope: str,
    operation: str,
    parent_id: str,
    evidence_id: str | None = None,
    url_externa: str | None = None,
    descricao: str | None = None,
    confirm_delete: bool = False,
    proposal_handle: str | None = None,
    confirmation: bool = False,
) -> CallToolResult:
    if proposal_handle:
        return tool_act_manage_evidence(
            proposal_handle, confirmation=confirmation
        )
    return tool_prepare_manage_evidence(
        scope=scope,
        operation=operation,
        parent_id=parent_id,
        evidence_id=evidence_id,
        url_externa=url_externa,
        descricao=descricao,
        confirm_delete=confirm_delete,
    )


__all__ = [
    "ACT_TOOL_CAPABILITY",
    "PREPARE_TOOL_CAPABILITY",
    "build_mcp_request",
    "handle_tool_error",
]
