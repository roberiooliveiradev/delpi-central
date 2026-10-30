"""SURI MCPServer — conversational surface of Portal Suprimentos.

Tools declared with the frozen ``delpi_mcp`` taxonomy; metadata never
authorizes — each handler re-applies the same policies the Flask BFF
routes use (``can_use_operations``/``require_units`` + Core-derived
EffectiveUser).
"""

from __future__ import annotations

import logging
from typing import Any

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
        name="get_my_context",
        title="Get my context",
        description=(
            "Contexto mínimo do usuário autenticado (capacidades "
            "declarativas e unidades permitidas). Identidade — nunca "
            "autorização adicional."
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
            "Discovery: tools realmente implementadas, classes, versão "
            "do catálogo e diretrizes de uso da SURI."
        ),
        annotations=_annotations("get_catalog", "Get catalog"),
        meta=meta,
    )
    def get_catalog() -> CallToolResult:
        return _guarded(bridge.tool_get_catalog)()

    @mcp.tool(
        name="list_purchase_orders",
        title="List open purchase orders",
        description=(
            "Linhas de pedidos de compra em aberto (SC7) por unidade "
            "obrigatória — paridade com a lista do Portal. Requer "
            "supplies.access e escopo de unidade do próprio usuário."
        ),
        annotations=_annotations(
            "list_purchase_orders", "List open purchase orders"
        ),
        meta=meta,
    )
    def list_purchase_orders(
        branch: list[str],
        order_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        expected_delivery_from: str | None = None,
        expected_delivery_to: str | None = None,
        late_only: bool = False,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> CallToolResult:
        return _guarded(bridge.tool_list_purchase_orders)(
            branch,
            order_number,
            product_code,
            supplier_code,
            expected_delivery_from,
            expected_delivery_to,
            late_only,
            sort_by,
            sort_dir,
            page,
            page_size,
        )

    @mcp.tool(
        name="get_purchase_order",
        title="Get purchase order detail",
        description=(
            "Ficha de um pedido de compra em aberto (itens e "
            "recebimentos) — paridade com o detalhe do Portal."
        ),
        annotations=_annotations(
            "get_purchase_order", "Get purchase order detail"
        ),
        meta=meta,
    )
    def get_purchase_order(
        branch: str, order_number: str
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_purchase_order)(
            branch, order_number
        )

    @mcp.tool(
        name="search_supplies_knowledge",
        title="Search supplies knowledge base",
        description=(
            "Busca no corpus governado da SURI (manual oficial do "
            "Portal Suprimentos) com citações verificáveis — fonte, "
            "locator e classificação de evidência."
        ),
        annotations=_annotations(
            "search_supplies_knowledge", "Search supplies knowledge base"
        ),
        meta=meta,
    )
    def search_supplies_knowledge(
        query: str | None = None,
        topic: str | None = None,
        limit: int = 8,
    ) -> CallToolResult:
        return _guarded(bridge.tool_search_supplies_knowledge)(
            query, topic, limit
        )

    @mcp.tool(
        name="get_knowledge_item",
        title="Get knowledge item",
        description=(
            "Item completo do corpus com conteúdo, proveniência e "
            "locator de citação."
        ),
        annotations=_annotations("get_knowledge_item", "Get knowledge item"),
        meta=meta,
    )
    def get_knowledge_item(knowledge_id: str) -> CallToolResult:
        return _guarded(bridge.tool_get_knowledge_item)(knowledge_id)

    @mcp.tool(
        name="list_knowledge_sources",
        title="List knowledge sources",
        description=(
            "Inventário das fontes do corpus (tipo, versão, hash, "
            "autoridade) e versão publicada."
        ),
        annotations=_annotations(
            "list_knowledge_sources", "List knowledge sources"
        ),
        meta=meta,
    )
    def list_knowledge_sources() -> CallToolResult:
        return _guarded(bridge.tool_list_knowledge_sources)()

    @mcp.tool(
        name="analyze_purchase_orders",
        title="Analyze open purchase orders",
        description=(
            "Análise determinística das linhas em aberto: fatos do "
            "owner (summary do contrato), cálculos reproduzíveis sobre "
            "a amostra e recomendações rotuladas — nunca ações."
        ),
        annotations=_annotations(
            "analyze_purchase_orders", "Analyze open purchase orders"
        ),
        meta=meta,
    )
    def analyze_purchase_orders(
        branch: list[str],
        order_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        expected_delivery_from: str | None = None,
        expected_delivery_to: str | None = None,
        late_only: bool = False,
        sample_size: int = 50,
    ) -> CallToolResult:
        return _guarded(bridge.tool_analyze_purchase_orders)(
            branch,
            order_number,
            product_code,
            supplier_code,
            expected_delivery_from,
            expected_delivery_to,
            late_only,
            sample_size,
        )

    return mcp


suri_mcp_server = create_mcp_server()
