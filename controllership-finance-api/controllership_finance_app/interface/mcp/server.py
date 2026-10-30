"""CLARA MCPServer — superfície MCP do Portal Controladoria & Finanças.

CLARA-MCP-SEMANTIC-001 (doc 119): exatamente seis tools semânticas
estáveis — ``get_context``, ``read``, ``analyze``, ``knowledge``,
``execute``, ``delete``. Capacidades crescem via registry tipado
``(entity, action)`` em ``semantic_bridge``, nunca via novos nomes de
tool. Os handlers legados seguem em ``tool_bridge`` como alvos do
dispatcher (compatibilidade interna) — não são registrados no
``tools/list``: o único consumer externo (plugin ChatGPT) descobre a
superfície dinamicamente a cada sessão.

Tools declaradas com a taxonomia congelada `delpi_mcp`; metadata jamais
autoriza — cada handler reaplica `authorized_user`/`has_permission` e os
repositórios canônicos reaplicam as regras de negócio.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations
from pydantic import ConfigDict

from delpi_mcp.tool_metadata import (
    DELPI_META_TOOL_CLASS,
    security_schemes_meta,
    tool_annotations_payload,
)
from delpi_mcp.transport import mcp_transport_security_settings

from controllership_finance_app.interface.mcp.branding import (
    CLARA_MCP_INSTRUCTIONS,
)
from controllership_finance_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    TOOL_CLASS,
)
from controllership_finance_app.interface.mcp.oauth_contract import (
    CLARA_MCP_SECURITY_SCHEMES,
)
from controllership_finance_app.interface.mcp.resource_metadata import (
    public_host_allowed_for_mcp,
)
from controllership_finance_app.interface.mcp import tool_bridge as bridge
from controllership_finance_app.interface.mcp import semantic_bridge as semantic

logger = logging.getLogger(__name__)


class _ClaraWireTool(MCPTool):
    """Preserva ``securitySchemes`` top-level no wire (contrato do host)."""

    model_config = ConfigDict(extra="allow")


class ClaraMCPServer(MCPServer):
    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            meta[DELPI_META_TOOL_CLASS] = TOOL_CLASS.get(
                info.name, "ACT"
            )
            schemes = (
                meta.get("securitySchemes") or CLARA_MCP_SECURITY_SCHEMES
            )
            payload: dict[str, Any] = {
                "name": info.name,
                "title": info.title,
                "description": info.description or "",
                "inputSchema": info.parameters,
                "outputSchema": info.output_schema,
                "annotations": info.annotations,
                "icons": info.icons,
                "_meta": meta or None,
                "securitySchemes": schemes,
            }
            listed.append(_ClaraWireTool.model_validate(payload))
        return listed


def _annotations(tool_name: str, title: str) -> ToolAnnotations:
    kind = TOOL_CLASS.get(tool_name, "ACT")
    read_only = kind in {"DISCOVERY", "READ", "ANALYSIS"}
    destructive = tool_name in DESTRUCTIVE_ACT_TOOLS
    return ToolAnnotations.model_validate(
        tool_annotations_payload(
            title,
            read_only=read_only,
            destructive=destructive,
        )
    )


def clara_mcp_transport_security() -> TransportSecuritySettings:
    hosts, origins = public_host_allowed_for_mcp()
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_server() -> MCPServer:
    mcp = ClaraMCPServer(
        name="controllership-finance",
        instructions=CLARA_MCP_INSTRUCTIONS,
    )
    meta = security_schemes_meta(CLARA_MCP_SECURITY_SCHEMES)

    def _guarded(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                return bridge.handle_tool_error(exc)

        return wrapper

    # --- Superfície semântica estável (doc 119): seis tools ----------

    @mcp.tool(
        name="get_context",
        title="Get context",
        description=(
            "Discovery e contexto da CLARA: ator autenticado e "
            "capacidades efetivas (topic='actor'), catálogo "
            "versionado de ações (entity, action) com gates "
            "(topic='catalog'), contrato JSON de uma action "
            "(topic='schema' + entity/action), persona/diretivas "
            "(topic='persona'). Chame antes de qualquer read/"
            "execute para descobrir ações e parâmetros."
        ),
        annotations=_annotations("get_context", "Get context"),
        meta=meta,
    )
    def get_context(
        topic: str | None = None,
        entity: str | None = None,
        action: str | None = None,
        scope: str | None = None,
        selected_ref: str | None = None,
    ) -> CallToolResult:
        return _guarded(semantic.tool_get_context)(
            topic, entity, action, scope, selected_ref
        )

    @mcp.tool(
        name="read",
        title="Read",
        description=(
            "Consultas e listagens com paridade 1:1 ao Portal "
            "(entity + action do catálogo). Ex.: entity='pendency', "
            "action='list', period='2026-09'; entity='report', "
            "action='stock_inventory'; entity='document', "
            "action='get', ref='<document_id>'. Mesmo usuário + "
            "mesmos parâmetros = mesmo resultado autorizado. Nunca "
            "responde de memória — sempre com dado do owner."
        ),
        annotations=_annotations("read", "Read"),
        meta=meta,
    )
    def read(
        entity: str,
        action: str,
        ref: str | None = None,
        period: str | None = None,
        filters: dict[str, Any] | None = None,
        page: int | None = None,
        page_size: int | None = None,
        projection: str | None = None,
    ) -> CallToolResult:
        return _guarded(semantic.tool_read)(
            entity, action, ref, period, filters, page,
            page_size, projection,
        )

    @mcp.tool(
        name="analyze",
        title="Analyze",
        description=(
            "Análises estruturadas sobre dados reais "
            "(analysis_type='closing_blockers': achados rotulados "
            "FACT vs RECOMMENDATION — nunca regra nova). Escopo "
            "explícito por period/filters."
        ),
        annotations=_annotations("analyze", "Analyze"),
        meta=meta,
    )
    def analyze(
        analysis_type: str,
        period: str | None = None,
        refs: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        question: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> CallToolResult:
        return _guarded(semantic.tool_analyze)(
            analysis_type, period, refs, filters, question,
            parameters,
        )

    @mcp.tool(
        name="knowledge",
        title="Knowledge",
        description=(
            "Base de conhecimento PROC-0072: action='search' "
            "(query/topic/report_id → itens com citações "
            "verificáveis: fonte, locator, classificação de "
            "evidência), action='get' (item completo por "
            "knowledge_id), action='sources' (inventário de fontes "
            "e versão do corpus). Distinguir PROVEN, "
            "OWNER_REPORTED, TO_INVENTORY e TARGET."
        ),
        annotations=_annotations("knowledge", "Knowledge"),
        meta=meta,
    )
    def knowledge(
        action: str,
        query: str | None = None,
        topic: str | None = None,
        report_id: str | None = None,
        business_step: str | None = None,
        knowledge_id: str | None = None,
        limit: int | None = None,
    ) -> CallToolResult:
        return _guarded(semantic.tool_knowledge)(
            action, query, topic, report_id, business_step,
            knowledge_id, limit,
        )

    @mcp.tool(
        name="execute",
        title="Execute",
        description=(
            "Operações de escrita governadas (entity + action do "
            "catálogo, ex.: entity='pendency', action='create', "
            "params={...}). Fluxo obrigatório: phase='prepare' sela "
            "a operação e devolve confirmation_url → o usuário "
            "consente no Portal com credencial fresca → "
            "phase='commit' com o proposal_handle exato. Um 'sim' "
            "digitado no chat NÃO é consentimento. Multi-ação: "
            "arg 'batch' {phase, operations:[{entity, action, "
            "params, depends_on?}], batch_handle, plan_hash} — uma "
            "confirmação consolidada cobre o plano inteiro. "
            "Revalida permissão efetiva, escopo, staleness, "
            "idempotência e pós-condição por read-back."
        ),
        annotations=_annotations("execute", "Execute"),
        meta=meta,
    )
    def execute(
        entity: str | None = None,
        action: str | None = None,
        params: dict[str, Any] | None = None,
        phase: str | None = None,
        proposal_handle: str | None = None,
        idempotency_key: str | None = None,
        expected_revision: int | None = None,
        batch: dict[str, Any] | None = None,
    ) -> CallToolResult:
        return _guarded(semantic.tool_execute)(
            entity, action, params, phase, proposal_handle,
            idempotency_key, expected_revision, batch,
        )

    @mcp.tool(
        name="delete",
        title="Delete",
        description=(
            "Operações destrutivas/irreversíveis do catálogo "
            "(entity + action marcadas destructive; ex.: "
            "entity='document', action='cancel', "
            "target_ref='<document_id>'). Mesmo fluxo governado: "
            "phase='prepare' expõe exatamente o objeto e a "
            "consequência → confirmação humana explícita no Portal "
            "→ phase='commit' com o proposal_handle. Nunca executa "
            "com 'confirmed=true' do modelo."
        ),
        annotations=_annotations("delete", "Delete"),
        meta=meta,
    )
    def delete(
        entity: str | None = None,
        action: str | None = None,
        target_ref: str | None = None,
        params: dict[str, Any] | None = None,
        phase: str | None = None,
        proposal_handle: str | None = None,
        expected_revision: int | None = None,
    ) -> CallToolResult:
        return _guarded(semantic.tool_delete)(
            entity, action, target_ref, params, phase,
            proposal_handle, expected_revision,
        )

    return mcp


clara_mcp_server = create_mcp_server()
