"""EVA MCP contract constants (Plugin / Agent surface).

Technical ids are not branding. EVA — Engenharia Virtual Assistida —
é a especialista de Engenharia exposta via MCP governado da
engineering-api (mesmo padrão TÉO/VISTA/CLARA: superfície MCP do
próprio owner do domínio).
"""

from __future__ import annotations

# Keycloak confidential client for OpenAI Plugin / MCP.
MCP_PREDEFINED_CLIENT_ID = "mcp-engineering"

CANONICAL_MCP_RESOURCE_URL = (
    "https://minhadelpi.com.br/apps/engineering-api/mcp"
)

MCP_GATEWAY_ROOT = "/apps/engineering-api"

MCP_AUTH_MODEL = "TRANSPORT_REQUIRES_OAUTH"

# READ | DISCOVERY | ANALYSIS — EVA V1 é somente leitura; ACT/PREPARE
# não existem nesta fase (fail-closed para nomes não registrados).
TOOL_CLASS: dict[str, str] = {
    "get_catalog": "DISCOVERY",
    "get_engineering_home": "READ",
    "get_engineering_overview": "READ",
}

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset()
