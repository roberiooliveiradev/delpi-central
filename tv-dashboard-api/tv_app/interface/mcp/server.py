"""MCPServer for TV Dashboard (VISTA) — Streamable HTTP, stateless, JSON."""

from __future__ import annotations

import logging
import re
from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings

from delpi_mcp.tool_metadata import delpi_tool_meta, tool_annotations_payload
from delpi_mcp.transport import mcp_transport_security_settings
from mcp.types import CallToolResult, InputRequiredResult, ToolAnnotations

from tv_app.config import settings

from .branding import VISTA_MCP_INSTRUCTIONS
from .constants import MCP_TOOL_NAMES, TOOL_CLASS
from .oauth_contract import MCP_TOOL_SECURITY_SCHEMES
from .tool_bridge import (
    tool_analyze,
    tool_delete,
    tool_execute,
    tool_get_context,
    tool_knowledge,
    tool_read,
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
    return mcp_transport_security_settings(
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
    """Build the VISTA MCP server — the complete owner capability surface."""
    mcp = TvDashboardMCPServer(
        name="tv-dashboard",
        instructions=VISTA_MCP_INSTRUCTIONS,
        version="0.1.0",
    )

    _register_read_tools(mcp)
    return mcp


def _register_read_tools(mcp: MCPServer) -> None:
    # S5: shared annotation/meta vocabulary — wire semantics unchanged.
    ann = ToolAnnotations.model_validate(
        tool_annotations_payload(
            "READ — tv-dashboard",
            read_only=True,
            destructive=False,
            idempotent=True,
        )
    )
    ann_analysis = ToolAnnotations.model_validate(
        tool_annotations_payload(
            "ANALYSIS — tv-dashboard",
            read_only=True,
            destructive=False,
            idempotent=True,
        )
    )
    ann_prepare = ToolAnnotations.model_validate(
        tool_annotations_payload(
            "PREPARE — tv-dashboard",
            read_only=False,
            destructive=False,
            idempotent=True,
        )
    )
    ann_act = ToolAnnotations.model_validate(
        tool_annotations_payload(
            "ACT — tv-dashboard",
            read_only=False,
            destructive=True,
            idempotent=True,
        )
    )

    def _meta(name: str) -> dict:
        # `_meta` keys must be vendor-namespaced: bare `securitySchemes` is a
        # reserved key for the OpenAI connector (it parses the value as typed
        # OAuthSecurityScheme objects) and broke action discovery.
        return delpi_tool_meta(
            tool_class=TOOL_CLASS[name],
            security_schemes=MCP_TOOL_SECURITY_SCHEMES,
        )













    # ------------------------------------------------------------------
    # SEMANTIC_TOOLS_V1 — closed-vocabulary verbs over the same dispatch.
    # ------------------------------------------------------------------
    mcp.add_tool(
        tool_get_context,
        name="get_context",
        title="Contexto do especialista + capabilities efetivas",
        description=(
            "Contexto da VISTA: identidade do assistente, principal, "
            "capabilities efetivas do usuário autenticado (derivadas de "
            "autorização real — o catálogo informa, nunca concede), modelo "
            "de confirmação e catalogVersion. action=context (default) ou "
            "action=catalog para o catálogo canônico completo."
        ),
        annotations=ann,
        meta=_meta("get_context"),
    )

    mcp.add_tool(
        tool_read,
        name="read",
        title="Leitura semântica (vocabulário fechado)",
        description=(
            "Leitura por vocabulário fechado entity+action: "
            "playlist.list|get|context, playlist_history.history, "
            "data_route.search, data_model.inspect, product_guide.guide. "
            "filters aceita apenas chaves declaradas por ação — chave "
            "desconhecida falha tipada (VALIDATION_ERROR). "
            "Entidade/ação desconhecida → UNKNOWN_ENTITY/UNKNOWN_ACTION. "
            "Capabilities planejadas retornam NOT_IMPLEMENTED honesto."
        ),
        annotations=ann,
        meta=_meta("read"),
    )

    mcp.add_tool(
        tool_analyze,
        name="analyze",
        title="Análise semântica (nunca persiste)",
        description=(
            "Análises fechadas do owner: data_block_preview, "
            "data_model_preview, intent_materialization (intenção NL → "
            "ops tipadas candidatas). Nada persiste; resposta inclui "
            "evidenceClass (preview|calculation). Ops candidatas seguem "
            "para o envelope governado — nunca persistem por si."
        ),
        annotations=ann_analysis,
        meta=_meta("analyze"),
    )

    mcp.add_tool(
        tool_knowledge,
        name="knowledge",
        title="Conhecimento canônico de produto",
        description=(
            "Registro canônico de guias de produto "
            "(GUIDANCE_NOT_DOMAIN_TRUTH). action=get: um guia por topic "
            "(+section opcional); sem topic = índice. action=search: "
            "projeção limitada do índice filtrada por query. Nunca estado "
            "de domínio nem autorização."
        ),
        annotations=ann,
        meta=_meta("knowledge"),
    )

    mcp.add_tool(
        tool_execute,
        name="execute",
        title="Execução semântica — PREPARE→COMMIT canônico",
        description=(
            "entity=\"presentation\" action=\"apply_mutation\". Fase "
            "prepare: operations[] (typed ops do catálogo) + target → "
            "PREPARE (mesma pipeline de prepare_change — proposal_handle "
            "selado + consentChallenge quando policy=confirm). Fase "
            "commit: proposal_handle + idempotency_key + consent_artifact "
            "aprovado no canal humano confiável + target_echo. "
            "operations[] nunca é reenviado no commit (PLAN_MISMATCH); "
            "não existe booleano de confirmação nesta superfície — só o "
            "artifact prova consentimento humano."
        ),
        annotations=ann_act,
        meta=_meta("execute"),
    )

    mcp.add_tool(
        tool_delete,
        name="delete",
        title="Exclusão semântica — somente block|section|slide",
        description=(
            "Exclusão governada em duas fases. phase=prepare: entity ∈ "
            "{block,section,slide} + target (playlistId + id da entidade; "
            "deleteSlides opcional para section) → proposal selado + "
            "consentChallenge. phase=commit: proposal_handle + "
            "idempotency_key + consent_artifact aprovado no canal humano "
            "confiável + target_echo — sem booleano de confirmação nesta "
            "superfície."
        ),
        annotations=ann_act,
        meta=_meta("delete"),
    )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    assert registered == set(MCP_TOOL_NAMES), (
        f"MCP1 surface drift: registered={sorted(registered)} expected={sorted(MCP_TOOL_NAMES)}"
    )
