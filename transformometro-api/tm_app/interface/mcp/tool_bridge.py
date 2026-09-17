"""Bridge MCP tools → existing GPT Actions application services.

Rebuilds a Starlette Request from delpi_auth context so AuthZ helpers that
read ``request.state.user`` keep working without duplicating RBAC.
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
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
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
from tm_app.interface.mcp.oauth_contract import mcp_www_authenticate_meta

logger = logging.getLogger(__name__)

_dispatch = GptActionsDispatchService()
_packages = GuidedImprovementPackageService(_dispatch)
_process_context = ProcessContextService()
_user_context = UserContextService(person_profile_reader=CorePersonProfileGateway())


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
) -> CallToolResult:
    payload = {
        "success": False,
        "message": message,
        "data": data or {"error_kind": "client"},
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
            return _error_result("Authentication required.", status_code=401)
        return _error_result("Forbidden", status_code=403, data={"error_kind": "authz"})
    if isinstance(exc, GptActionsError):
        return _error_result(
            exc.message,
            status_code=exc.status_code,
            data=dict(exc.data or {}) or {"error_kind": "client"},
        )
    if isinstance(exc, (ValueError, LookupError)) and not isinstance(exc, KeyError):
        return _error_result(str(exc), status_code=400, data={"error_kind": "validation"})
    if isinstance(exc, JSONResponse):
        # Should not happen; _raise_http_err converts these.
        return _error_result("Acesso negado.", status_code=403, data={"error_kind": "authz"})
    logger.exception("teo_mcp_tool_unhandled")
    return _error_result(
        "Erro interno do servidor.",
        status_code=500,
        data={"error_kind": "internal", "error_type": type(exc).__name__},
    )


# --- tool implementations -------------------------------------------------


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
        request = build_mcp_request()
        return _ok_result(_dispatch.get_record(request, entity, id), "Registro.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_create_record(entity: str, data: dict | None = None) -> CallToolResult:
    try:
        request = build_mcp_request()
        result, message, _status = _dispatch.create_record(
            request, entity, {"data": data or {}}
        )
        return _ok_result(result, message)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_update_record(entity: str, id: str, data: dict | None = None) -> CallToolResult:
    try:
        request = build_mcp_request()
        result, message = _dispatch.update_record(
            request, entity, id, {"data": data or {}}
        )
        return _ok_result(result, message)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_delete_record(entity: str, id: str) -> CallToolResult:
    try:
        request = build_mcp_request()
        result, message = _dispatch.delete_record(request, entity, id)
        return _ok_result(result, message)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_duplicate_record(
    entity: str, id: str, data: dict | None = None
) -> CallToolResult:
    try:
        request = build_mcp_request()
        result, message, _status = _dispatch.duplicate_record(
            request, entity, id, {"data": data or {}} if data else None
        )
        return _ok_result(result, message)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_activate_revision(id: str) -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.activate_revision(request, id),
            "Revisão ativada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_recalculate_dashboard(
    revisao_id: str | None = None,
    processo_id: str | None = None,
    competencia_inicio: str | None = None,
    competencia_fim: str | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        result = _dispatch.recalculate_dashboard(
            request,
            revisao_id=revisao_id,
            processo_id=processo_id,
            competencia_inicio=competencia_inicio,
            competencia_fim=competencia_fim,
        )
        mode = result.get("mode")
        message = (
            "Cache do dashboard atualizado (incremental)."
            if mode == "incremental"
            else "Cache do dashboard atualizado (completo)."
        )
        return _ok_result(result, message)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_meeting_minute_workflow(
    id: str, action: str, reason: str | None = None
) -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.meeting_minute_workflow(
                request, id, action=action, reason=reason
            ),
            "Workflow de ata executado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_validate_improvement_package(
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        data = _packages.validate(
            request,
            {
                "process": process or {},
                "instance": instance or {},
                "baseline": baseline,
                "scenario": scenario,
            },
        )
        message = (
            "Pacote pronto para commit."
            if data.get("ready")
            else "Pacote incompleto — veja missing."
        )
        return _ok_result(data, message)
    except Exception as exc:
        return handle_tool_error(exc)


def tool_commit_improvement_package(
    process: dict | None = None,
    instance: dict | None = None,
    baseline: dict | None = None,
    scenario: dict | None = None,
    dry_run: bool = False,
    activate_scenario: bool = False,
    recalculate: bool = False,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        body = {
            "process": process or {},
            "instance": instance or {},
            "baseline": baseline,
            "scenario": scenario,
            "dry_run": dry_run,
            "activate_scenario": activate_scenario,
            "recalculate": recalculate,
        }
        data = _packages.commit(request, body)
        if dry_run:
            message = (
                "Pacote pronto para commit."
                if data.get("ready")
                else "Pacote incompleto — veja missing."
            )
        else:
            message = "Pacote de melhoria gravado."
        return _ok_result(data, message)
    except GptActionsError as exc:
        if exc.status_code == 404:
            data = dict(exc.data or {})
            data.setdefault("not_found", True)
            return _error_result(exc.message, status_code=400, data=data)
        return handle_tool_error(exc)
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


def tool_manage_evidence(
    scope: str,
    operation: str,
    parent_id: str,
    evidence_id: str | None = None,
    url_externa: str | None = None,
    descricao: str | None = None,
    confirm_delete: bool = False,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        data = _dispatch.manage_evidence(
            request,
            scope=scope,
            operation=operation,
            parent_id=parent_id,
            evidence_id=evidence_id,
            url_externa=url_externa,
            descricao=descricao,
            confirm_delete=confirm_delete,
        )
        return _ok_result(data, "Evidência atualizada.")
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


def tool_adjust_shared_resource_cost(
    recurso_compartilhado_id: str,
    valor_mensal: float,
    vigente_desde: str,
    observacoes: str | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.adjust_shared_resource_cost(
                request,
                recurso_compartilhado_id=recurso_compartilhado_id,
                valor_mensal=valor_mensal,
                vigente_desde=vigente_desde,
                observacoes=observacoes,
            ),
            "Reajuste de custo registrado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_meeting_minute_manage(
    action: str,
    minute_id: str | None = None,
    data: dict | None = None,
) -> CallToolResult:
    try:
        request = build_mcp_request()
        return _ok_result(
            _dispatch.manage_meeting_minute(
                request,
                action=action,
                minute_id=minute_id,
                payload=data or {},
            ),
            "Operação de ata executada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)
