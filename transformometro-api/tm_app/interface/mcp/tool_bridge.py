"""Bridge MCP tools → governed writes + existing GPT Actions services.

Rebuilds a Starlette Request from delpi_auth context so AuthZ helpers that
read ``request.state.user`` keep working without duplicating RBAC.

Material writes: PREPARE → opaque proposal_handle → commit_proposal
(no model-trusted mutation; capability comes from the stored proposal).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi.responses import JSONResponse
from mcp.types import CallToolResult, TextContent
from starlette.requests import Request

from delpi_auth.request_context import (
    get_current_user,
    get_request_authorization,
)
from tm_app.application.governed_writes.errors import (
    OUTCOME_VERIFICATION_FAILED,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    MEETING_MANAGE_NON_ACT,
    MEETING_MANAGE_READ_ACTIONS,
    GovernedWriteOrchestrator,
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
from tm_app.application.gpt_actions.user_context_service import (
    AuthenticatedUserContext,
    UserContextService,
)
from tm_app.infrastructure.gateways.core_person_profile_gateway import (
    CorePersonProfileGateway,
)
from tm_app.interface.mcp.constants import (
    ACT_TOOL_CAPABILITY,
    PREPARE_TOOL_CAPABILITY,
)
from tm_app.interface.mcp.oauth_contract import mcp_www_authenticate_meta

logger = logging.getLogger(__name__)

_dispatch = GptActionsDispatchService()
_packages = GuidedImprovementPackageService(_dispatch)
_orchestrator = GovernedWriteOrchestrator(_dispatch, _packages)
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
    user = get_current_user()
    if user is None:
        raise PermissionError("Unauthorized")
    auth = (get_request_authorization() or "").strip()
    headers: list[tuple[bytes, bytes]] = []
    if auth:
        headers.append((b"authorization", auth.encode("utf-8")))
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 0),
        "server": ("transformometro-api", 443),
    }
    request = Request(scope)
    request.state.user = user
    return request


def _ok_result(data: Any, message: str = "ok") -> CallToolResult:
    payload = {"success": True, "message": message, "data": data}
    text = json.dumps(payload, ensure_ascii=False, default=str)
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structuredContent=payload,
        isError=False,
    )


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
    text = json.dumps(payload, ensure_ascii=False, default=str)
    result: dict[str, Any] = {
        "content": [{"type": "text", "text": text}],
        "structuredContent": payload,
        "isError": True,
    }
    if status_code == 401:
        result["_meta"] = mcp_www_authenticate_meta(
            error="invalid_token",
            error_description="Authentication required",
        )
    return CallToolResult.model_validate(result)


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
    if isinstance(exc, GovernedWriteError):
        return _error_result(
            exc.message,
            status_code=exc.status_code,
            data=dict(exc.data or {}),
            error_code=exc.code,
        )
    if isinstance(exc, GptActionsError):
        code = "validation"
        if exc.status_code == 401:
            code = "unauthenticated"
        elif exc.status_code == 403:
            code = "forbidden"
        elif exc.status_code == 404:
            code = "not_found"
        elif exc.status_code == 409:
            code = "conflict"
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


def _prepare(
    capability: str,
    args: dict[str, Any],
    *,
    commit_now: bool = False,
    confirmation: bool = False,
    idempotency_key: str | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        data = _governed.prepare_capability(
            request,
            capability=capability,
            args=args,
            operation_label=f"prepare_{capability}",
            commit_now=bool(commit_now),
            confirmation=bool(confirmation),
            idempotency_key=idempotency_key,
        )
        if data.get("persisted"):
            return _ok_result(data, "Change persisted and verified (commit_now).")
        prop = data.get("proposal") if isinstance(data.get("proposal"), dict) else {}
        if prop and not prop.get("act_allowed", True):
            return _ok_result(
                data,
                "Proposal prepared but not ready for commit (see validation_result).",
            )
        return _ok_result(
            data,
            "Governed proposal prepared. Confirm with commit_proposal(proposal_handle).",
        )
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
        user = get_current_user()
        if user is None:
            raise PermissionError("Unauthorized")
        authorization = (get_request_authorization() or "").strip()
        if not authorization:
            raise PermissionError("Unauthorized")
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
        return _ok_result(_dispatch.get_catalog(request), "Catálogo do Transformômetro.")
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


def tool_list_evidence(scope: str, parent_id: str) -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.list_evidence(request, scope=scope, parent_id=parent_id),
            "Evidências listadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


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


def tool_meeting_minute_read(
    action: str,
    minute_id: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    """READ-only meeting-minute manage actions (no PREPARE/ACT)."""
    try:
        action_norm = str(action or "").strip()
        if action_norm not in MEETING_MANAGE_READ_ACTIONS:
            return _error_result(
                f"Action '{action_norm}' is not a READ meeting-minute action. "
                "Use prepare_meeting_minute_manage / act_meeting_minute_manage, "
                "or generate_from_transcript.",
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
    """Analysis-only: generate draft from transcript without persistence ACT."""
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.manage_meeting_minute(
                request,
                action="generate_from_transcript",
                minute_id=minute_id,
                payload=data or {},
            ),
            "Transcript analysis (no persistence).",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- PREPARE tools --------------------------------------------------------


def tool_prepare_record_change(
    entity: str,
    operation: str,
    record_id: str | None = None,
    changes: dict | None = None,
    commit_now: bool = False,
    confirmation: bool = False,
    idempotency_key: str | None = None,
) -> CallToolResult:
    """Generic ENTITY prepare (create|update|delete|duplicate) → proposal_handle.

    Additive ops may set commit_now=true for atomic PREPARE+ACT.
    """
    try:
        request = build_mcp_request()
        data = _governed.prepare_record_change(
            request,
            entity=entity,
            operation=operation,
            record_id=record_id,
            changes=changes or {},
            commit_now=bool(commit_now),
            confirmation=bool(confirmation),
            idempotency_key=idempotency_key,
        )
        if data.get("persisted"):
            return _ok_result(data, "Change persisted and verified (commit_now).")
        prop = data.get("proposal") if isinstance(data.get("proposal"), dict) else {}
        if prop and not prop.get("act_allowed", True):
            return _ok_result(
                data,
                "Proposal prepared but not ready for commit (see validation_result).",
            )
        return _ok_result(
            data,
            "Governed proposal prepared. Confirm with commit_proposal(proposal_handle).",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_commit_proposal(
    proposal_handle: str, confirmation: bool = True
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


def tool_prepare_activate_revision(id: str) -> CallToolResult:
    return _prepare("activate_revision", {"id": id})


def tool_prepare_recalculate_dashboard(
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
) -> CallToolResult:
    return _prepare(
        "recalculate_dashboard",
        {
            "revisao_id": revisao_id,
            "processo_id": processo_id,
            "competencia_inicio": competencia_inicio,
            "competencia_fim": competencia_fim,
        },
    )


def tool_prepare_meeting_minute_workflow(
    id: str, action: str, reason: str | None = None
) -> CallToolResult:
    return _prepare(
        "meeting_minute_workflow",
        {"id": id, "action": action, "reason": reason},
    )


def tool_prepare_improvement_package(
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
    activate_scenario: bool = False,
    recalculate: bool = False,
    commit_now: bool = False,
    confirmation: bool = False,
    idempotency_key: str | None = None,
) -> CallToolResult:
    return _prepare(
        "commit_improvement_package",
        {
            "process": process or {},
            "instance": instance or {},
            "baseline": baseline,
            "scenario": scenario,
            "activate_scenario": activate_scenario,
            "recalculate": recalculate,
        },
        commit_now=commit_now,
        confirmation=confirmation,
        idempotency_key=idempotency_key,
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
    return _prepare(
        "manage_evidence",
        {
            "scope": scope,
            "operation": operation,
            "parent_id": parent_id,
            "evidence_id": evidence_id,
            "url_externa": url_externa,
            "descricao": descricao,
            "confirm_delete": confirm_delete,
        },
    )


def tool_prepare_adjust_shared_resource_cost(
    recurso_compartilhado_id: str,
    valor_mensal: float,
    vigente_desde: str,
    observacoes: str | None = None,
    commit_now: bool = False,
    confirmation: bool = False,
    idempotency_key: str | None = None,
) -> CallToolResult:
    return _prepare(
        "adjust_shared_resource_cost",
        {
            "recurso_compartilhado_id": recurso_compartilhado_id,
            "valor_mensal": valor_mensal,
            "vigente_desde": vigente_desde,
            "observacoes": observacoes,
        },
        commit_now=commit_now,
        confirmation=confirmation,
        idempotency_key=idempotency_key,
    )


def tool_prepare_meeting_minute_manage(
    action: str,
    minute_id: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    action_norm = str(action or "").strip()
    if action_norm in MEETING_MANAGE_NON_ACT:
        return _error_result(
            f"Action '{action_norm}' is not an ACT write. "
            "Use meeting_minute_read or generate_from_transcript.",
            status_code=400,
            error_code="validation",
        )
    return _prepare(
        "meeting_minute_manage",
        {"action": action_norm, "minute_id": minute_id, "data": data or {}},
    )


# --- Legacy ACT helpers (delegate to common commit; not MCP-registered) ---


def tool_act_create_record(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_update_record(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_delete_record(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_duplicate_record(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_activate_revision(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_recalculate_dashboard(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_meeting_minute_workflow(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_commit_improvement_package(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_manage_evidence(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_adjust_shared_resource_cost(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


def tool_act_meeting_minute_manage(proposal_handle: str) -> CallToolResult:
    return tool_commit_proposal(proposal_handle)


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
) -> CallToolResult:
    """ACT requires proposal_handle. dry_run without handle re-prepares only."""
    if proposal_handle:
        return tool_act_commit_improvement_package(proposal_handle)
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
) -> CallToolResult:
    if proposal_handle:
        return tool_act_manage_evidence(proposal_handle)
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
