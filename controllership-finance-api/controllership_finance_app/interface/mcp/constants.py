"""Constantes do contrato MCP da CLARA.

Technical ids não são branding — «CLARA» é identidade de produto,
o id técnico permanece ``controllership-finance`` /
``mcp-controllership-finance`` (``mcp-clara`` = identificador OAuth
anterior, mantido apenas como histórico).

CLARA-MCP-SEMANTIC-001 (doc 119): a superfície pública é exatamente
seis tools semânticas estáveis; capacidades crescem via registry
(entity, action) — nunca via novos nomes de tool. Os nomes legados
permanecem documentados em ``LEGACY_TOOL_NAMES`` para a janela de
compatibilidade/migração de consumers (os handlers seguem vivos como
alvos do dispatcher semântico).
"""

from __future__ import annotations

# Keycloak confidential client para a superfície MCP da CLARA.
MCP_PREDEFINED_CLIENT_ID = "mcp-controllership-finance"

CANONICAL_MCP_RESOURCE_URL = (
    "https://minhadelpi.com.br/apps/controllership-finance-api/mcp"
)

MCP_GATEWAY_ROOT = "/apps/controllership-finance-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# --- Superfície semântica estável (doc 119) ---------------------------
# DISCOVERY | READ | ANALYSIS | PREPARE | ACT — taxonomia congelada
# do shared/delpi_mcp. Metadata descreve semântica, nunca autoriza.
SEMANTIC_TOOL_CLASS: dict[str, str] = {
    "get_context": "DISCOVERY",
    "read": "READ",
    "analyze": "ANALYSIS",
    "knowledge": "READ",
    "execute": "ACT",
    "delete": "ACT",
}

SEMANTIC_TOOL_NAMES: tuple[str, ...] = tuple(SEMANTIC_TOOL_CLASS.keys())

# --- Superfície legada (pré-doc-119) ----------------------------------
# Mantida para a janela de compatibilidade: os handlers tool_* seguem
# como alvos do dispatcher semântico. Não registradas no tools/list —
# consumers migram pelo discovery dinâmico do host (plugin ChatGPT).
LEGACY_TOOL_CLASS: dict[str, str] = {
    "get_my_context": "READ",
    "get_catalog": "DISCOVERY",
    "get_competence_state": "READ",
    "get_checklist_items": "READ",
    "list_documents": "READ",
    "get_p3_reconciliation": "READ",
    "list_pendencies": "READ",
    "get_package_review": "READ",
    "analyze_closing_blockers": "ANALYSIS",
    "search_closing_knowledge": "READ",
    "get_knowledge_item": "READ",
    "list_knowledge_sources": "DISCOVERY",
    # --- paridade READ Portal × CLARA (execução 016, classe A) -------
    "list_competences": "READ",
    "get_competence": "READ",
    "get_checklist_item": "READ",
    "get_closing_cockpit": "READ",
    "list_my_tasks": "READ",
    "get_pendency": "READ",
    "list_p3_events": "READ",
    "get_package": "READ",
    "get_document": "READ",
    "get_item_validation": "READ",
    "lookup_participants": "READ",
    "get_financial_settlements": "READ",
    "get_financial_settlements_summary": "READ",
    "get_stock_inventory": "READ",
    "get_stock_movements": "READ",
    "get_work_in_process": "READ",
    "get_stock_reconciliation": "READ",
    "get_report_matrix": "READ",
    "list_closing_catalogs": "READ",
    "list_catalog_entries": "READ",
    "list_checklist_templates": "READ",
    "get_checklist_template_version": "READ",
    "list_received_deliveries": "READ",
    "get_received_delivery": "READ",
    "get_received_document": "READ",
    # --- escritas governadas (PREPARE → consentimento → ACT) --------
    "prepare_governed_operation": "PREPARE",
    "commit_proposal": "ACT",
    "prepare_batch": "PREPARE",
    "confirm_batch": "PREPARE",
    "execute_batch": "ACT",
    "get_batch_status": "READ",
}

CLARA_LEGACY_TOOL_NAMES: tuple[str, ...] = tuple(
    LEGACY_TOOL_CLASS.keys()
)

# União semântica + legada — usada para class/annotation lookup.
TOOL_CLASS: dict[str, str] = {
    **LEGACY_TOOL_CLASS,
    **SEMANTIC_TOOL_CLASS,
}

# tools/list público: somente a superfície semântica (cutover doc 119).
MCP_TOOL_NAMES: tuple[str, ...] = SEMANTIC_TOOL_NAMES

# execute commit fases e delete carregam operações sensíveis —
# anotação honesta para hosts que respeitam destructiveHint.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset(
    {"execute", "delete"}
)
