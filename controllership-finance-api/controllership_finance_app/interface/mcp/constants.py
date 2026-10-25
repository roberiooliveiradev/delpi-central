"""Constantes do contrato MCP da CLARA.

Technical ids não são branding — «CLARA» é identidade de produto,
o id técnico permanece ``controllership-finance`` / ``mcp-clara``.
"""

from __future__ import annotations

# Keycloak confidential client para a superfície MCP da CLARA.
MCP_PREDEFINED_CLIENT_ID = "mcp-clara"

CANONICAL_MCP_RESOURCE_URL = (
    "https://minhadelpi.com.br/apps/controllership-finance-api/mcp"
)

MCP_GATEWAY_ROOT = "/apps/controllership-finance-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# DISCOVERY | READ | ANALYSIS | PREPARE | ACT — taxonomia congelada
# do shared/delpi_mcp. Metadata descreve semântica, nunca autoriza.
TOOL_CLASS: dict[str, str] = {
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
    "prepare_governed_operation": "PREPARE",
    "commit_proposal": "ACT",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# commit_proposal pode executar operação sensível — anotação honesta.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset({"commit_proposal"})
