# API DELPI — OpenAI Plugin package

Portable Agent Plugins 1.0 package for ChatGPT / Codex.

**Strategic target:** OpenAI Plugin + MCP (not Custom GPT Actions).

## Contents

| File | Role |
|---|---|
| `plugin.json` | Agent Plugins manifest (`name`: `api-delpi`) |
| `mcp.json` | Streamable HTTP MCP server URL |
| `skills/api-delpi/SKILL.md` | Minimal workflow guidance |

User-facing display name: **API DELPI**.

Capability advertised by description: **Read-only** (no Write).

## Developer-mode test (manual)

Documentation does not prove runtime.

1. Ensure `https://{host}/apps/api-delpi/mcp` is reachable over HTTPS.
2. Confirm `GET /.well-known/oauth-protected-resource` (under `/apps/api-delpi`) returns metadata.
3. In ChatGPT developer mode, load this plugin directory (or register the MCP URL).
4. Complete OAuth with a real DELPI user (Keycloak).
5. Tool scan must list only `search_products`.
6. Authorized user: search returns allowlisted fields only.
7. Unauthorized user: fail-closed (403 / tool error).

Do not place files under `~/.agents/` or `~/.codex/` from this repository.

## Go-live

See `api-delpi/docs/integrations/openai-plugin-mcp.md`. `GO_LIVE` remains **PENDING** until OAuth compatibility and production smoke pass.
