"""MCPServer for TV Dashboard (VISTA) — Streamable HTTP, stateless, JSON."""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, InputRequiredResult, ToolAnnotations

from tv_app.config import settings

from .branding import VISTA_MCP_INSTRUCTIONS
from .constants import MCP_TOOL_NAMES, TOOL_CLASS
from .oauth_contract import MCP_TOOL_SECURITY_SCHEMES
from .tool_bridge import (
    tool_commit_proposal,
    tool_get_catalog,
    tool_get_playlist_context,
    tool_inspect_data_model,
    tool_list_playlists,
    tool_prepare_change,
    tool_preview_data_model,
    tool_search_data_routes,
)

logger = logging.getLogger(__name__)


def _mcp_allowed_hosts() -> list[str]:
    env = (settings.TV_MCP_ALLOWED_HOSTS or "").strip()
    if env:
        return [h.strip() for h in env.split(",") if h.strip()]
    return [
        "minhadelpi.com.br",
        "*.minhadelpi.com.br",
        "localhost",
        "127.0.0.1",
        "localhost:*",
        "127.0.0.1:*",
    ]


def _mcp_allowed_origins() -> list[str]:
    env = (settings.TV_MCP_ALLOWED_ORIGINS or "").strip()
    if env:
        return [o.strip() for o in env.split(",") if o.strip()]
    return [
        "https://minhadelpi.com.br",
        "https://*.minhadelpi.com.br",
        "http://localhost:*",
        "http://127.0.0.1:*",
        "https://localhost:*",
        "https://127.0.0.1:*",
    ]


def mcp_transport_security() -> TransportSecuritySettings:
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_mcp_allowed_hosts(),
        allowed_origins=_mcp_allowed_origins(),
    )


class TvDashboardMCPServer(MCPServer):
    """Preserve domain/contract error codes on the transport path.

    Tool fns already return typed CallToolResult errors; this subclass only
    guards the SDK-level unexpected-tool-error path so codes embedded in
    domain exception messages survive without leaking internals.
    """

    _CODE_RE = re.compile(r"^[a-z_]+(?:\.[a-z_]+)+$|^INVALID_CHANGE$|^QUERY_REQUIRED$")

    async def call_tool(
        self, name: str, arguments: dict[str, Any], context: Any = None
    ) -> CallToolResult | InputRequiredResult:
        try:
            return await super().call_tool(name, arguments, context)
        except ToolError:
            # Protocol-level failure (e.g. unknown tool) — let the SDK emit
            # the canonical JSON-RPC error instead of an app-level envelope.
            raise
        except Exception as e:
            msg = str(e)
            if self._CODE_RE.match(msg.split(":")[0].strip()):
                logger.warning("mcp tool %s domain error: %s", name, msg.split(":")[0])
                return CallToolResult(
                    is_error=True,
                    content=[],
                    structured_content={
                        "status": "error",
                        "code": msg.split(":")[0].strip(),
                        "message": msg,
                    },
                )
            logger.exception("mcp tool %s failed: %s", name, type(e).__name__)
            return CallToolResult(
                is_error=True,
                content=[],
                structured_content={
                    "status": "error",
                    "code": "INTERNAL_ERROR",
                    "message": "Falha interna na tool.",
                },
            )


def create_mcp_server() -> MCPServer:
    """Build the VISTA MCP server — exactly eight semantic tools."""
    mcp = TvDashboardMCPServer(
        name="tv-dashboard",
        instructions=VISTA_MCP_INSTRUCTIONS,
    )

    _register_read_tools(mcp)
    return mcp


def _register_read_tools(mcp: MCPServer) -> None:
    ann = ToolAnnotations(
        title="READ — tv-dashboard",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
    ann_prepare = ToolAnnotations(
        title="PREPARE — tv-dashboard",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False,
    )
    ann_act = ToolAnnotations(
        title="ACT — tv-dashboard",
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=True,
        open_world_hint=False,
    )

    def _meta(name: str) -> dict:
        return {
            "securitySchemes": list(MCP_TOOL_SECURITY_SCHEMES),
            "toolClass": TOOL_CLASS[name],
        }

    mcp.add_tool(
        tool_list_playlists,
        name="list_playlists",
        title="Listar programações do usuário",
        description=(
            "Lista as programações (playlists) do TV Dashboard visíveis ao "
            "usuário autenticado, com paginação. Ponto de partida para "
            "descobrir playlist_id canônico."
        ),
        annotations=ann,
        meta=_meta("list_playlists"),
    )

    mcp.add_tool(
        tool_get_playlist_context,
        name="get_playlist_context",
        title="Contexto estrutural da programação",
        description=(
            "Retorna o contexto compacto de uma programação: identidade, "
            "telas, blocos, filtros e revisão — sem conteúdo pesado de "
            "renderização. Requer playlist_id e permissão de leitura sobre a "
            "programação."
        ),
        annotations=ann,
        meta=_meta("get_playlist_context"),
    )

    mcp.add_tool(
        tool_get_catalog,
        name="get_catalog",
        title="Catálogo canônico de operações",
        description=(
            "Retorna o catálogo canônico de capacidades/operações do TV "
            "Dashboard (vocabulary para futuras mutações via envelope "
            "PREPARE/ACT) e formatos de exibição suportados."
        ),
        annotations=ann,
        meta=_meta("get_catalog"),
    )

    mcp.add_tool(
        tool_search_data_routes,
        name="search_data_routes",
        title="Descobrir rotas de dados DELPI",
        description=(
            "Busca semântica nas rotas de dados DELPI permitidas (campos, "
            "parâmetros, operações autorizadas). Somente descoberta — a tool "
            "não executa a rota encontrada."
        ),
        annotations=ann,
        meta=_meta("search_data_routes"),
    )

    mcp.add_tool(
        tool_inspect_data_model,
        name="inspect_data_model",
        title="Inspecionar DataModel persistido",
        description=(
            "Inspeciona um DataModel persistido em uma tela: definição, "
            "inputs, transform, outputSchema, consumidores e estado de "
            "runtime. model_id é apenas referência — não concede permissão."
        ),
        annotations=ann,
        meta=_meta("inspect_data_model"),
    )

    mcp.add_tool(
        tool_preview_data_model,
        name="preview_data_model",
        title="Preview de DataModel sem persistir",
        description=(
            "Executa o runtime de um DataModel — persistido (model_id) ou "
            "candidato inline (model) — e retorna linhas/colunas calculadas. "
            "Não grava nada: nenhum candidato é persistido e a revisão da "
            "programação não muda."
        ),
        annotations=ann,
        meta=_meta("preview_data_model"),
    )

    mcp.add_tool(
        tool_prepare_change,
        name="prepare_change",
        title="PREPARE — candidato de mutação governado",
        description=(
            "Avalia um candidato de mutação governado (target + ops[] do "
            "catálogo canônico) sem persistir. Retorna proposal_handle opaco, "
            "canCommit, risk, confirmationPolicy e diff/candidate preview. "
            "Nada é gravado — commit só via commit_proposal."
        ),
        annotations=ann_prepare,
        meta=_meta("prepare_change"),
    )

    mcp.add_tool(
        tool_commit_proposal,
        name="commit_proposal",
        title="ACT — commit de proposta validada",
        description=(
            "Executa o commit de uma proposta retornada por prepare_change. "
            "Exige proposal_handle exato, idempotency_key do chamador e "
            "confirmation=true explícito. O postcondition é verificado pelo "
            "backend (VERIFIED / OUTCOME_NOT_VERIFIED)."
        ),
        annotations=ann_act,
        meta=_meta("commit_proposal"),
    )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    assert registered == set(MCP_TOOL_NAMES), (
        f"MCP1 surface drift: registered={sorted(registered)} expected={sorted(MCP_TOOL_NAMES)}"
    )
