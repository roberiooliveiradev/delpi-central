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

# DISCOVERY | READ | ANALYSIS | PREPARE | ACT — fail-closed para nomes
# não registrados (o default ACT é a classe mais restritiva).
# ACT só executa com identidade humana, confirmação explícita, AuthZ
# live e ENG_EVA_ACT_ENABLED — ver tool_bridge._require_eva_act.
TOOL_CLASS: dict[str, str] = {
    "get_catalog": "DISCOVERY",
    "get_engineering_home": "READ",
    "get_engineering_overview": "READ",
    "list_lmps": "READ",
    "get_lmp_summary": "READ",
    "get_lmp_detail": "READ",
    "get_lmp_history": "READ",
    "get_lmp_goal_context": "READ",
    "get_lmp_department_idd": "READ",
    "get_lmp_nc_streak": "READ",
    "get_product_structure": "READ",
    "search_nonconformities": "READ",
    "get_nonconformity": "READ",
    "get_nonconformity_history": "READ",
    "get_nonconformity_indicators": "READ",
    "get_nonconformity_tags": "READ",
    "get_nonconformity_context": "READ",
    "export_nonconformities": "READ",
    "prepare_nonconformity_mutation": "PREPARE",
    "create_nonconformity": "ACT",
    "update_nonconformity": "ACT",
    "delete_nonconformity": "ACT",
    "import_nonconformities": "ACT",
}

# Superfície semântica estável (EVA.MCP.SEMANTIC.R1 / plano 54): as
# seis tools despacham por (entity, action) do registry tipado — novas
# capacidades entram como ações, nunca como novas tools.
SEMANTIC_TOOL_CLASS: dict[str, str] = {
    "get_context": "DISCOVERY",
    "read": "READ",
    "analyze": "ANALYSIS",
    "knowledge": "READ",
    "execute": "ACT",
    "delete": "ACT",
}

SEMANTIC_TOOL_NAMES: tuple[str, ...] = tuple(SEMANTIC_TOOL_CLASS.keys())

# Legadas retiradas do MCP (mission legacy-removal): 23 nomes
# permanecem aqui somente como referência histórica de descontinuação
# — nenhuma é registrada, exposta ou invocável.
EVA_LEGACY_TOOL_NAMES: frozenset[str] = frozenset(TOOL_CLASS.keys())

TOOL_CLASS.update(SEMANTIC_TOOL_CLASS)

MCP_TOOL_NAMES: tuple[str, ...] = SEMANTIC_TOOL_NAMES

# ACT de alto impacto — confirmação humana reforçada obrigatória;
# delete é irreversível (imports destrutivos vivem dentro de
# execute/nonconformity.import via prepare/commit, não como tool).
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset({"delete"})
