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

    # --- Paridade READ Portal × CLARA (classe A — sem confirmação) --
    # Cada tool invoca a função de rota canônica do Portal com a
    # request reconstruída: gate, bearer e envelope idênticos.

    @mcp.tool(
        name="list_competences",
        title="List competences",
        description=(
            "Competências do fechamento mensal — mesma listagem do "
            "Portal (GET /closing/competences)."
        ),
        annotations=_annotations("list_competences", "List competences"),
        meta=meta,
    )
    def list_competences() -> CallToolResult:
        return _guarded(bridge.tool_list_competences)()

    @mcp.tool(
        name="get_competence",
        title="Get competence",
        description=(
            "Detalhe da competência (período AAAA-MM) — mesmo "
            "contrato do Portal."
        ),
        annotations=_annotations("get_competence", "Get competence"),
        meta=meta,
    )
    def get_competence(period: str) -> CallToolResult:
        return _guarded(bridge.tool_get_competence)(period)

    @mcp.tool(
        name="get_checklist_item",
        title="Get checklist item",
        description="Detalhe de um item do checklist da competência.",
        annotations=_annotations(
            "get_checklist_item", "Get checklist item"
        ),
        meta=meta,
    )
    def get_checklist_item(
        period: str, item_key: str
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_checklist_item)(
            period, item_key
        )

    @mcp.tool(
        name="get_closing_cockpit",
        title="Get closing cockpit",
        description=(
            "Cockpit consolidado da competência (P1) — a mesma "
            "composição da tela Cockpit do Portal."
        ),
        annotations=_annotations(
            "get_closing_cockpit", "Get closing cockpit"
        ),
        meta=meta,
    )
    def get_closing_cockpit(period: str) -> CallToolResult:
        return _guarded(bridge.tool_get_closing_cockpit)(period)

    @mcp.tool(
        name="list_my_tasks",
        title="List my tasks",
        description=(
            "Fila de tarefas do usuário autenticado (pendências, "
            "revisões, correções) — mesma visão «Minhas tarefas»."
        ),
        annotations=_annotations("list_my_tasks", "List my tasks"),
        meta=meta,
    )
    def list_my_tasks(period: str | None = None) -> CallToolResult:
        return _guarded(bridge.tool_list_my_tasks)(period)

    @mcp.tool(
        name="get_pendency",
        title="Get pendency",
        description=(
            "Detalhe da pendência + histórico de eventos — mesma "
            "visão do Portal."
        ),
        annotations=_annotations("get_pendency", "Get pendency"),
        meta=meta,
    )
    def get_pendency(
        period: str,
        pendency_id: str,
        include_history: bool = True,
        branch_scope: str | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_pendency)(
            period, pendency_id, include_history, branch_scope
        )

    @mcp.tool(
        name="list_p3_events",
        title="List P3 events",
        description=(
            "Eventos/auditoria da conciliação P3 da competência."
        ),
        annotations=_annotations("list_p3_events", "List P3 events"),
        meta=meta,
    )
    def list_p3_events(period: str) -> CallToolResult:
        return _guarded(bridge.tool_list_p3_events)(period)

    @mcp.tool(
        name="get_package",
        title="Get package detail",
        description=(
            "Detalhe de um pacote (versões, estado, esclarecimentos) "
            "— mesmo escopo de visibilidade do Portal."
        ),
        annotations=_annotations("get_package", "Get package"),
        meta=meta,
    )
    def get_package(period: str, package_id: str) -> CallToolResult:
        return _guarded(bridge.tool_get_package)(period, package_id)

    @mcp.tool(
        name="get_document",
        title="Get document detail",
        description=(
            "Documento da competência com versões, mensagens, "
            "solicitações de ajuste e (opcional) eventos de auditoria "
            "— mesma visão do painel de documentos do Portal."
        ),
        annotations=_annotations("get_document", "Get document"),
        meta=meta,
    )
    def get_document(
        period: str,
        document_id: str,
        branch_scope: str | None = None,
        include_audit: bool = False,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_document)(
            period, document_id, branch_scope, include_audit
        )

    @mcp.tool(
        name="get_item_validation",
        title="Get item validation",
        description=(
            "Decisões e correções de um item do checklist — mesma "
            "visão de validação do Portal."
        ),
        annotations=_annotations(
            "get_item_validation", "Get item validation"
        ),
        meta=meta,
    )
    def get_item_validation(
        period: str, item_key: str, branch_scope: str | None = None
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_item_validation)(
            period, item_key, branch_scope
        )

    @mcp.tool(
        name="lookup_participants",
        title="Lookup document participants",
        description=(
            "Resolve nomes de participantes vinculados ao documento "
            "(autor/ator/uploader). Ids sem vínculo são omitidos — "
            "ausência não confirma existência."
        ),
        annotations=_annotations(
            "lookup_participants", "Lookup participants"
        ),
        meta=meta,
    )
    def lookup_participants(
        period: str,
        document_id: str,
        ids: list[str],
        branch_scope: str | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_lookup_participants)(
            period, document_id, ids, branch_scope
        )

    @mcp.tool(
        name="get_financial_settlements",
        title="Get financial settlements",
        description=(
            "Baixas a pagar/receber (R01/R02) — consulta operacional "
            "real via api-delpi com filtros, ordenação e paginação "
            "idênticos ao Portal. Paridade oficial do relatório: "
            "PENDING."
        ),
        annotations=_annotations(
            "get_financial_settlements", "Get financial settlements"
        ),
        meta=meta,
    )
    def get_financial_settlements(
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
        sort_by: str = "settlement_date",
        sort_dir: str = "desc",
        page: int = 1,
        page_size: int = 50,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_financial_settlements)(
            side, start_date, end_date, nature_code, movement_type,
            sort_by, sort_dir, page, page_size
        )

    @mcp.tool(
        name="get_financial_settlements_summary",
        title="Get settlements summary",
        description=(
            "Totais das baixas no período (mesma rota /summary do "
            "Portal)."
        ),
        annotations=_annotations(
            "get_financial_settlements_summary",
            "Get settlements summary",
        ),
        meta=meta,
    )
    def get_financial_settlements_summary(
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_financial_settlements_summary)(
            start_date, end_date, nature_code, movement_type
        )

    @mcp.tool(
        name="get_stock_inventory",
        title="Get stock inventory",
        description=(
            "R03/P7 posição de estoque — consulta operacional real "
            "(período, filial, escopo all_products|mp_pi_pa, armazém, "
            "paginação). Paridade oficial MATR460: PENDING."
        ),
        annotations=_annotations(
            "get_stock_inventory", "Get stock inventory"
        ),
        meta=meta,
    )
    def get_stock_inventory(
        period: str,
        branch: str = "all",
        report_scope: str = "all_products",
        warehouse: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_stock_inventory)(
            period, branch, report_scope, warehouse, page, page_size
        )

    @mcp.tool(
        name="get_stock_movements",
        title="Get stock movements",
        description=(
            "R05 entradas e saídas do mês (MATR320) — dados reais "
            "delegados ao api-delpi com o bearer do usuário."
        ),
        annotations=_annotations(
            "get_stock_movements", "Get stock movements"
        ),
        meta=meta,
    )
    def get_stock_movements(
        period: str,
        branch: str = "all",
        report_scope: str = "all_products",
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_stock_movements)(
            period, branch, report_scope
        )

    @mcp.tool(
        name="get_work_in_process",
        title="Get work in process",
        description=(
            "R08/H02 material em processo (MATR989) — físico e "
            "alocado, com filtro de armazém e paginação do Portal."
        ),
        annotations=_annotations(
            "get_work_in_process", "Get work in process"
        ),
        meta=meta,
    )
    def get_work_in_process(
        period: str,
        branch: str = "all",
        report_scope: str = "all_products",
        warehouse: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_work_in_process)(
            period, branch, report_scope, warehouse, page, page_size
        )

    @mcp.tool(
        name="get_stock_reconciliation",
        title="Get stock reconciliation",
        description=(
            "Conciliação analítica R05−P7−H02 — composição de "
            "identidade SB9. verdict=IDENTITY_ONLY ou DIVERGENCE com "
            "reconciliationVerdict=INCONCLUSIVE; nunca paridade "
            "oficial."
        ),
        annotations=_annotations(
            "get_stock_reconciliation", "Get stock reconciliation"
        ),
        meta=meta,
    )
    def get_stock_reconciliation(
        period: str,
        branch: str = "all",
        report_scope: str = "all_products",
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_stock_reconciliation)(
            period, branch, report_scope
        )

    @mcp.tool(
        name="get_report_matrix",
        title="Get report matrix",
        description=(
            "Matriz R01–R15 de cobertura da competência (checklist-"
            "derived) — implementado vs pendente, sem afirmar "
            "paridade oficial."
        ),
        annotations=_annotations(
            "get_report_matrix", "Get report matrix"
        ),
        meta=meta,
    )
    def get_report_matrix(
        period: str, branch_scope: str | None = None
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_report_matrix)(
            period, branch_scope
        )

    @mcp.tool(
        name="list_closing_catalogs",
        title="List closing catalogs",
        description=(
            "Catálogos governados do fechamento — superfície "
            "administrativa (manage)."
        ),
        annotations=_annotations(
            "list_closing_catalogs", "List closing catalogs"
        ),
        meta=meta,
    )
    def list_closing_catalogs() -> CallToolResult:
        return _guarded(bridge.tool_list_closing_catalogs)()

    @mcp.tool(
        name="list_catalog_entries",
        title="List catalog entries",
        description=(
            "Entradas de um catálogo governado (manage) — ativas e "
            "opcionalmente inativas."
        ),
        annotations=_annotations(
            "list_catalog_entries", "List catalog entries"
        ),
        meta=meta,
    )
    def list_catalog_entries(
        catalog_key: str, include_inactive: bool = True
    ) -> CallToolResult:
        return _guarded(bridge.tool_list_catalog_entries)(
            catalog_key, include_inactive
        )

    @mcp.tool(
        name="list_checklist_templates",
        title="List checklist templates",
        description=(
            "Templates do checklist e suas versões — superfície "
            "administrativa (manage)."
        ),
        annotations=_annotations(
            "list_checklist_templates", "List checklist templates"
        ),
        meta=meta,
    )
    def list_checklist_templates() -> CallToolResult:
        return _guarded(bridge.tool_list_checklist_templates)()

    @mcp.tool(
        name="get_checklist_template_version",
        title="Get template version",
        description=(
            "Versão de um template com os itens — superfície "
            "administrativa (manage)."
        ),
        annotations=_annotations(
            "get_checklist_template_version", "Get template version"
        ),
        meta=meta,
    )
    def get_checklist_template_version(
        template_id: str, version: int
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_checklist_template_version)(
            template_id, version
        )

    @mcp.tool(
        name="list_received_deliveries",
        title="List received deliveries",
        description=(
            "Entregas de documentos disponibilizados ao destinatário "
            "— experiência DRE (access.dre)."
        ),
        annotations=_annotations(
            "list_received_deliveries", "List received deliveries"
        ),
        meta=meta,
    )
    def list_received_deliveries() -> CallToolResult:
        return _guarded(bridge.tool_list_received_deliveries)()

    @mcp.tool(
        name="get_received_delivery",
        title="Get received delivery",
        description=(
            "Entrega da competência com documentos disponibilizados "
            "— experiência DRE (access.dre)."
        ),
        annotations=_annotations(
            "get_received_delivery", "Get received delivery"
        ),
        meta=meta,
    )
    def get_received_delivery(period: str) -> CallToolResult:
        return _guarded(bridge.tool_get_received_delivery)(period)

    @mcp.tool(
        name="get_received_document",
        title="Get received document",
        description=(
            "Documento recebido com mensagens e solicitações de "
            "ajuste — experiência DRE (access.dre)."
        ),
        annotations=_annotations(
            "get_received_document", "Get received document"
        ),
        meta=meta,
    )
    def get_received_document(
        period: str, document_id: str
    ) -> CallToolResult:
        return _guarded(bridge.tool_get_received_document)(
            period, document_id
        )

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
            "ACT: executa a proposta selada após consentimento "
            "verificável — consent_record gravado pela página de "
            "consentimento do Portal (confirmation_url do PREPARE) "
            "com credencial fresca que esta conversa não produz. "
            "Revalida ator, expiração, estado selado e as regras da "
            "BFF; audita canal mcp/clara e verifica a pós-condição "
            "real. resume=true reconcilia CLAIMED/UNKNOWN por "
            "read-back, sem repetir efeito."
        ),
        annotations=_annotations("commit_proposal", "Commit proposal"),
        meta=meta,
    )
    def commit_proposal(
        proposal_handle: str, resume: bool = False
    ) -> CallToolResult:
        return _guarded(bridge.tool_commit_proposal)(
            proposal_handle, resume
        )

    @mcp.tool(
        name="prepare_batch",
        title="Prepare operation batch",
        description=(
            "PREPARE_BATCH: classifica as operações pedidas (viable/"
            "blocked), resolve dependências, sela o plano inteiro "
            "(plan_hash) e cria uma proposta governed por operação. "
            "Uma única confirmação consolidada (confirm_batch) cobre "
            "o lote — nunca uma por operação."
        ),
        annotations=_annotations(
            "prepare_batch", "Prepare operation batch"
        ),
        meta=meta,
    )
    def prepare_batch(
        operations: list[dict[str, Any]]
    ) -> CallToolResult:
        return _guarded(bridge.tool_prepare_batch)(operations)

    @mcp.tool(
        name="confirm_batch",
        title="Confirm batch plan",
        description=(
            "Verifica o consentimento do lote inteiro: um "
            "consent_record portal_step_up gravado pela página de "
            "consentimento do Portal (CONSOLIDATED) ou atestação "
            "assinada do host (HOST_ATTESTED), ambos vinculados ao "
            "plan_hash exato. A chamada MCP não é prova de "
            "consentimento — sem evidência válida retorna "
            "consent_required com a confirmation_url. O plano selado "
            "não pode ser ampliado."
        ),
        annotations=_annotations(
            "confirm_batch", "Confirm batch plan"
        ),
        meta=meta,
    )
    def confirm_batch(
        batch_handle: str,
        plan_hash: str,
        attestation: dict[str, Any] | None = None,
    ) -> CallToolResult:
        return _guarded(bridge.tool_confirm_batch)(
            batch_handle, plan_hash, attestation
        )

    @mcp.tool(
        name="execute_batch",
        title="Execute confirmed batch",
        description=(
            "EXECUTE: executa o lote CONFIRMED em ordem topológica — "
            "claim atômico por operação, revalidação de staleness, "
            "execução pelas regras canônicas da BFF, read-back "
            "independente e relatório por operação. Dependentes de "
            "falhas são bloqueadas; independentes continuam."
        ),
        annotations=_annotations(
            "execute_batch", "Execute confirmed batch"
        ),
        meta=meta,
    )
    def execute_batch(
        batch_handle: str, resume: bool = False
    ) -> CallToolResult:
        return _guarded(bridge.tool_execute_batch)(
            batch_handle, resume
        )

    @mcp.tool(
        name="get_batch_status",
        title="Get batch status",
        description=(
            "Estado do lote e de cada operação (VERIFIED/FAILED/"
            "BLOCKED/UNKNOWN), consent_mode e resultado consolidado."
        ),
        annotations=_annotations(
            "get_batch_status", "Get batch status"
        ),
        meta=meta,
    )
    def get_batch_status(batch_id: str) -> CallToolResult:
        return _guarded(bridge.tool_get_batch_status)(batch_id)

    return mcp


clara_mcp_server = create_mcp_server()
