# DAVI — OpenAI Plugin package (technical id: `api-delpi`)

Portable Agent Plugins 1.0 package for ChatGPT / Codex.

**Specialist identity (user-facing):** DAVI — Especialista em Dados e Informações DELPI  
**Technical plugin name:** `api-delpi` (do not rename for branding)  
**Strategic target:** OpenAI Plugin + MCP (not Custom GPT Actions)

## Contents

| File | Role |
|---|---|
| `plugin.json` | Agent Plugins manifest (`name`: `api-delpi`) |
| `mcp.json` | Streamable HTTP MCP server URL |
| `skills/api-delpi/SKILL.md` | DAVI workflow guidance |

Capability: **Read-only** V1 (`search_products` only).

## Developer-mode test (manual)

Documentation does not prove runtime.

1. Ensure `https://minhadelpi.com.br/apps/api-delpi/mcp` is reachable over HTTPS.
2. Confirm protected-resource metadata includes `mcp:tools` and exact MCP resource URL.
3. Keycloak client `mcp-api-delpi` per runbook (copy **exact** ChatGPT return URL into Valid redirect URIs — do not invent/hardcode; JWT `scope` must include `openid profile email mcp:tools` — not `audience-delpi`; resource audience is **dedicated** to this client, not nested in shared `mcp:tools`).
4. In ChatGPT, connect remote MCP / load this plugin; specialist presents as **DAVI**.
5. OAuth with a real DELPI user (Authorization Code + PKCE).
6. Tool scan must list only expected MCP tools (`search_products` + dynamic broker tools when deployed).
7. Authorized user: allowlisted fields only.
8. User without `ENGINEERING_LMP_ACCESS`: Forbidden (not OAuth re-link).

Shared MCP Plugin onboarding: `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`.

Do not place files under `~/.agents/` or `~/.codex/` from this repository.

## Publication

`homepage = TO_CONFIGURE` is a **PUBLICATION_BLOCKER**, not an internal MCP runtime blocker.

## Go-live

See `api-delpi/docs/integrations/openai-plugin-mcp.md` and Keycloak runbook. `GO_LIVE` remains blocked until operational proofs pass.
