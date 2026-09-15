# API DELPI — Custom GPT Actions (LEGACY_TRANSITIONAL)

> **Strategic external target is OpenAI Plugin + MCP.**  
> See [openai-plugin-mcp.md](../integrations/openai-plugin-mcp.md).  
> This surface is retained for migration/compatibility only. Do not expand Actions.

> Approval (data slice): **API-DELPI-GPT-004A.2** (`APPROVED_WITH_RESTRICTIONS`)  
> Pattern (historical): [padrao-custom-gpt-actions-oauth.md](../../docs/11-padroes-de-desenvolvimento/padrao-custom-gpt-actions-oauth.md)

## Scope (V1 — frozen)

| operationId | Path | AuthZ |
|---|---|---|
| `gpt_get_catalog` | `GET /gpt-actions/v1/catalog` | JWT authentication required; business search permission **not** required for catalog |
| `gpt_search_products` | `GET /gpt-actions/v1/products/search` | `ENGINEERING_LMP_ACCESS` |
| `gpt_get_openapi_schema` | `GET /gpt-actions/v1/openapi.json` | **public** (import only; not in schema paths) |

Gateway base: `/apps/api-delpi`.

Shared semantic logic lives in `application/external_capabilities/` (also used by MCP).

### Product search allowlist

`product_code` ← `code` · `description` · `group_category` ← `group_code`  
`customer_reference` and all other fields: **DENY BY DEFAULT**.

`page_size` max **50**.

Out of scope: stock, BOM, production, pricing, finance, sales.

External catalog payloads expose `available: true|false` only — **no** raw permission codes.

## Ops note

Do **not** create a Keycloak client merely named `chatgpt-api-delpi` because old docs mentioned it. Prefer MCP OAuth client configuration documented in the Plugin/MCP guide.
