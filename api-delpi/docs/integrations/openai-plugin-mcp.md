# API DELPI — OpenAI Plugin + MCP

> **Documentation does not prove runtime.**

## Status

| Item | Value |
|---|---|
| Strategic target | OpenAI Plugin → MCP → semantic capability → existing use cases |
| Legacy | `/gpt-actions/v1` = `LEGACY_TRANSITIONAL` |
| V1 business tool | `search_products` (read-only Product Master) |
| MCP auth model | **A — transport requires OAuth** |
| Resource audience | `aud` must include exact `{MCP_RESOURCE_URL}` **and** `delpi-central` |
| Keycloak config | Runbook: [keycloak-mcp-client-runbook.md](./keycloak-mcp-client-runbook.md) (`NOT_APPLIED` until operator) |
| Go-live | `GO_LIVE_BLOCKED` until Keycloak binding + deploy + e2e |

## Architecture

```text
ChatGPT / Codex
  → OpenAI Plugin (integrations/openai-plugin/)
  → MCP Streamable HTTP  /apps/api-delpi/mcp
  → interface/mcp adapter
  → application/external_capabilities
  → SearchProducts use case
  → ENGINEERING_LMP_ACCESS
  → authoritative source
```

## MCP resource (exact)

```text
https://minhadelpi.com.br/apps/api-delpi/mcp
```

Must match metadata, OAuth `resource`, Keycloak Audience mapper, JWT `aud`, plugin `mcp.json`, and MCP validation — no trailing-slash rewrite.

## OAuth scopes

```text
openid profile email audience-delpi mcp:tools
```

- `audience-delpi` → `aud` includes `delpi-central` (platform)
- `mcp:tools` → `aud` includes MCP resource URL (Keycloak documented workaround; **not** native RFC8707)
- Neither scope is business AuthZ

## Token validation on `/mcp`

1. Shared `validate_token` → signature, issuer, exp, nbf, `aud` includes `delpi-central`
2. MCP adapter → `aud` contains exact `MCP_RESOURCE_URL`
3. Required OAuth scopes including `mcp:tools`
4. User context + `ENGINEERING_LMP_ACCESS` for `search_products`

Ordinary DELPI tokens with only `delpi-central` are **rejected** on `/mcp`.

## Client

| Field | Value |
|---|---|
| Mode | `PREDEFINED` |
| Client ID | `mcp-api-delpi` |
| Redirect URI | `TO_CONFIGURE` (ChatGPT MCP UI exact value) |

## Rate limit

Gateway `location ^~ /apps/api-delpi/` has **no** `limit_req`.

```text
MCP_RATE_POLICY = PENDING_OWNER_DECISION
```

Reuse `api_zone` (50r/s) only after gateway owner decision — do not invent limits in Application.

## Plugin package

`api-delpi/integrations/openai-plugin/` — `homepage=TO_CONFIGURE` is a publication blocker, not an MCP runtime blocker.
