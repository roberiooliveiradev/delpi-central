# DAVI-DOCUMENT-TRANSPORT-NONPROD-REMOTE-001

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`  
**Task type:** NONPRODUCTION REMOTE MCP INVENTORY / HANDOFF  
**Implementation authorized:** `NO`  
**Production runtime changed:** `NO`

## Bootstrap

| Field | Value |
|---|---|
| Last observed main | `a70c30dbc416764edcfcb560172c51c6d5623032` |
| BASE HEAD / origin/main | `3bbe711dc5bc0b97aaa3a30ff4b10ad4e7ed79e4` |
| Inventory ancestor | `3193c398c` — still ancestor |
| Spike ancestor | `a70c30dbc` — still ancestor |
| EXECUTION_DRIFT | **NO** — commits after the spike do not change api-delpi MCP, OAuth, Keycloak, gateway, DAVI allowlist, document spike, or drawing routes. TÉO MCP tool-count note in the shared onboarding runbook is unrelated. |

## Verdict

**INCONCLUSIVE**

`NONPROD_REMOTE_MCP = ABSENT`

`BLOCKER = external homolog runtime not provisioned`

Production MCP was not used as the experiment environment. Spike flag was not enabled anywhere.

## Homolog classification

| Gate | Value | Evidence |
|---|---|---|
| HOMOLOG_GITHUB_ENV | **PROVEN** as workflow name only | `.github/workflows/sync-api-delpi-openapi.yml` choice `homolog` / `prod` |
| GitHub Environment variables/secrets | **TO_INVENTORY** | `gh` not installed; git credential absent; unauthenticated `GET /environments/homolog` returned `404` (ambiguous on a private repo) |
| HOMOLOG_REMOTE_HOST | **ABSENT** | No homolog hostname, SSH host, or compose target in `infra/` or ops docs. Only proven runtime host is production `srv-api` (`192.168.1.237`) |
| HOMOLOG_PUBLIC_HTTPS | **ABSENT** | Only proven public HTTPS MCP host is `https://minhadelpi.com.br` |
| HOMOLOG_API_DELPI | **ABSENT** | No second api-delpi runtime |
| HOMOLOG_KEYCLOAK | **ABSENT** | Only proven issuer is `https://minhadelpi.com.br/auth/realms/delpi` |
| HOMOLOG_REMOTE_MCP | **ABSENT** | Production protected-resource metadata still returns `https://minhadelpi.com.br/apps/api-delpi/mcp` |

These gates were not inferred from each other. CI environment **name** does not prove a reachable host.

## Production probe (read-only)

`GET https://minhadelpi.com.br/apps/api-delpi/.well-known/oauth-protected-resource` → HTTP 200

| Field | Value |
|---|---|
| resource | `https://minhadelpi.com.br/apps/api-delpi/mcp` |
| authorization_servers | `https://minhadelpi.com.br/auth/realms/delpi` |
| scopes | `openid profile email mcp:tools` |

Production client `mcp-api-delpi` was not modified.

## Why provisioning stopped

Section 21 forbids inventing a hostname or using an unapproved tunnel. Section 35 forbids touching production when no usable homolog remote exists. There is no proven homolog base URL from which to derive `/apps/api-delpi/mcp`.

Keycloak client creation was not attempted. Canonical provisioning today is the manual runbook `api-delpi/docs/integrations/keycloak-mcp-client-runbook.md` (Keycloak Admin Console), not Terraform/realm export in this repo.

`KEYCLOAK_PROVISIONING = PENDING_EXTERNAL_ACTION` — only after a homolog host exists.

## Infrastructure handoff

Do not enable `DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED` on `https://minhadelpi.com.br/apps/api-delpi/mcp`.

Required external capability, in order:

1. **Host / DNS.** A public homolog hostname distinct from `minhadelpi.com.br`, with a valid CA certificate (no self-signed cert). Do not use ngrok, Cloudflare Tunnel, or an ad-hoc public tunnel.
2. **Gateway.** Same application path shape: `<PROVEN_HOMOLOG_BASE_URL>/apps/api-delpi/mcp`. Exact resource URL is recorded only after the host is proven.
3. **Runtime.** Isolated api-delpi process. Minimum dependencies: Keycloak OAuth + MCP + synthetic spike. Do not mount production FILESERVER, Protheus, or production secrets just to make business tools succeed. Normal DAVI tools may fail closed.
4. **Spike flag (homolog env only).** `DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED=true` and `DAVI_DOCUMENT_TRANSPORT_SPIKE_MODE=resource_link`. Also set `PUBLIC_BASE_URL` and `MCP_RESOURCE_URL` to the homolog resource so protected-resource metadata does not advertise the production URL. Code already resolves audience from those env vars (`oauth_contract.resolve_required_mcp_resource_audience`).
5. **Keycloak.** Do not edit client `mcp-api-delpi`. Preferred new client `mcp-api-delpi-homolog` only if platform naming is confirmed at provision time. Authorization Code + PKCE S256; Standard Flow ON; Direct Access Grants OFF; Service Accounts OFF; scopes `openid profile email mcp:tools`; audiences `delpi-central` and the **exact homolog MCP resource only**. Redirect URI = the ChatGPT connector return URL copied from the **separate** test connector, not the production DAVI connector. Audience mapper must not be nested in shared scope `mcp:tools`.
6. **GitHub Environment `homolog`.** Confirm or create it, then set (values not invented here): `DEPLOY_SSH_HOST`, `DEPLOY_SSH_USER`, `DEPLOY_SSH_KEY` (secret), `DEPLOY_REPO_PATH` (secret), `DEPLOY_BASE_URL` (variable) pointing at the homolog base URL. Presence of these on the current Environment is **TO_INVENTORY**.
7. **ChatGPT.** Separate connector display name such as `DAVI Document Spike — Homolog`. Do not edit the production DAVI connection.

After that exists, re-run LEVEL 2–5 of `DAVI-DOCUMENT-TRANSPORT-PROVIDER-SPIKE-001`. Until then `MODEL_PDF_VISIBILITY = NOT_PROVEN` and architecture OUTCOME remains **F**.

## Source tests

`pytest tests/test_davi_document_transport_provider_spike.py tests/test_external_capabilities_mcp.py tests/test_mcp_oauth_contract.py tests/test_davi_product_drawing_capability.py` → **75 passed**.

Default-OFF production surface remains 3 tools / 0 resources (covered by those tests). Homolog deploy, remote MCP, OAuth live, and ChatGPT provider tests: **TEST_NOT_RUN**.
