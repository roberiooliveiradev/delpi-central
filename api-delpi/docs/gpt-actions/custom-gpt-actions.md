# API DELPI — Custom GPT Actions (V1)

> Approval: **API-DELPI-GPT-004A.2** (`APPROVED_WITH_RESTRICTIONS`)  
> Pattern: [padrao-custom-gpt-actions-oauth.md](../../docs/11-padroes-de-desenvolvimento/padrao-custom-gpt-actions-oauth.md)

## Scope (V1)

| operationId | Path | AuthZ |
|---|---|---|
| `gpt_get_catalog` | `GET /gpt-actions/v1/catalog` | `ENGINEERING_LMP_ACCESS` |
| `gpt_search_products` | `GET /gpt-actions/v1/products/search` | `ENGINEERING_LMP_ACCESS` |
| `gpt_get_openapi_schema` | `GET /gpt-actions/v1/openapi.json` | **public** (import only; not in schema paths) |

Gateway base: `/apps/api-delpi`.

### Product search allowlist

`product_code` ← `code` · `description` · `group_category` ← `group_code`  
`customer_reference` and all other fields: **DENY BY DEFAULT**.

`page_size` max **50**.

Out of scope: stock, BOM, production, pricing, finance, sales.

## Ops checklist (not done by this code change)

- Keycloak client `chatgpt-api-delpi` (confidential, Standard Flow ON, Direct Grants OFF, aud `delpi-central`)
- GPT Builder import from `https://{host}/apps/api-delpi/gpt-actions/v1/openapi.json`
- Specialist Instructions (catalog → search; no autonomous unbounded pagination)
