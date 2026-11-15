# P1.3 - Private MCP transport and OAuth connection

**Status: source preparation only, no tunnel client installed, no Keycloak client provisioned, no runtime rollout, no ChatGPT connection verified.**
**Owner acceptance:** Linux collector / Portal TI automatic observations operational, confirmed by operator 2026-11-14.
**Change scope:** no production server/container touched in this PR. Existing MCP read-only tools only.

## Selected topology

ChatGPT/approved workspace -> OpenAI Secure MCP Tunnel -> local host `127.0.0.1:<selected-port>` -> opt-in `linux-ops-mcp` container -> `it-portal-api` read endpoint; authenticated resource-bound **human** OAuth + fresh Core RBAC. A tunnel is transport, NOT business authorization.

The existing canonical Compose contains a single opt-in service (profile `linux-ops`). The *only* published port is `127.0.0.1:${LINUX_OPS_MCP_LOOPBACK_PORT:-18765}:8000`; localhost is not reachable from LAN/Internet. `linux-ops-mcp` has no docker.sock, no host bind mounts, no sudo, no shell tool or deploy tool, read-only filesystem and restrictive resources. Tunnel client should be an independent, unprivileged process on the host, not a modification to the existing SSH service.

### OAuth decision and contract

- New **dedicated** Keycloak OIDC client (suggested ID `mcp-linux-ops`), Authorization Code + PKCE S256, exact callback taken from the actual ChatGPT connector registration UI, Direct Access Grants OFF, Service Accounts OFF, Implicit OFF.
- The canonical resource audience `LINUX_OPS_MCP_RESOURCE_URL` is exactly the HTTPS URL shown to ChatGPT, e.g. `https://minhadelpi.com.br/apps/linux-ops-mcp/mcp` **only if that is the actually registered external resource**. The tunnel registration may supply a distinct resource URL. Never mix them.
- `PUBLIC_BASE_URL` must be the same HTTPS origin used in resource audience; wrong origin fails startup. Do not silently bypass validation to accommodate the tunnel.
- `scope`: `openid profile email mcp:tools`; `aud`: include API platform audience (for canonical JWT) **and** exact MCP resource audience via a **dedicated client mapper**; never place resource-specific audience in shared `mcp:tools`.
- Core business permissions: `it-portal.access` and `it-portal.servers.view`; each MCP call refreshes RBAC and forwards original bearer only to the approved in-network IT Portal API endpoint. If Keycloak and the IT Portal API do not accept the *same* narrowly scoped human token, resolve proper token exchange / authorized adapter instead of weakening verification.
- The MCP publishes explicit OAuth `securitySchemes` metadata on all four tools and RFC 9728 protected-resource metadata. Treat an HTTP 401/WWW-Authenticate as expected for an unauthenticated request, but never infer successful OAuth from it.

## Recommended rollout gates (operator on srv-api)

**G0, no host mutation:** source PR + CI tests pass; local checkout divergence resolved **without** `git reset --hard`, `git restore` or blind `pull`. Do not overwrite `shared/delpi_auth.egg-info/SOURCES.txt`, known modified on host. Use separate clean worktree/checkout for any approved build if that is safer.

**G1, OAuth provision:** validate the actual workspace connector supports Secure MCP Tunnel, private server enrollment and OIDC OAuth with the chosen Keycloak issuer/audience. Configure dedicated client after obtaining exact callback from platform; do not paste admin credentials, access token, client secret, API key, tunnel credentials, or .env into conversation/GitHub. Host-only secret store with minimum permissions. All modifications must be explicitly operator-authorized.

**G2, local only start (after merge, explicit authorization, CI):**
- In pre-approved checkout, set only `LINUX_OPS_SERVER_ID`, `LINUX_OPS_MCP_RESOURCE_URL`, Keycloak issuer/JWKS and `PUBLIC_BASE_URL` using the existing canonical env mechanism. Never emit env values on screen.
- Run `docker compose -f infra/docker-compose.yml --profile linux-ops config --services | grep '^linux-ops-mcp$'` to verify profile; `config --services` never prints secrets. Avoid `docker compose config` unredacted.
- Only after operator approval: `docker compose -f infra/docker-compose.yml --profile linux-ops build linux-ops-mcp` then `docker compose -f infra/docker-compose.yml --profile linux-ops up -d --no-deps linux-ops-mcp`. Build might consume host resources: schedule outside critical window; use existing sequential deployment norms. **This is a future runbook, not executed or authorized by this PR.**
- Discover the selected port after startup: `PORT=$(docker compose -f infra/docker-compose.yml --profile linux-ops port linux-ops-mcp 8000 | awk -F: '$1 == "127.0.0.1" {print $NF}')` and verify with `test -n "$PORT"`. A non-loopback address fails this gate. Re-evaluate in each shell. Do not assume the default port when an override is configured.
- Confirm `docker ps --filter name=delpi-linux-ops-mcp --format 'table {{.Names}}\t{{.Status}}'`, then `curl --silent --show-error --fail "http://127.0.0.1:${PORT}/healthz"` and `curl -sS -D - -o /dev/null -X POST "http://127.0.0.1:${PORT}/mcp" -H 'Content-Type: application/json' -d '{}'` should deny unauthorized requests with OAuth challenge. Curl should not include a token.
- Confirm no external listener: `ss -lnt | grep ":${PORT}"` must show `127.0.0.1:${PORT}` only; no 0.0.0.0 or :::.

**G3, private tunnel setup (after G2):**
- Follow *current official* [Secure MCP Tunnels](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) tooling and verify CLI binary/signature and workspace access before installation. Do not invent tunnel commands or presume tunnel entitlement. Keep tunnel credential on host-only secret store. Tunnel forwards only to `http://127.0.0.1:${PORT}/mcp`, never to SSH or Docker. Verify policy for OAuth resource metadata forwarding and Host/Origin allowlists; do not disable transport protections.
- Test and capture sanitized: provider metadata, exact OAuth callback, human login, PKCE, issuer, audience and scopes (never raw token), `initialize`, `tools/list`, `tools/call` for `get_host_health`, Core authorization denied case, stale data behavior and connection teardown.

**G4, fail-close and rollback:** stop/disable **only** tunnel instance and `linux-ops-mcp`; do not restart gateway, Keycloak or databases. Revocation in workspace and Keycloak invalidates connector. All 135 existing containers must be unaffected.

## Open risks / decisions

1. Whether the chosen Secure MCP Tunnel mode advertises the same externally reachable OAuth resource URL as the project and forwards all OAuth discovery paths correctly. If not, adapt resource/metadata contract via a separate reviewed change. **Do not start before compatibility is proven.**
2. Dedicated Keycloak client resource audience must match the URL really used by the tunnel, not an assumed public gateway URL.
3. The current `linux-ops-mcp` transports scoped user bearer to `it-portal-api`; cross-audience AuthN and strict Core policies must be tested end-to-end.
4. `read_only` tool annotations are informational; RBAC and network restrictions still enforce reads.
5. `get_deployment_revision` remains unavailable because production deployed SHA has no authoritative owner report yet.
6. No image rebuild/global deploy of other services or migration is allowed for this milestone.

## Evidence ledger

| Date | Evidence | State |
|---|---|---|
| 2026-11-14 | Owner confirmed Linux collector working | OWNER_ACCEPTED |
| 2026-11-14 | PR #186 merged, image/CI had passed | SOURCE_MERGED |
| 2026-11-15 | Provider-facing OAuth metadata and host-loopback-only candidate with negative tests | SOURCE_IN_PR, CI_PENDING |
| 2026-11-15 | tunnel-client installed, Keycloak client, user OAuth, real ChatGPT, private MCP transport | NOT_DONE |

**Update this ledger after every change with SHA, CI result, reviewed permission/URL, deployment outcome and read-back.**
