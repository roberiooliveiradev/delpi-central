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

MCP_TOOL_NAMES: tuple[str, ...] = tuple(TOOL_CLASS.keys())

# ACT de alto impacto — confirmação humana reforçada obrigatória;
# delete é irreversível e import substitui todo o acervo quando não é
# dry-run (o adapter Postgres ainda exige ENG_NC_IMPORT_REPLACE_ENABLED).
DESTRUCTIVE_ACT_TOOLS: frozenset[str] = frozenset(
    {"delete_nonconformity", "import_nonconformities"}
)
