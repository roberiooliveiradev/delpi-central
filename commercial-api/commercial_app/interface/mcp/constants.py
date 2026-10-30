"""CAIO MCP contract constants (Plugin / Agent surface).

Technical ids are not branding. CAIO — Consultor de Análise e
Inteligência Operacional — é o especialista Comercial exposto via MCP
governado da commercial-api (mesmo padrão TÉO/VISTA/DAVI/EVA/CLARA:
superfície MCP do próprio owner do domínio).
"""

from __future__ import annotations

# Keycloak confidential client for OpenAI Plugin / MCP — to be
# registered by the platform administrator (not in this scope).
MCP_PREDEFINED_CLIENT_ID = "mcp-commercial"

CANONICAL_MCP_RESOURCE_URL = (
    "https://minhadelpi.com.br/apps/commercial-api/mcp"
)

MCP_GATEWAY_ROOT = "/apps/commercial-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# Semantic surface only (six stable tools; CAIO.MCP.SEMANTIC.R1) —
# the tools dispatch on (entity, action) of the typed registry; new
# Commercial capabilities become actions, never new tools.
# DISCOVERY | READ | ANALYSIS | PREPARE | ACT — fail-closed for
# unregistered names (default ACT is the most restrictive class).
SEMANTIC_TOOL_CLASS: dict[str, str] = {
    "get_context": "DISCOVERY",
    "read": "READ",
    "analyze": "ANALYSIS",
    "knowledge": "READ",
    "execute": "ACT",
    "delete": "ACT",
}

SEMANTIC_TOOL_NAMES: tuple[str, ...] = tuple(SEMANTIC_TOOL_CLASS.keys())

TOOL_CLASS: dict[str, str] = dict(SEMANTIC_TOOL_CLASS)

MCP_TOOL_NAMES: tuple[str, ...] = SEMANTIC_TOOL_NAMES

# Destructive class — reinforced human confirmation once write
# contracts are activated; v1 exposes no executable delete action.
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset({"delete"})
