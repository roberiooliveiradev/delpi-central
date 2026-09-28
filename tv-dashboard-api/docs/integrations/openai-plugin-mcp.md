# VISTA / TV Dashboard — OpenAI Plugin + MCP (READ surface)

> Documentation does not prove runtime. Evidence is classified; revalidate after material deploy/auth changes.

Shared onboarding (novos MCPs):
[`docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`](../../../docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md)

## Specialist identity

| Field | Value |
|---|---|
| Short name | **VISTA** |
| Full name | VISTA — Especialista em Painéis Operacionais DELPI |
| Mission | Painéis operacionais / programações / telas / DataModels no TV Dashboard |
| Role | Conversational specialist = **MCP consumer over canonical application services** |

```text
VISTA capability ≤ authenticated user capability
ChatGPT confirmation ≠ authorization
MCP ≠ Domain API
MCP ≠ RBAC
MCP ≠ generic proxy
AuthZ final = backend / GptActionsDispatchService / PlaylistAccessService
```

## Technical identities

| Surface | Technical id |
|---|---|
| MCP server name | `tv-dashboard` |
| Keycloak client | `mcp-tv-dashboard` (PENDING provisioning) |
| MCP endpoint / resource | `https://minhadelpi.com.br/apps/tv-dashboard-api/mcp` |
| Protected Resource Metadata | `https://minhadelpi.com.br/apps/tv-dashboard-api/.well-known/oauth-protected-resource` |
| OIDC issuer | `https://minhadelpi.com.br/auth/realms/delpi` |

## Architecture

```text
Workspace Agent / ChatGPT Plugin (VISTA)
  → OAuth Authorization Code + PKCE
  → Keycloak end-user identity (mcp-tv-dashboard)
  → MCP Streamable HTTP /apps/tv-dashboard-api/mcp
  → interface/mcp adapter (context rebuild only)
  → GptActionsDispatchService (same as /gpt-actions)
  → canonical AuthZ + domain services
  → Postgres tv-dashboard
```

No HTTP loop: tools call the dispatch service directly — never `/gpt-actions` over HTTP.

## Surface policy (MCP1)

```text
VISTA_MCP_SURFACE = READ_V1
six semantic READ tools = REQUIRED
write / PREPARE / ACT tools = MCP2 (not this surface)
resources / prompts = FORBIDDEN
legacy primitive tools (upsert_data_source, patch_data_source_params,
suggest_change, preview_data_block, preview_change, commit_change) = FORBIDDEN
```

Tools (all `READ`, non-persisting):

| Tool | Delegates to |
|---|---|
| `list_playlists` | `GptActionsDispatchService.list_playlists` |
| `get_playlist_context` | `GptActionsDispatchService.get_playlist_context` |
| `get_catalog` | `GptActionsDispatchService.get_catalog` |
| `search_data_routes` | `GptActionsDispatchService.search_data_routes` |
| `inspect_data_model` | `GptActionsDispatchService.inspect_data_model` |
| `preview_data_model` | `GptActionsDispatchService.preview_data_model` (inline candidate never persisted) |

## OAuth transport requirements

Access tokens used at `/mcp` must contain:

```text
aud: delpi-central + https://minhadelpi.com.br/apps/tv-dashboard-api/mcp
scope: openid profile email mcp:tools
```

- `audience-delpi` is an internal audience mapper — never an OAuth `scope` claim.
- Internal service tokens (`internal-service`) are rejected on `/mcp` with 401.
- Unauthenticated calls return `401` + `WWW-Authenticate: Bearer realm="mcp", resource_metadata=…`.
- `/mcp` (no slash) is rewritten internally to `/mcp/` — no provider-breaking 307.
- DNS-rebinding/Origin protection via FastMCP `TransportSecuritySettings`
  (`TV_MCP_ALLOWED_HOSTS`, `TV_MCP_ALLOWED_ORIGINS` override defaults).

## Configuration

| Env | Purpose | Default |
|---|---|---|
| `TV_DASHBOARD_API_ROOT_PATH` | public app root (mount prefix) | `/apps/tv-dashboard-api` |
| `PUBLIC_BASE_URL` | public origin for resource URL derivation | unset → canonical `minhadelpi.com.br` |
| `MCP_RESOURCE_URL` | explicit resource/audience override (per-env) | unset |
| `MCP_PREDEFINED_CLIENT_ID` | Keycloak client override | `mcp-tv-dashboard` |
| `KEYCLOAK_ISSUER` | authorization_servers in metadata | unset |
| `TV_MCP_ALLOWED_HOSTS` | DNS-rebinding host allowlist (csv) | `minhadelpi.com.br` + localhost |
| `TV_MCP_ALLOWED_ORIGINS` | Origin allowlist (csv) | `https://minhadelpi.com.br` + localhost |

No enable/disable flag — mount is unconditional, matching the TÉO/DAVI
convention (surface is OAuth-gated; absence of traffic is the off state).

## Keycloak provisioning (PENDING)

Required on `mcp-tv-dashboard` (confidential, Authorization Code + PKCE):

1. client scope `mcp:tools` (generic, shared with other MCP clients);
2. **dedicated** audience mapper emitting `https://minhadelpi.com.br/apps/tv-dashboard-api/mcp` into `aud` — never reuse `audience-delpi`, never place resource audience inside shared `mcp:tools`;
3. audience mapper bound to this client's specific scope only;
4. redirect URIs for the Plugin/Workspace Agent;
5. verify issued token: `aud` contains both `delpi-central` and the MCP resource, `scope` contains `mcp:tools`.

Until provisioning evidence exists, status is **PENDING** — do not mark live.

## Writes are MCP2

This surface exposes no mutation path. Writes will arrive as the governed
envelope (`prepare_change` → proposal handle → `commit_proposal`) over the
existing `changes/preview|commit` flow — same contract as GPT Actions.
