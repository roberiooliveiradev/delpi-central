# 184 — DÉLIA · DAVI-Only Production Deploy and Runtime Validation

**Date:** 2026-10-28. **Task:** `DELIA-C3-DAVI-ONLY-GOVERNED-PRODUCTION-RELEASE-02`. **References:** docs 174, 181 (+independent review), 182, 183; Execution Ledger. **Implementation SHA:** `269d5276b092d7f6e3fb7ce0a69350c5710b066f`. **Status:** DEPLOY_EXECUTED; RUNTIME_BOUNDARY_VERIFIED; READ_TESTS=TEST_NOT_RUN; BUSINESS_OUTCOME=INCONCLUSIVE.

## 1. Reanchorage

BASE_HEAD=`48afe2ba860ccf9ec5956f7aca7016b39b0d9059` (main, includes owner-disposition ledger entry). Verified: no commit after `269d5276b0` touches `delia-api/`, `api-delpi/`, shared or compose scope; `269d5276b0` remains the effective boundary implementation. Authorities 16, 50, 17, 49, 51, 52, 21, 20, 25 and docs 174, 181–183 read. Phase C3 unchanged; no CP/RQ advance.

## 2. Security gate disposition

Owner declared in session: the exposed credential is a **test key** and was never pushed to GitHub; instructed removal of every non-`.env` key record, then deploy. Executed remediation:

- Repo scan: no real key values (placeholders only) — consistent with owner statement.
- Local artifacts sanitized by equal-length byte redaction (no values printed):
  `sessions.db` 156 occurrences, `sessions.db-wal` 15, history summary `history_33aa1692a2ea4d4c.md` 2 — **173 total**.
- `.env` files preserved per explicit owner instruction.
- Post-redaction value-aware verification: **0 real key values** remaining (remaining regex-shaped strings are the `sk-or-v1-RRR…` redaction markers).
- Caveat recorded: WAL could not be checkpointed (CLI DB locked); redacted directly.

Recorded in the ledger under the owner-disposition entry: `EXTERNAL_EXPOSURE=REMEDIATED-LOCALLY`, `SECURITY_OWNER_DECISION=ACCEPT/CLASSIFIED-TEST-KEY`, `RISK_ACCEPTANCE=RECORDED`, `RELEASE_SECURITY_GATE=PASS` (per doc 183 disposition, completed by executed local remediation). Docs 174, 182, 183 preserved — no incident record was deleted.

## 3. Pre-deploy and rollback

- Production checkout advanced `git pull --ff-only` → `48afe2ba86` on `srv-api:~/projetos/delpi-central`.
- Baseline: v24 DÉLIA runtime (pre-boundary-removal image). Rollback procedure: redeploy previous image/checkout of `delia-api` via canonical script; not executed.
- `infra/.env` on server had 4 dead `DELIA_OPENAPI_*` vars injected via `env_file` (3 `DELIA_OPENAPI_DELPI_*` + `DELIA_OPENAPI_TIMEOUT_SECONDS`) — removed as dead config matching the code removal; `.env.bak-delpi-openapi` backup kept on server.

## 4. Deploy execution

Canonical: `./infra/scripts/up-prod-sequential.sh --build delia-api`. Only `delia-api` rebuilt/restarted.

- DEPLOYED_CODE_SHA=`48afe2ba86` (build context HEAD; contains implementation `269d5276b0`)
- DEPLOYED_IMAGE_DIGEST=`sha256:9947eac96f471f55b9ea4de5c67675b962261ded9d07c047e8f4e02de3fad1c8`
- CONTAINER=`delpi-delia-api` Up (healthy); `GET /health` in-container = 200.
- Model, CRI, DAVI, API DELPI, Keycloak, RBAC: unchanged.

## 5. Runtime boundary verification (executed against the running container)

| Check | Result |
|---|---|
| `DELIA_OPENAPI_*` env vars in container | **0** (after .env cleanup + recreate) |
| `openapi_declarations.delpi.json` in image `/app/config` | **absent** |
| Settings attrs (`openapi_delpi_*`, `openapi_timeout_seconds`) | **all False** (removed) |
| Composer `_wire_openapi_provider` / `source_id="delpi"` | **0 matches** |
| `DELIA_MCP_DAVI_ENABLED/BASE_URL/HOST_HEADER` | present (DAVI-only path intact) |
| `DIRECT_DELPI_PROVIDER` | **0** |
| `DIRECT_DELPI_CAPABILITIES` | **0** |
| `DIRECT_DELPI_FALLBACK` | **0** (no provider to fall back to) |
| DAVI MCP surface `…/apps/api-delpi/mcp` | **401** — mounted, AuthZ enforced |
| DÉLIA unauthenticated interaction | **401** — fail-closed |

## 6. READ tests T1–T6 — TEST_NOT_RUN

No authorized identity token is available. Prior runs minted a bearer via a Keycloak password reset, which doc 173 classified as an unauthorized identity write and explicitly prohibited repeating; this task also forbids obtaining tokens via password reset. Without a legitimately provisioned identity, production business queries cannot be exercised:

- DAVI_DISCOVERY / DAVI_EXECUTION: TEST_NOT_RUN (endpoint mounted + 401 challenge = surface live and fail-closed; not a full tools/list).
- AUTHZ: structural PASS at ingress (unauth → 401 on both surfaces); scenario T6 TEST_NOT_RUN.
- BUSINESS_OUTCOME: **INCONCLUSIVE** — not claimed.
- MODEL_CALLS/TOOL_CALLS/TOKENS/LATENCY: N/A.

## 7. Residuals

- `get_product_summary` / `search_customers`: legitimately unavailable through DAVI — no fallback exists by construction.
- Prod `.env` cleanup done server-side (not committed; env files are untracked).
- WAL redaction caveat in §2.

## 8. Verdict

`LOCAL+RUNTIME_PASS_WITH_RESIDUAL` — DAVI-only boundary verified in the running production container (provider/capabilities/fallback all structurally 0; DAVI surface live and authz-enforced). Business Outcome inconclusive pending a legitimately authorized identity. **Next C3 step:** resume intelligence track (semantic selection, contextual recovery, LLM efficiency, evidence quality) — no DAVI/API-DELPI scope expansion.
