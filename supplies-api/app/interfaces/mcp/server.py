"""SURI MCPServer — conversational surface of Portal Suprimentos.

Semantic contract freeze rev.3: exactly five tools
(``get_context``, ``read``, ``analyze``, ``knowledge``, ``execute``)
dispatching to specialized handlers. Tools are declared with the frozen
``delpi_mcp`` taxonomy; metadata never authorizes — each handler re-applies
the same policies the Flask BFF routes use (``can_use_operations``/
``require_units`` + Core-derived EffectiveUser).
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
    PostalCodeIdentity,
    PurchaseOrderAnalyzeFilters,
    PurchaseOrderExportFilters,
    PurchaseOrderIdentity,
    PurchaseOrderSearchFilters,
    PurchaseRequestCostCentersFilters,
    PurchaseRequestDetailFilters,
    PurchaseRequestExportFilters,
    PurchaseRequestIdentity,
    PurchaseRequestRequestersFilters,
    PurchaseRequestSearchFilters,
    PurchaseRequestSummaryFilters,
    SupplierCatalogFilters,
    SupplierIdentity,
    SupplierOperationIdentity,
    SupplierPreviewFilters,
    SupplierSearchFilters,
    SupplierTaxIdFilters,
    SupplierWriteOperation,
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
    # ACT tools declare their governed retry semantics: writes are never
    # re-sent implicitly and idempotency keys dedupe client retries.
    idempotent = True if kind == "ACT" else None
    return ToolAnnotations.model_validate(
        tool_annotations_payload(
            title,
            read_only=read_only,
            destructive=destructive,
            idempotent=idempotent,
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
            "via 'identity' {branch, order_number}. entity=suppliers: "
            "action=search lista fornecedores (filters query/state/"
            "blocked/page/page_size/sort), action=get retorna a ficha "
            "cadastral via 'identity' {supplier_code, supplier_store}, "
            "action=catalogs consulta catálogos TOTVS da allowlist "
            "(filters.kind obrigatório), action=search_by_tax_id lista "
            "registros existentes para um CNPJ, action=existing verifica "
            "duplicidade por CNPJ, action=operations acompanha uma "
            "operação cadastral via 'identity' {operation_id}, "
            "action=integration_status publica o diagnóstico sanitizado "
            "da integração (somente supplies.manage). "
            "entity=postal_codes: action=lookup propõe endereço por CEP "
            "via 'identity' {postal_code} — proposta, nunca persiste. "
            "entity=purchase_requests: action=search lista "
            "solicitações de compra (filters fechados — branch "
            "obrigatória, período, request_number, requester_user_id, "
            "cost_center, product_code, supplier_code, order_number, "
            "overall_stage, sort, page/page_size); action=summary "
            "retorna os contadores de etapa do owner; "
            "action=requesters e action=cost_centers retornam as "
            "facetas autorizadas; action=get retorna a solicitação por "
            "'identity' {branch, request_number} com contexto opcional "
            "de facetas em 'filters'; action=export retorna o dataset "
            "filtrado em JSON com metadados do artefato. "
            "entity=purchase_orders: action=export retorna o dataset "
            "filtrado de pedidos em aberto em JSON (mesmo recorte do "
            "XLSX do Portal; a materialização em arquivo permanece no "
            "Portal). "
            "Requer supplies.access e escopo do próprio usuário."
        ),
        annotations=_annotations("read", "Read supplies entities"),
        meta=meta,
    )
    def read(
        entity: Literal[
            "purchase_orders",
            "purchase_requests",
            "suppliers",
            "postal_codes",
        ],
        action: Literal[
            "search",
            "get",
            "export",
            "summary",
            "requesters",
            "cost_centers",
            "catalogs",
            "search_by_tax_id",
            "existing",
            "operations",
            "integration_status",
            "lookup",
        ],
        filters: (
            PurchaseOrderSearchFilters
            | PurchaseOrderExportFilters
            | PurchaseRequestSearchFilters
            | PurchaseRequestSummaryFilters
            | PurchaseRequestRequestersFilters
            | PurchaseRequestCostCentersFilters
            | PurchaseRequestDetailFilters
            | PurchaseRequestExportFilters
            | SupplierSearchFilters
            | SupplierCatalogFilters
            | SupplierTaxIdFilters
            | None
        ) = None,
        identity: (
            PurchaseOrderIdentity
            | PurchaseRequestIdentity
            | SupplierIdentity
            | SupplierOperationIdentity
            | PostalCodeIdentity
            | None
        ) = None,
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
            "limita a amostra. "
            "analysis=supplier_creation_preview: pré-cadastro de "
            "fornecedor por CNPJ (filters.tax_id) — dados consultados no "
            "registro externo com proveniência, duplicidades detectadas, "
            "campos obrigatórios ausentes e prontidão para cadastro; "
            "estritamente read-only (write_enabled=false) e dependente "
            "do provider configurado — indisponibilidade é reportada "
            "honestamente, nunca preenchida com dados inventados."
        ),
        annotations=_annotations("analyze", "Analyze supplies data"),
        meta=meta,
    )
    def analyze(
        analysis: Literal[
            "purchase_orders_summary", "supplier_creation_preview"
        ],
        filters: PurchaseOrderAnalyzeFilters | SupplierPreviewFilters | None = None,
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

    @mcp.tool(
        name="execute",
        title="Execute governed supplier writes",
        description=(
            "Escrita governada com paridade ao Portal Suprimentos. "
            "entity=suppliers: action=create cadastra um novo fornecedor "
            "(op.supplier — mesmos campos do Portal, validação cadastral "
            "e pré-checagem de duplicidade por tax_id); action=update "
            "altera campos editáveis de um fornecedor existente "
            "(op.supplier_code + op.supplier_store + op.fields — "
            "identidade inequívoca, campos de identidade/documento "
            "imutáveis). 'operations' aceita até 10 operações "
            "sequenciais; cada uma pode levar 'idempotency_key' para "
            "deduplicar retries. Requer supplies.access; identidade e "
            "escopo são os do próprio usuário. Resultados por operação: "
            "confirmed/acknowledged/sent/rejected/indeterminate/replayed "
            "com operation_id do tracker api-delpi — indeterminate exige "
            "verificação antes de repetir (nunca há retry implícito)."
        ),
        annotations=_annotations("execute", "Execute supplier writes"),
        meta=meta,
    )
    def execute(
        entity: Literal["suppliers"],
        action: Literal["create", "update"],
        operations: list[SupplierWriteOperation],
    ) -> CallToolResult:
        return _guarded(bridge.tool_execute)(entity, action, operations)

    return mcp


suri_mcp_server = create_mcp_server()
