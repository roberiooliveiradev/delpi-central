# DAVI-DOCUMENT-TRANSPORT-HOMOLOG-PROVISIONING-001

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`

**Task type:** HOMOLOG PROVISIONING / EXTERNAL BLOCKER HANDOFF

**Homolog provisioned:** `NO`

**Production changed:** `NO`

**Provider spike resumed:** `NO`

**New product capability authorized:** `NO`

## Bootstrap

| Field | Value |
|---|---|
| Previous nonprod baseline | `davi-document-transport-nonprod-remote-001` (INCONCLUSIVE / ABSENT) |
| Intelligence closure HEAD | `b6f566602131887d9ce8e16d4bfde838a30d5f39` |
| BASE HEAD / origin/main | `b6f566602131887d9ce8e16d4bfde838a30d5f39` |
| EXECUTION_DRIFT | **NO** (no post-closure commits touching MCP/OAuth/infra/spike) |

## Verdict

**INCONCLUSIVE**

`HOMOLOG_PROVISIONED = NO`
`HOMOLOG_INFRA_EXTERNAL_ACTION_REQUIRED = YES`
`PROVIDER_SPIKE_RESUMED = NO`
`DOCUMENT TRANSPORT OUTCOME = F` (unchanged)
`MODEL_PDF_VISIBILITY = NOT_PROVEN`

This task does **not** re-inventory the same absence. The external host/DNS/TLS/Keycloak admin/GitHub Environment secret access required to provision remains outside repository authority.

## Gate revalidation (shortest)

| Gate | Status | Note |
|---|---|---|
| HOMOLOG_REMOTE_HOST | ABSENT | unchanged vs nonprod-001 |
| HOMOLOG_PUBLIC_BASE_URL | ABSENT | no invented hostname |
| HOMOLOG_PUBLIC_HTTPS | ABSENT | |
| HOMOLOG_API_DELPI | ABSENT | |
| HOMOLOG_GATEWAY | ABSENT | |
| HOMOLOG_KEYCLOAK | ABSENT | only proven issuer is production realm |
| HOMOLOG_MCP_RESOURCE | ABSENT | |
| GitHub Environment `homolog` | PROVEN_WORKFLOW_NAME_ONLY | vars/secrets still TO_INVENTORY / not configurable from this workspace |

Production protected-resource (read-only): HTTP 200 → resource `https://minhadelpi.com.br/apps/api-delpi/mcp` (unchanged).

## Source hardening delivered (not homolog runtime)

Fail-closed guard when spike is ON:

1. `MCP_RESOURCE_URL` **required**
2. must **not** equal production `https://minhadelpi.com.br/apps/api-delpi/mcp`
3. resolved audience must not fall back to production
4. `PUBLIC_BASE_URL` must not be `https://minhadelpi.com.br`

Owner: `assert_spike_environment_isolated()` in `document_transport_spike.py`, enforced in `create_mcp_server()`.

Without this, missing env would silently advertise production MCP resource while enabling experimental tools — forbidden by §42–43.

## External actions remaining (exact)

### 1. DNS / TLS / host (blocks everything else)

| Requirement | Value |
|---|---|
| Hostname | Distinct from `minhadelpi.com.br` — **must be chosen by infra owner** (do not invent here) |
| DNS | A/AAAA (or CNAME) to homolog host |
| TLS | Publicly trusted CA certificate for that hostname |
| Forbidden | self-signed, ngrok, Cloudflare Tunnel, IP-only HTTPS, local-only names |

### 2. Runtime host

| Requirement | Value |
|---|---|
| Process | Isolated `api-delpi` (same image/code as main) |
| Deploy | Prefer `infra/scripts/up-prod-sequential.sh` pattern on a **non-prod** host — not `srv-api` production |
| Min deps | Keycloak OIDC + MCP + spike; no FILESERVER / Protheus / prod DB required |
| Env | See § Homolog env template below |

### 3. Gateway

Path shape: `<HOMOLOG_BASE_URL>/apps/api-delpi/mcp` (+ protected-resource well-known). Same nginx pattern as production app path; different server_name/certificate.

### 4. Keycloak (manual Admin Console — canonical)

Do **not** edit `mcp-api-delpi`.

Create dedicated client (preferred id if naming confirmed): `mcp-api-delpi-homolog`

| Setting | Value |
|---|---|
| Standard Flow | ON |
| PKCE | S256 |
| Direct Access Grants | OFF |
| Service Accounts | OFF |
| Scopes | openid profile email mcp:tools |
| Audiences | `delpi-central` + **exact homolog MCP resource only** |
| Audience mapper | client-dedicated — **not** nested in shared `mcp:tools` |
| Redirect URI | copy from **new** ChatGPT connector UI (exact; no wildcard after bootstrap) |

### 5. GitHub Environment `homolog`

Configure when host exists (never commit secrets):

| Name | Kind |
|---|---|
| `DEPLOY_SSH_HOST` | secret |
| `DEPLOY_SSH_USER` | secret |
| `DEPLOY_SSH_KEY` | secret |
| `DEPLOY_REPO_PATH` | secret (optional default `/opt/delpi-central`) |
| `DEPLOY_BASE_URL` | variable = homolog HTTPS base |

### 6. ChatGPT

Separate connector: `DAVI Document Spike — Homolog` → exact homolog MCP URL → End-user OAuth. Do not touch production DAVI connection.

## Homolog env template (after host exists)

```text
PUBLIC_BASE_URL=<HOMOLOG_BASE_URL>
MCP_RESOURCE_URL=<HOMOLOG_BASE_URL>/apps/api-delpi/mcp
DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED=true
DAVI_DOCUMENT_TRANSPORT_SPIKE_MODE=resource_link
KEYCLOAK_ISSUER=<approved issuer>
# do NOT set production FILESERVER / Protheus / prod DB merely for spike
```

Expected when spike ON + isolated: tools = 4 (3 + `spike_document_transport_probe`), synthetic resources present.

## Provider spike resume gate

Not eligible until:

```text
PUBLIC HTTPS = PASS
PROTECTED RESOURCE METADATA = PASS
END USER OAUTH = PASS
MCP INITIALIZE = PASS
SPIKE SURFACE = PASS
```

Then resume `DAVI-DOCUMENT-TRANSPORT-PROVIDER-SPIKE-001` LEVEL 2–5 only.

## Production regression (source)

allowlist v9 / 17 / tools 3 / resources 0 / spike OFF / READ-only / intelligence 2026.09.24.2 unchanged by this task’s intent.
