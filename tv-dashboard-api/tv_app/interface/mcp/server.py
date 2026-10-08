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
    tool_commit_proposal,
    tool_get_catalog,
    tool_get_playlist_context,
    tool_get_product_guide,
    tool_inspect_data_model,
    tool_list_playlists,
    tool_prepare_change,
    tool_preview_data_block,
    tool_preview_data_model,
    tool_search_data_routes,
    tool_suggest_change,
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
            "renderização. Opcionalmente foca uma fonte de dados legada "
            "(data_source_id): devolve o transform persistido, dependências, "
            "consumidores e — com include_runtime=true — effectiveParams e "
            "resultado do runtime. Cada tela inclui designAudit (issues de "
            "layout detectadas pelo owner: cobertura de frame, sobreposição, "
            "contraste, tipografia, safe-area) — use para revisar qualidade "
            "antes/depois de mutações. Requer playlist_id e permissão de "
            "leitura sobre a programação."
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
        tool_preview_data_block,
        name="preview_data_block",
        title="Análise de bloco de dados (não persiste)",
        description=(
            "ANALYSIS do owner sobre um bloco de dados — nunca persiste. "
            "Retorna semanticDigest (colunas/métricas/filtros resolvidos), "
            "visualRecommendation (tipo de bloco/família de gráfico adequada "
            "aos dados), joinHints, formatHints e erro tipado quando a "
            "resolução/transform falha (nunca dataset vazio disfarçado). "
            "Três formas de alvo: (a) playlist_id+slide_id+block_id para "
            "bloco persistido; (b) operation_id+params para bloco hipotético "
            "derivado de rota; (c) block(+native_config) para candidato "
            "inline. Use ANTES de prepare_change para entender o que o bloco "
            "mostra e se o tratamento visual cabe nos dados."
        ),
        annotations=ann_analysis,
        meta=_meta("preview_data_block"),
    )

    mcp.add_tool(
        tool_get_product_guide,
        name="get_product_guide",
        title="Guia de produto (como/quando usar)",
        description=(
            "Lê o registro canônico de orientação de produto do TV Dashboard "
            "(GUIDANCE_NOT_DOMAIN_TRUTH). Sem topic: índice de tópicos. Com "
            "topic (+section opcional): um guia. Orientação apenas — o "
            "catálogo vivo, leituras de domínio e contratos api-delpi/OpenAPI "
            "sempre prevalecem sobre o texto do guia."
        ),
        annotations=ann,
        meta=_meta("get_product_guide"),
    )

    mcp.add_tool(
        tool_suggest_change,
        name="suggest_change",
        title="ANALYSIS — interpretar intenção em ops tipadas",
        description=(
            "ANALYSIS do owner sobre uma intenção em linguagem natural — "
            "nunca persiste e não concede autorização. Interpreta o pedido "
            "contra o host_context fornecido (playlistId, slideId, "
            "selectedBlockIds, nativeConfig, dataModels...) e retorna o "
            "plano discriminado do materializador canônico: status "
            "(ready/clarification/selection_pending/unsupported/"
            "not_command), ops[] tipadas candidatas, confirmationPolicy, "
            "risk, candidates e reason. Use ANTES de prepare_change para "
            "transformar intenção em ops do catálogo; ops candidatas devem "
            "seguir para prepare_change — nunca persistem por si."
        ),
        annotations=ann_analysis,
        meta=_meta("suggest_change"),
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
            "Exige proposal_handle exato e idempotency_key do chamador. "
            "confirmation=true é exigido apenas quando a proposta declara "
            "confirmação explícita (confirmationPolicy=confirm / "
            "destructive); propostas direct commitam sem confirmação. "
            "O postcondition é verificado pelo "
            "backend (VERIFIED / OUTCOME_NOT_VERIFIED)."
        ),
        annotations=ann_act,
        meta=_meta("commit_proposal"),
    )

    registered = {t.name for t in mcp._tool_manager.list_tools()}
    assert registered == set(MCP_TOOL_NAMES), (
        f"MCP1 surface drift: registered={sorted(registered)} expected={sorted(MCP_TOOL_NAMES)}"
    )
