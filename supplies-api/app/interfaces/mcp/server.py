"""SURI MCPServer — conversational surface of Portal Suprimentos.

Semantic contract freeze rev.2: exactly four tools
(``get_context``, ``read``, ``analyze``, ``knowledge``) dispatching to
specialized handlers. Tools are declared with the frozen ``delpi_mcp``
taxonomy; metadata never authorizes — each handler re-applies the same
policies the Flask BFF routes use (``can_use_operations``/``require_units``
+ Core-derived EffectiveUser).
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from delpi_mcp.tool_metadata import (
    DELPI_META_TOOL_CLASS,
    security_schemes_meta,
    tool_annotations_payload,
)
from delpi_mcp.transport import mcp_transport_security_settings
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, Tool as MCPTool, ToolAnnotations
from pydantic import ConfigDict

from app.interfaces.mcp import tool_bridge as bridge
from app.interfaces.mcp.branding import SURI_MCP_INSTRUCTIONS
from app.interfaces.mcp.constants import DESTRUCTIVE_ACT_TOOLS, TOOL_CLASS
from app.interfaces.mcp.oauth_contract import SURI_MCP_SECURITY_SCHEMES
from app.interfaces.mcp.resource_metadata import public_host_allowed_for_mcp
from app.interfaces.mcp.schemas import (
    PurchaseOrderAnalyzeFilters,
    PurchaseOrderIdentity,
    PurchaseOrderSearchFilters,
)

logger = logging.getLogger(__name__)


class _SuriWireTool(MCPTool):
    """Preserves top-level ``securitySchemes`` on the wire (host contract)."""

    model_config = ConfigDict(extra="allow")


class SuriMCPServer(MCPServer):
    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            meta[DELPI_META_TOOL_CLASS] = TOOL_CLASS.get(info.name, "READ")
            schemes = meta.get("securitySchemes") or SURI_MCP_SECURITY_SCHEMES
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
            listed.append(_SuriWireTool.model_validate(payload))
        return listed


def _annotations(tool_name: str, title: str) -> ToolAnnotations:
    kind = TOOL_CLASS.get(tool_name, "READ")
    read_only = kind in {"DISCOVERY", "READ", "ANALYSIS"}
    destructive = tool_name in DESTRUCTIVE_ACT_TOOLS
    return ToolAnnotations.model_validate(
        tool_annotations_payload(
            title,
            read_only=read_only,
            destructive=destructive,
        )
    )


def suri_mcp_transport_security() -> TransportSecuritySettings:
    hosts, origins = public_host_allowed_for_mcp()
    return mcp_transport_security_settings(
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def create_mcp_server() -> MCPServer:
    mcp = SuriMCPServer(
        name="supplies",
        instructions=SURI_MCP_INSTRUCTIONS,
    )
    meta = security_schemes_meta(SURI_MCP_SECURITY_SCHEMES)

    def _guarded(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                return bridge.handle_tool_error(exc)

        return wrapper

    @mcp.tool(
        name="get_context",
        title="Get context and capability catalog",
        description=(
            "Ponto de entrada da SURI. action=context: identidade e "
            "capacidades efetivas do usuário autenticado (unidades "
            "permitidas, flags declarativas). action=catalog: catálogo "
            "semântico de capabilities realmente implementadas — tools, "
            "entidades/ações/análises permitidas, limites e diretrizes."
        ),
        annotations=_annotations("get_context", "Get context and catalog"),
        meta=meta,
    )
    def get_context(
        action: Literal["context", "catalog"] = "context",
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_context)(action)

    @mcp.tool(
        name="read",
        title="Read supplies entities",
        description=(
            "Consulta semântica de entidades de Suprimentos. "
            "entity=purchase_orders: action=search lista linhas de "
            "pedidos em aberto via 'filters' fechados (branch "
            "obrigatória, order_number, product_code, supplier_code, "
            "expected_delivery_from/to, late_only, sort_by/dir, "
            "page/page_size); action=get retorna a ficha de um pedido "
            "via 'identity' {branch, order_number}. Requer "
            "supplies.access e escopo de unidade do próprio usuário."
        ),
        annotations=_annotations("read", "Read supplies entities"),
        meta=meta,
    )
    def read(
        entity: Literal["purchase_orders"],
        action: Literal["search", "get"],
        filters: PurchaseOrderSearchFilters | None = None,
        identity: PurchaseOrderIdentity | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_read)(entity, action, filters, identity)

    @mcp.tool(
        name="analyze",
        title="Analyze supplies data",
        description=(
            "Análises determinísticas homologadas. "
            "analysis=purchase_orders_summary: fatos do contrato do "
            "owner (summary), cálculos reproduzíveis sobre a amostra e "
            "recomendações rotuladas FACT/CALCULATION/RECOMMENDATION — "
            "recomendações nunca executam. 'filters' aceita o mesmo "
            "vocabulário fechado do read (sem sort/page); 'sample_size' "
            "limita a amostra."
        ),
        annotations=_annotations("analyze", "Analyze supplies data"),
        meta=meta,
    )
    def analyze(
        analysis: Literal["purchase_orders_summary"],
        filters: PurchaseOrderAnalyzeFilters | None = None,
        sample_size: int = 50,
    ) -> CallToolResult:
        return _guarded(bridge.tool_analyze)(analysis, filters, sample_size)

    @mcp.tool(
        name="knowledge",
        title="Supplies knowledge and guidance",
        description=(
            "Conhecimento governado do Portal Suprimentos com citações "
            "verificáveis (fonte, locator, classificação de evidência). "
            "action=search: busca por 'query'/'topic' (limit); "
            "action=get: item completo por 'knowledge_id'; "
            "action=sources: inventário das fontes do corpus."
        ),
        annotations=_annotations(
            "knowledge", "Supplies knowledge and guidance"
        ),
        meta=meta,
    )
    def knowledge(
        action: Literal["search", "get", "sources"],
        query: str | None = None,
        topic: str | None = None,
        knowledge_id: str | None = None,
        limit: int = 8,
    ) -> CallToolResult:
        return _guarded(bridge.tool_knowledge)(
            action, query, topic, knowledge_id, limit
        )

    return mcp


suri_mcp_server = create_mcp_server()
