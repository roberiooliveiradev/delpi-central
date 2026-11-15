# Linux Ops MCP P1.5 — Keycloak OAuth client (no additional subscription)

**Source status:** reviewed script candidate in PR. **Not run on production**, no client or secret created by assistant, no gateway deployment, no OAuth login proven.

## Existing accepted evidence

- Owner confirmed automatic Linux collector integration works.
- Owner reported `delpi-linux-ops-mcp` healthy on `127.0.0.1:18765`; metadata OAuth 200 and missing Bearer 401.
- PR #188 merged: limited Nginx routes, but production gateway has **not** been redeployed.
- Zero additional OpenAI API fees / tunnel subscription allowed. Use existing Cloudflare HTTPS hostname and ChatGPT plugin entitlement.

## Provisioning method and protections

Dedicated client `mcp-linux-ops`, confidential OAuth authorization-code flow with PKCE S256, shared generic `mcp:tools`, shared `audience-delpi` plus **only** dedicated `mcp-audience-linux-ops` mapper, mapping `https://minhadelpi.com.br/apps/linux-ops-mcp/mcp` into the access token `aud`. No shared-scope audience changes. No user provisioning, service account, direct grants, or token exchange.

Script: `infra/scripts/keycloak_linux_ops_client.py` (reuses the existing `delia_mcp_keycloak_state.py` Admin REST helper; no new dependencies). Default mode is READ-only `--check`; `--apply` creates only one dedicated client/scope and binds defaults, refuses to overwrite drifted/unknown existing configurations. The script never emits client secrets or bearer tokens. It validates the running server major as Keycloak 24, the canonical HTTPS URL, and exact operator-supplied ChatGPT callback.

**Caution:** the callback must be copied verbatim from the actual ChatGPT custom MCP plugin setup (client-defined OAuth). Never guess callback, use wildcard, use redirect from DAVI/TÉO, or enter secrets in ChatGPT conversation or GitHub. Plugin UI may differ by plan/workspace. Do not apply unless an exact callback has been shown and security-reviewed.

### Step A: obtain callback, no server changes

1. In ChatGPT Plugins, create a custom plugin/connector pointing to **https://minhadelpi.com.br/apps/linux-ops-mcp/mcp**. If the plugin UI needs public provider discovery, the gateway must first be brought online in a separately approved change; do not substitute an insecure URL.
2. Choose OAuth **user-defined client** (not service token). Note the exact callback URL shown. If callback is not exposed at this stage, stop and verify with platform controls; do not guess.
3. On Keycloak admin console or on srv-api, store the callback **locally**, never in Git or chat; e.g. set `LINUX_OPS_OAUTH_REDIRECT_URI` as environment variable in the shell running the provisioner (prefer interactive prompt without shell history); the script deliberately does not modify `infra/.env`.

### Step B: READ-only preflight and inspect drift

Run from `srv-api` in an authorized shell after updating source from `main` (never reset the local tracked modification automatically). Existing `infra/.env` must have `PUBLIC_BASE_URL`, `LINUX_OPS_MCP_RESOURCE_URL`, and credentials for the existing Keycloak admin client or `KC_ADMIN_TOKEN`; no values should be copied into tickets/PRs/chat.

```bash
cd /home/operador/projetos/delpi-central
python3 infra/scripts/keycloak_linux_ops_client.py --check
```

Expected first run: `[DRIFT] dedicated OAuth client absent` and perhaps `dedicated audience scope absent`, exit 2, or `FAIL_CLOSED` if missing prerequisites. A drift result is not authorization to modify realm.

### Step C: apply only after Keycloak backup and exact callback confirmed

**Do not run until** the ChatGPT callback is obtained, the user authorizes Keycloak change, Keycloak database backup/restore is current and the shared scopes are verified. To avoid placing callback into shell history:

```bash
cd /home/operador/projetos/delpi-central
read -r -p "Exact ChatGPT OAuth callback: " LINUX_OPS_OAUTH_REDIRECT_URI
export LINUX_OPS_OAUTH_REDIRECT_URI
python3 infra/scripts/keycloak_linux_ops_client.py --apply
python3 infra/scripts/keycloak_linux_ops_client.py --check
unset LINUX_OPS_OAUTH_REDIRECT_URI
```

Both operations must succeed; re-running `--apply` must be idempotent. There is **no** Keycloak restart and no gateway restart in this step.

### Step D: real OAuth acceptance

1. In Keycloak `Clients > mcp-linux-ops`, obtain the client secret (only to the ChatGPT OAuth configuration interface). Never print/copy into chats or logs.
2. Use ChatGPT MCP OAuth config with client ID `mcp-linux-ops`, exact redirect, issuer `https://minhadelpi.com.br/auth/realms/delpi`, resource URL, and scopes `openid profile email mcp:tools`; test `client_secret_post` per canonical Delpi MCP runbook.
3. Evaluate an actual **human user's** access token in Keycloak: `aud` includes `delpi-central` and exact Linux MCP resource URL, never other MCP audiences; `scope` contains `mcp:tools`; `azp=mcp-linux-ops`; `iss` canonical realm; no token content in chat.
4. Confirm Core grants `it-portal.access` and `it-portal.servers.view`, plus IT Portal API accepts the bearer. Avoid bypassing Core guard or copying tokens into command history.
5. With gateway route online after separately reviewed deploy, prove metadata 200, unauthenticated MCP 401, and **authenticated** initialize, tools/list (exactly four READ), tools/call get_host_health; negative tests for revoked grant and wrong audience.

## Keycloak rollback / isolation

Disable only `mcp-linux-ops` client in Keycloak and disconnect ChatGPT connector. Avoid deleting generic scopes or changing `delpi-central`, `mcp:tools`, token exchange policies or Keycloak itself. Route rollback is independent; follow `04-cloudflare-existing-gateway-rollout.md`.

## Evidence log

| Milestone | Status |
|---|---|
| Keycloak client provisioner code + isolated tests | CODE_CANDIDATE; CI to verify |
| Production check | NOT_EXECUTED |
| Production Keycloak apply | NOT_EXECUTED |
| Connector callback | NOT_COLLECTED |
| Public gateway route | NOT_DEPLOYED |
| OAuth login + MCP tools/call | NOT_TESTED |
