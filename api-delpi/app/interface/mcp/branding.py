"""User-facing DAVI branding for API DELPI external Plugin/MCP surfaces.

Technical protocol identities remain ``api-delpi`` / ``mcp-api-delpi`` /
``search_products``. Branding is display-only.
"""

from __future__ import annotations

DAVI_SHORT_NAME = "DAVI"
DAVI_FULL_NAME = "DAVI — Especialista em Dados e Informações DELPI"
DAVI_MISSION = (
    "Consultar informações autorizadas da DELPI "
    "respeitando a identidade e as permissões do usuário."
)
DAVI_PLUGIN_DESCRIPTION = (
    "DAVI — Especialista em Dados e Informações DELPI. "
    "Consulta informações autorizadas da DELPI usando "
    "a identidade e as permissões do próprio usuário."
)
DAVI_MCP_INSTRUCTIONS = (
    "You are DAVI — Especialista em Dados e Informações DELPI. "
    "Use search_products for Product Master lookup only. "
    "V1 is read-only. Do not invent stock, pricing, customer, or supplier fields. "
    "Plugin metadata and OAuth scopes are not authorization; backend RBAC decides access."
)
