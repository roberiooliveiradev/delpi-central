# P1.4 - HTTPS MCP via existing DELPI Cloudflare + Nginx

**Status:** CODE_IN_PR; NOT_DEPLOYED, NO_KEYCLOAK_CLIENT, NO_CHATGPT_CONNECTOR.
**User constraint:** zero incremental subscriptions, no OpenAI API metered calls.
**Owner:** DELPI infrastructure + security. Production gateway is a shared critical component.

## Facts / scope

- Linux Ops MCP already built and running on srv-api as an opt-in Docker Compose service.
- Operator reported `healthy`, `http://127.0.0.1:18765/healthz` returns read-only OK, `POST /mcp` without auth returns 401 and OAuth PRMD returns 200.
- `LINUX_OPS_MCP_RESOURCE_URL` is `https://minhadelpi.com.br/apps/linux-ops-mcp/mcp` (reported local PRMD).
- Existing `cloudflared` and Nginx gateway already front the domain, but end-to-end Cloudflare policy/routing for the **new** path is NOT YET VERIFIED.
- This PR adds one shared Nginx snippet included in existing prod/dev gateway configs and a self-contained CI syntax/security test. Does not touch Docker Compose, Keycloak, cloudflared, credentials, databases, other services, host listeners, or MCP API code.

## Exposure model

```text
ChatGPT MCP connector (OAuth user)
   HTTPS https://minhadelpi.com.br/apps/linux-ops-mcp/mcp
     -> existing Cloudflare Tunnel + existing Nginx gateway
       -> Docker network linux-ops-mcp:8000 (same existing container)
         -> IT Portal API READ observation, user bearer + fresh Core RBAC
```

- Paths forwarded by gateway only:
  - `/apps/linux-ops-mcp/mcp` and optional trailing slash, GET/POST/DELETE according to MCP transport (Bearer required);
  - `/apps/linux-ops-mcp/.well-known/oauth-protected-resource`, GET metadata (public).
- ALL other `/apps/linux-ops-mcp/` paths return 404, including `healthz`, `docs`, shell or operational/admin endpoints.
- Upstream uses dynamic name resolved through Docker `resolver 127.0.0.11`; profile-off must not prevent gateway startup, which would happen with an unconditional static upstream resolver.
- Rate limit, limited request size, auth header forwarded, buffering off, no-store and sanitized access logs. No change to listening ports or Cloudflare hostname.
- LOCAL bind `127.0.0.1:18765` remains available only to host; gateway connects on existing Docker network; no public port for SSH/terminal/Docker.
- Healthcheck / 401 are smoke evidence ONLY: no end-user OAuth and `tools/call` proven until explicit authenticated test.

## Gates, order and rollback

**G0 - PR review + CI:** architecture enforcement, `gateway/tests/test_linux_ops_mcp_gateway.py` and `nginx -t` harness must pass. Merge must be authorized. Confirm no security review issues. No direct config edits in production.

**G1 - OAuth BEFORE external enablement:**
1. In existing Keycloak realm `delpi`, register one dedicated OAuth client `mcp-linux-ops` with Auth Code + PKCE and callback copied **exactly** from ChatGPT connector UI. Disable implicit/direct-grant/service-account flows. Keep client credentials only in Keycloak/ChatGPT configuration, never in Git/chat.
2. Dedicated resource audience mapper on this client: `https://minhadelpi.com.br/apps/linux-ops-mcp/mcp`, plus canonical `delpi-central` audience. Scope `openid profile email mcp:tools` (optional `offline_access` only when requested); never put resource URL mapper in shared `mcp:tools` client scope.
3. User needs `it-portal.access` and `it-portal.servers.view` from Core; no Docker/systemd/deploy permission created.
4. Validate exact issuer/resource metadata over HTTPS, authorized token audience, scope and subject **without posting token values**. Confirm ChatGPT workspace permits custom MCP OAuth and endpoint use. **If callback cannot be obtained or auth is untested, do not publish the route yet.**

**G2 - isolated gateway build/test (authorized change window):**
```bash
cd /home/operador/projetos/delpi-central
git status --short
git pull --ff-only origin main  # only if current checkout and local modifications allow fast-forward safely
cd infra
docker compose -f docker-compose.yml --env-file .env build gateway
docker compose -f docker-compose.yml --env-file .env run --rm --no-deps --entrypoint nginx gateway -t
```
No `docker compose config` output (may expose secrets), no blanket `up` and no restart yet. Existing local modified `shared/delpi_auth.egg-info/SOURCES.txt` must not be auto-discarded.

**G3 - controlled gateway publication AFTER G0-G2 and AuthZ proof:**
- Record running image/container revision, take backup of gateway config/image, check critical services and select short change window.
- Recreate **only** gateway; do NOT run `up --build` or any global sequential deployment command. An approved command is:
```bash
docker compose -f docker-compose.yml --env-file .env up -d --no-deps --no-build gateway
docker exec delpi-gateway nginx -t
docker ps --filter name=delpi-gateway --format 'table {{.Names}}\t{{.Status}}'
```
This changes the existing critical gateway; may briefly interrupt the portal. **Never run on a failed preflight.**
- Verify existing homepage + Keycloak + existing critical API health, and **only then**:
```bash
curl -fsS -H 'Host: minhadelpi.com.br' http://127.0.0.1/apps/linux-ops-mcp/.well-known/oauth-protected-resource
curl -sS -o /dev/null -w '%{http_code}\n' -H 'Host: minhadelpi.com.br' \
  -H 'Content-Type: application/json' -d '{}' \
  http://127.0.0.1/apps/linux-ops-mcp/mcp   # expects 401 without Bearer
curl -sS -o /dev/null -w '%{http_code}\n' -H 'Host: minhadelpi.com.br' \
  http://127.0.0.1/apps/linux-ops-mcp/healthz # expects 404
```
- Verify HTTPS via Cloudflare externally, 200 PRMD with exact resource and 401 MCP challenge. Do not share access tokens, secrets, full config or raw logs.

**G4 - live end-to-end authentication:** ChatGPT connector OAuth using dedicated Keycloak client, `initialize`, `tools/list` four approved READ tools and `tools/call get_host_health`; test revoked Core permission and wrong audience returns deny. Record evidence and timestamp only.

**Rollback:** if gateway fails health or other apps degrade, restore last known good gateway image/config and recreate **only** gateway; record old image digest before deployment and do not rely on mutable `latest` as a rollback target. For emergency exposure isolation without full gateway recreation, pause or disconnect custom MCP connector and/or stop only `linux-ops-mcp`, which will result in an unavailable route, while existing gateway stays online. A proper *full* route rollback requires rolling back the versioned gateway configuration and validated gateway image in a separate controlled step. Never stop Keycloak, Docker daemon or other applications.

## Source files

- `gateway/snippets/linux-ops-mcp-locations.conf`
- `gateway/nginx.conf` and `gateway/nginx.dev.conf` (single include each)
- `gateway/tests/nginx-linux-ops-mcp-test.conf`
- `gateway/tests/test_linux_ops_mcp_gateway.py`
- `.github/workflows/linux-ops-mcp-gateway.yml`

## Evidence ledger

| Item | Status |
|---|---|
| MCP local / OAuth metadata / unauth 401 | OPERATOR_VERIFIED |
| Nginx snippet + regression suite | CODE_IN_PR / CI_PENDING |
| Keycloak dedicated client + exact callback | NOT_DONE |
| New Cloudflare HTTPS route live | NOT_DONE |
| ChatGPT login + tools/list + tools/call | NOT_DONE |
| Additional recurring cost | NOT_AUTHORIZED |
