# Delpi Linux Operations MCP — P1 READ-ONLY candidate

**Status:** source candidate, **not deployed**. No production connection, tunnel, Keycloak client, CI pass, health smoke, or user authorization has been proven. The public repository must not contain secrets or runtime log outputs.

## Scope and reuse

Four typed READ tools; no ACT/PREPARE; no SSH, subprocess, shell, Docker socket, SQL or arbitrary filesystem access:

- `get_host_health`: curated CPU/RAM/swap/root disk and freshness.
- `list_managed_services`: allowlisted systemd unit states and Docker aggregate counts. **No container list**, since collector summary is intentionally limited.
- `get_service_health`: allowlisted systemd unit. Service status is the *last observation*, **not current probe**.
- `get_deployment_revision`: returns **not_available** until there is a canonical attested deployed-SHA source. GitHub HEAD is **never** reported as production revision.

Data owner: existing `it-portal-api` `GET /servers/{server_id}/observations/latest`, permission `it-portal.access` and `it-portal.servers.view`; HTTP GET only. Existing Linux collector owns observation ingestion. No duplicate inventory collector, migrations, API schemas or gateway configuration.

MCP AuthN reuses `delpi_mcp.auth.mcp_transport_auth`, `delpi_auth` JWT validation and RBAC context, `delpi_mcp.resource_contract` metadata/challenge and `delpi_mcp.transport`. The IT Portal backend **independently rechecks** its permissions against the same human bearer. Any unavailable Core RBAC, bad issuer/aud/scope, missing permissions, stale token or service identity fails closed. Stale **observation** is allowed but explicitly labeled stale.

## Configuration (no secret values in Git/chat)

Required runtime env, in approved canonical env storage:
- `LINUX_OPS_IT_PORTAL_URL=http://it-portal-api:8000`: fixed internal service URL. The adapter denies outbound URLs except local IT Portal approved hosts.
- `LINUX_OPS_SERVER_ID=<existing UUID>`: registered srv-api ID (no new server).
- `LINUX_OPS_MCP_RESOURCE_URL=https://.../apps/linux-ops-mcp/mcp`: **exact OAuth audience** for approved transport.
- `KEYCLOAK_ISSUER=https://.../auth/realms/delpi`: real trusted issuer.
- `PUBLIC_BASE_URL=https://...`: transport host/Origin allowlist derivation.

**Do not create arbitrary new compose/env files**: `.cursor/rules/platform-delivery-runtime-operations.mdc` requires use of existing canonical sources. This candidate **does not modify** `infra/docker-compose.yml`, `.env.prod.example` or gateway yet. Runtime deployment must be a separate, reviewed and authorized change.

## Preflight before ANY runtime deployment

1. Review status of PR #184 and the P1 PR, run local tests/CI with shared repo packages and `mcp>=2,<3`, static security scanners and type/import checks. These tests are **not executed** by a code-only GitHub commit.
2. Resolve unclean production checkout without `restore`/`reset` by automation. Check local git SHA against verified remote; do not assume modified `shared/delpi_auth.egg-info/SOURCES.txt` is safe to overwrite.
3. Check Linux collector S2S installation, latest observation populated, freshness/sections. A missing observation must return `unavailable`, never fabricated live host data.
4. Select transport after verify of Secure MCP Tunnel entitlement, or use canonical OAuth via gateway; this repo does not deploy or configure tunnel-client.
5. Register Keycloak dedicated client and exact redirect (from ChatGPT), resource audience, `mcp:tools` and Core permissions using existing onboarding runbook. No secret in Git.
6. Deploy MCP process as non-root/non-docker, read-only root filesystem, no host namespace, no SSH agent, no bind of `/var/run/docker.sock`, no `infra/.env` mount, no arbitrary network egress, bounded CPU/RAM, healthchecks, stdout redaction and HTTPS/tunnel.
7. Test negative cases: no/invalid token, wrong audience, missing scope, wrong principal, revoked Core permission, Core outage, upstream 401/403/503, malicious observation fields, stale data, invalid service name, URL spoofing and no-capability to run commands.
8. Prove a real authenticated ChatGPT `tools/list`/`tools/call` against `srv-api`, with timestamps and sanitized evidence. Only then mark P1 runtime verified.

## Development checks (local only, not srv-api)

Install the pre-existing shared packages from the checkout's package files in a **temporary venv**, together with `requirements.txt`; do not use `pip` global or change production packages.

```bash
cd linux-ops-mcp
PYTHONPATH=. pytest -q tests/test_reader.py
python -m compileall -q linux_ops_mcp
```

The package is intentionally not wired into Docker or the public gateway until security review. **No pull/deploy recommended at P1 code-delivery time.**

## Decision and documentation log

| Date | Event | Status |
|---|---|---|
| 2026-11-14 | Host inventory: Ubuntu 24.04.4, 16 CPU, 47 GiB RAM, 135 running containers, health filters empty | OPERATOR_REPORTED |
| 2026-11-14 | Local `origin/main` SHA differs from running checkout SHA, working tree has 1 tracked changed file | DRIFT_TO_INVESTIGATE |
| 2026-11-14 | Source candidate with 4 read-only MCP tools and pure tests | CODE_CANDIDATE / TEST_NOT_RUN |
| 2026-11-14 | Agent installed, token connected, tunnel created, host touched | NOT_DONE |

Next step is evidence of `it-portal-api` Linux observation ingested + authenticated smoke in a non-production environment.
