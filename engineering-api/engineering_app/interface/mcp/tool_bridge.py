"""EVA MCP tool bridge — adapters over the official use cases.

Identidade: o contexto autenticado pelo transporte MCP (delpi_auth
middleware + audience/scope) é o mesmo objeto canônico do request;
``access_token`` humano é propagado aos owners downstream exatamente
como nas rotas REST — sem service token, sem elevação (F2a.R1).
AuthZ de negócio: ``engineering.access`` + ``principal_type=="user"``
aplicados aqui, idênticos às rotas /v1 — MCP não é autoridade.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Mapping

from mcp.types import CallToolResult

from delpi_auth.authz_core import has_any_permission
from delpi_mcp.errors import mcp_tool_result
from delpi_mcp.identity import (
    build_mcp_request as _shared_build_request,
)
from delpi_mcp.identity import (
    require_mcp_context,
)
from starlette.requests import Request

from engineering_app.application.eva.agent_intelligence_service import (
    EvaAgentIntelligenceService,
)
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.application.ports.overview_sources import OverviewQuery
from engineering_app.composition.home_composer import (
    build_get_engineering_home_use_case,
)
from engineering_app.composition.overview_composer import (
    build_get_engineering_overview_use_case,
)
from engineering_app.interface.mcp.branding import EVA_FULL_NAME
from engineering_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

logger = logging.getLogger(__name__)

ENGINEERING_ACCESS = "engineering.access"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPETENCE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

_TOOL_CONTRACT: dict[str, dict[str, Any]] = {
    "get_catalog": {
        "title": "Get catalog",
        "description": "Discovery catalog of the EVA tool surface.",
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
    },
    "get_engineering_home": {
        "title": "Get engineering home",
        "description": (
            "Authorized Engineering workspace — sections, attention items, "
            "tasks, requests and LMPs with per-source availability."
        ),
        "input_schema": {"type": "object", "properties": {}},
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/home",
    },
    "get_engineering_overview": {
        "title": "Get engineering overview",
        "description": (
            "Official six Engineering indicators (3 LMP + 3 TRANSFORMA+) "
            "with values, units, period, scope, provenance and owner-"
            "authorized goals/IDD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "end_date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "competence": {"type": "string", "pattern": "^\\d{4}-(0[1-9]|1[0-2])$"},
                "branch": {"type": "string"},
            },
        },
        "output_schema": {"type": "object"},
        "read_only": True,
        "required_permission": ENGINEERING_ACCESS,
        "source": "engineering-api GET /v1/overview",
    },
}

# Capacidades futuras — documentadas como não implementadas, nunca
# executáveis nem retornadas como tools.
_PLANNED_CAPABILITIES: tuple[dict[str, str], ...] = (
    {
        "name": "engineering_products",
        "status": "not_implemented",
        "note": "Produtos DELPI — sem contrato oficial ainda.",
    },
    {
        "name": "engineering_bom",
        "status": "not_implemented",
        "note": "BOM/roteiros — sem contrato oficial ainda.",
    },
    {
        "name": "engineering_documents",
        "status": "not_implemented",
        "note": "Desenhos/especificações/inspeções — sem contrato oficial.",
    },
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
    payload = {
        "success": False,
        "message": message,
        "status_code": status_code,
        "data": err_data,
    }
    return mcp_tool_result(payload, is_error=True)


def handle_tool_error(exc: Exception) -> CallToolResult:
    """Map adapter failures to honest typed results — never silent."""
    if isinstance(exc, PermissionError):
        msg = str(exc) or "Unauthorized"
        if msg == "Unauthorized":
            return _error_result(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        return _error_result(
            "Forbidden",
            status_code=403,
            error_code="forbidden",
            data={"error_kind": "authz"},
        )
    if isinstance(exc, TimeoutError):
        return _error_result(
            "Upstream timeout.",
            status_code=504,
            error_code="timeout",
        )
    if isinstance(exc, (ValueError, LookupError)) and not isinstance(
        exc, KeyError
    ):
        return _error_result(
            str(exc),
            status_code=400,
            error_code="validation",
            data={"error_kind": "validation"},
        )
    logger.exception("eva_mcp_tool_error")
    return _error_result(
        "Upstream service error.",
        status_code=502,
        error_code="upstream_error",
    )


def build_mcp_request() -> Request:
    """Rebuild the adapter Request from the delpi_auth-established context."""
    context = require_mcp_context()
    return _shared_build_request(
        context=context,
        server=("engineering-api", 443),
        client=("127.0.0.1", 0),
    )


def _require_engineering_human():
    """Same gate as the REST routes: human principal + effective permission.

    Raises PermissionError — mapped by ``handle_tool_error`` (401/403).
    """
    context = require_mcp_context()
    if not context.user or not context.authorization:
        raise PermissionError("Unauthorized")
    user = context.user
    if getattr(user, "principal_type", None) != "user":
        raise PermissionError("MCP tools require a human principal.")
    if not getattr(user, "is_superadmin", False) and not has_any_permission(
        user, [ENGINEERING_ACCESS]
    ):
        raise PermissionError("Forbidden")
    return context


def _source_context(context) -> HomeSourceContext:
    access_token = str(
        getattr(context.user, "access_token", "") or ""
    ).strip()
    if not access_token:
        header = context.authorization
        access_token = (
            header.split(" ", 1)[1].strip()
            if header.lower().startswith("bearer ")
            else ""
        )
    if not access_token:
        raise PermissionError("Unauthorized")
    return HomeSourceContext(
        user_id=str(getattr(context.user, "id", "") or ""),
        access_token=access_token,
        request_id=get_request_id(),
    )


# --- DISCOVERY ------------------------------------------------------------


def tool_get_catalog() -> CallToolResult:
    """EVA discovery catalog — live tools only; planning clearly marked."""
    try:
        _require_engineering_human()
        tools = []
        for name in MCP_TOOL_NAMES:
            contract = _TOOL_CONTRACT[name]
            tools.append(
                {
                    "name": name,
                    "title": contract["title"],
                    "description": contract["description"],
                    "capability_class": TOOL_CLASS[name],
                    "status": "implemented",
                    "input_schema": contract["input_schema"],
                    "output_schema": contract["output_schema"],
                    "read_only": contract["read_only"],
                    "required_permission": contract["required_permission"],
                    "source": contract.get("source"),
                    "owner": "engineering-api",
                }
            )
        data = {
            "assistant": EVA_FULL_NAME,
            "schema_version": "1.0",
            "tools": tools,
            "tool_class_legend": {
                "DISCOVERY": "Discovery only — never business data.",
                "READ": "Read-only official data — never persists.",
            },
            "write_tools": [],
            "agent_directives": (
                EvaAgentIntelligenceService.agent_directives()
            ),
            "planned_capabilities": list(_PLANNED_CAPABILITIES),
            "notes": [
                "EVA é somente leitura; não existem ferramentas de escrita.",
                "Disponibilidade por fonte é preservada — unavailable ou "
                "forbidden NÃO significa ausência de dados.",
                "Metas/IDD só existem nos indicadores elegíveis "
                "(lmp_on_time, transforma_gross_savings).",
                "Permissões declaradas são requisito, não concessão — a "
                "autorização efetiva é da Core e dos owners downstream.",
            ],
        }
        return _ok_result(data, "Catálogo de capacidades da EVA.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- READ tools -----------------------------------------------------------


async def tool_get_engineering_home() -> CallToolResult:
    try:
        context = _require_engineering_human()
        ctx = _source_context(context)
        home = await build_get_engineering_home_use_case().execute(ctx)
        return _ok_result(
            home.model_dump(),
            "Home de Engenharia autorizada do usuário.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def _validate_overview_filters(
    start_date: str | None,
    end_date: str | None,
    competence: str | None,
) -> str | None:
    """Mesma validação da rota REST — o MCP não inventa contrato."""
    for name, value in (
        ("start_date", start_date),
        ("end_date", end_date),
    ):
        if value is not None and not _ISO_DATE_RE.match(value.strip()):
            return f"{name} inválida — use YYYY-MM-DD."
    if (
        start_date
        and end_date
        and _ISO_DATE_RE.match(start_date.strip())
        and _ISO_DATE_RE.match(end_date.strip())
        and start_date.strip() > end_date.strip()
    ):
        return "start_date não pode ser posterior a end_date."
    if competence is not None and not _COMPETENCE_RE.match(
        competence.strip()
    ):
        return "competence inválida — use YYYY-MM."
    return None


async def tool_get_engineering_overview(
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    competence: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        context = _require_engineering_human()
        error = _validate_overview_filters(start_date, end_date, competence)
        if error:
            return _error_result(
                error,
                status_code=400,
                error_code="validation",
                data={"error_kind": "validation"},
            )
        ctx = _source_context(context)
        query = OverviewQuery(
            start_date=start_date.strip() if start_date else None,
            end_date=end_date.strip() if end_date else None,
            competence=competence.strip() if competence else None,
            branch=branch.strip() if branch else None,
        )
        overview = await build_get_engineering_overview_use_case().execute(
            ctx, query=query
        )
        return _ok_result(
            overview.model_dump(),
            "Visão geral oficial de Engenharia.",
        )
    except Exception as exc:
        return handle_tool_error(exc)
