"""CLARA MCPServer — superfície MCP do Portal Controladoria & Finanças.

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

    @mcp.tool(
        name="get_my_context",
        title="Get my context",
        description=(
            "Contexto mínimo do usuário autenticado (capacidades e "
            "grupos). Identidade — nunca autorização adicional."
        ),
        annotations=_annotations("get_my_context", "Get my context"),
        meta=meta,
    )
    def get_my_context() -> CallToolResult:
        return _guarded(bridge.tool_get_my_context)()

    @mcp.tool(
        name="get_catalog",
        title="Get catalog",
        description=(
            "Discovery: tools disponíveis ao usuário, operações "
            "governadas (PREPARE→ACT), versão do corpus e diretivas."
        ),
        annotations=_annotations("get_catalog", "Get catalog"),
        meta=meta,
    )
    def get_catalog() -> CallToolResult:
        return _guarded(bridge.tool_get_catalog)()

    @mcp.tool(
        name="get_competence_state",
        title="Get competence closing state",
        description=(
            "Estado derivado do fechamento mensal da competência "
            "(blockers, rejeição terminal, readiness) — mesmo contrato "
            "de GET /closing/competences/{period}/monthly-state."
        ),
        annotations=_annotations(
            "get_competence_state", "Get competence state"
        ),
        meta=meta,
    )
    def get_competence_state(period: str) -> CallToolResult:
        return _guarded(bridge.tool_get_competence_state)(period)

    @mcp.tool(
        name="get_checklist_items",
        title="Get checklist items",
        description=(
            "Itens do checklist da competência com estado, área "
            "destinatária e escopo — paridade com a listagem do Portal."
        ),
        annotations=_annotations(
            "get_checklist_items", "Get checklist items"
        ),
        meta=meta,
    )
    def get_checklist_items(
        period: str,
        sheet: str | None = None,
        recipient_area: str | None = None,
        state: str | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_checklist_items)(
            period, sheet, recipient_area, state
        )

    @mcp.tool(
        name="list_documents",
        title="List competence documents",
        description=(
            "Documentos/evidências da competência (metadados, estado, "
            "vínculo com item) — paridade com a listagem do Portal."
        ),
        annotations=_annotations("list_documents", "List documents"),
        meta=meta,
    )
    def list_documents(
        period: str,
        snapshot_item_id: str | None = None,
        state: str | None = None,
        branch_scope: str | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_list_documents)(
            period, snapshot_item_id, state, branch_scope
        )

    @mcp.tool(
        name="get_p3_reconciliation",
        title="Get P3 reconciliation state",
        description=(
            "Estado P3: cutoff, revalidação vigente, sources e "
            "conciliação por domínio — o owner entrega os números; a "
            "CLARA não recalcula divergências."
        ),
        annotations=_annotations(
            "get_p3_reconciliation", "Get P3 reconciliation"
        ),
        meta=meta,
    )
    def get_p3_reconciliation(period: str) -> CallToolResult:
        return _guarded(bridge.tool_get_p3_reconciliation)(period)

    @mcp.tool(
        name="list_pendencies",
        title="List closing pendencies",
        description=(
            "Pendências da competência com estado, responsável e "
            "classificação — paridade com a listagem do Portal."
        ),
        annotations=_annotations("list_pendencies", "List pendencies"),
        meta=meta,
    )
    def list_pendencies(
        period: str,
        state: str | None = None,
        kind: str | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_list_pendencies)(period, state, kind)

    @mcp.tool(
        name="get_package_review",
        title="Get package review state",
        description=(
            "Pacotes da competência visíveis ao usuário: versões, "
            "assignments, decisões e esclarecimentos — mesmo escopo de "
            "visibilidade do Portal."
        ),
        annotations=_annotations(
            "get_package_review", "Get package review"
        ),
        meta=meta,
    )
    def get_package_review(period: str) -> CallToolResult:
        return _guarded(bridge.tool_get_package_review)(period)

    @mcp.tool(
        name="analyze_closing_blockers",
        title="Analyze closing blockers",
        description=(
            "Análise estruturada do que impede a conclusão da "
            "competência: achados rotulados FACT (dado do owner) vs "
            "RECOMMENDATION (orientação) — nunca regra nova."
        ),
        annotations=_annotations(
            "analyze_closing_blockers", "Analyze closing blockers"
        ),
        meta=meta,
    )
    def analyze_closing_blockers(period: str) -> CallToolResult:
        return _guarded(bridge.tool_analyze_closing_blockers)(period)

    @mcp.tool(
        name="search_closing_knowledge",
        title="Search closing knowledge base",
        description=(
            "Busca na base de conhecimento PROC-0072 com citações "
            "verificáveis (fonte, locator, classificação de evidência) "
            "— processo, vídeo, rotinas TOTVS, relatórios R01–R15, "
            "regras e histórico de decisões."
        ),
        annotations=_annotations(
            "search_closing_knowledge", "Search closing knowledge"
        ),
        meta=meta,
    )
    def search_closing_knowledge(
        query: str | None = None,
        topic: str | None = None,
        business_step: str | None = None,
        report_id: str | None = None,
        limit: int = 8,
    ) -> CallToolResult:
        return _guarded(bridge.tool_search_closing_knowledge)(
            query, topic, business_step, report_id, limit
        )

    @mcp.tool(
        name="get_knowledge_item",
        title="Get knowledge item",
        description=(
            "Item completo da base de conhecimento com conteúdo, "
            "metadados de proveniência e locator de citação."
        ),
        annotations=_annotations(
            "get_knowledge_item", "Get knowledge item"
        ),
        meta=meta,
    )
    def get_knowledge_item(knowledge_id: str) -> CallToolResult:
        return _guarded(bridge.tool_get_knowledge_item)(knowledge_id)

    @mcp.tool(
        name="list_knowledge_sources",
        title="List knowledge sources",
        description=(
            "Inventário das fontes do corpus (tipo, versão, hash, "
            "autoridade) e versão publicada do corpus."
        ),
        annotations=_annotations(
            "list_knowledge_sources", "List knowledge sources"
        ),
        meta=meta,
    )
    def list_knowledge_sources() -> CallToolResult:
        return _guarded(bridge.tool_list_knowledge_sources)()

    @mcp.tool(
        name="prepare_governed_operation",
        title="Prepare governed operation",
        description=(
            "PREPARE de operação governada (capability + params): sela "
            "a operação exata, o estado esperado e a expiração — sem "
            "efeito colateral. Exige confirmação humana explícita antes "
            "de commit_proposal."
        ),
        annotations=_annotations(
            "prepare_governed_operation", "Prepare governed operation"
        ),
        meta=meta,
    )
    def prepare_governed_operation(
        capability: str, params: dict[str, Any]
    ) -> CallToolResult:
        return _guarded(bridge.tool_prepare_governed_operation)(
            capability, params
        )

    @mcp.tool(
        name="commit_proposal",
        title="Commit prepared proposal",
        description=(
            "ACT: executa a proposta selada após confirmação explícita "
            "do usuário. Revalida ator, expiração, estado selado e as "
            "regras da BFF; audita canal mcp/clara e verifica a "
            "pós-condição real."
        ),
        annotations=_annotations("commit_proposal", "Commit proposal"),
        meta=meta,
    )
    def commit_proposal(proposal_handle: str) -> CallToolResult:
        return _guarded(bridge.tool_commit_proposal)(proposal_handle)

    return mcp


clara_mcp_server = create_mcp_server()
