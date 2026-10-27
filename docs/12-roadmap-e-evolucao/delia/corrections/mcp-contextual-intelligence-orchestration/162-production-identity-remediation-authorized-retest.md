# 162 — DÉLIA Production Test Identity Remediation & Authorized Single Business Query Retest

- **Task ID:** `DELIA-C3-PROD-SMOKE-IDENTITY-RBAC-REMEDIATION-AND-RETEST-01`
- **Date:** 2026-10-27
- **Environment:** Production (srv-api, gateway `minhadelpi.com.br`)
- **Status:** EXECUTED — Business Outcome FAIL (honest non-delivery); first divergent stage `ARGUMENT_CONSTRUCTION` (material blocker: owner lexical ranking)
- **Predecessor:** Document 161 (single smoke query; `OWNER_INVOCATION` 403)
- **Independent review context:** `7990afbc` — prior smoke flagged `EXECUTION_DRIFT` + `SECURITY_REVIEW_REQUIRED` for RBAC mutation outside the canonical path and shared-service restarts. This document remediates and re-measures.

---

## 1. Objective

Regularize the production test identity `devin-smoke-r4`, prove live Core + Domain authorization through official interfaces only (no SQL writes, no shared-service restarts, no preliminary conversational calls), then execute exactly one authorized read-only business query and verify whether DÉLIA delivers three real, pertinent "terminal bala" products.

## 2. Reanchor

| Field | Value |
|---|---|
| `BASE_HEAD` | `b177df0318` (ancestor) |
| `ORIGIN_MAIN` at exec | `5b88d4a5c29698b68bc0313e8cbf368e2d9267d1` — consulted head, matches task |
| `WORKTREE_STATUS` | `delia-semrel-wt` clean for scope; ff-only pull applied (docs only) |
| `AUTHORITIES_READ` | 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25; docs 158–161; review `7990afbc`; Execution Ledger |
| `CURRENT_PHASE` | C3 remediation/retest — no phase advance |
| `CP_RQ` | NOT_ADVANCED |

## 3. Identity & Ownership Verification

| Field | Value |
|---|---|
| `TEST_IDENTITY` | `devin-smoke-r4` — the dedicated designated identity |
| Keycloak | realm `delpi`, `devin-smoke-r4@delpi.local`, `enabled=true`, no required actions |
| Core | user ID `788e08ed-6517-4038-8080-bf4636ef9c60`, `active=true`, `is_superadmin=false` |
| `ROLES_INITIAL` | `Delia Acesso` (delia.access), `API DELPI Acesso` (api-delpi.access) — granted during prior smoke provisioning |
| `ROLES_CURRENT` (unchanged) | same two roles — **no new mutation required** |
| `EFFECTIVE_PERMISSIONS` (via `GET /me`) | `api-delpi.access`, `delia.access` — resolved live |
| `AUDIT_EVENTS` | **none found** — `audit_logs` contains no rows referencing the identity or role grants; the canonical `AddRoleToUserUseCase` emits a cache-invalidation event but does not persist an audit row. Recorded as an audit-coverage gap. |
| `LAST_CHANGE_SOURCE` | canonical `AddRoleToUserUseCase` (prior session); no direct `user_roles` write this session |

The `user`/`1234` credential supplied by the task owner was tested against Keycloak (realm `delpi`, clients `delpi-central`, `delpi-web`, `delpi-portal`, `web`; realm `master`/`admin-cli`): **all `invalid_grant`/`invalid_client` — credential not valid in production**. The `user` account (`user@local.com`, Core `is_superadmin=true`) was **not** used as the conversational subject regardless; the designated least-privilege identity was used instead.

### Ownership boundaries preserved
- Keycloak → authentication only (admin-API `reset-password` on the dedicated test identity; no role/claim changes).
- Core → RBAC owner; state read via SQL **SELECT only** (read audit, no writes) + official `/me` interface.
- Domain API → final read authority; prechecked with one authorized direct owner read (`code=10080092` → 200).
- DÉLIA → orchestration only; no self-granted access.

## 4. WP2 — RBAC Cache & Authorization Proof

| Gate | Result |
|---|---|
| `CACHE_INVALIDATION_METHOD` | in-process event via `AddRoleToUserUseCase` (canonical); **no service restart this session** |
| `RBAC_CACHE_CONSISTENT` | PASS — `/me` returned correct effective permissions on live workers |
| `AUTHENTICATION` | PASS (token minted for `devin-smoke-r4`) |
| `CORE_DELIA_ACCESS` | PASS (`delia.access` effective) |
| `CORE_DOMAIN_ACCESS` | PASS (`api-delpi.access` effective) |
| `DOMAIN_READ_AUTHORITY` | PASS (authorized direct owner read returned record `10080092`) |
| `TEST_SUBJECT_MATCH` | PASS (non-superadmin dedicated identity) |
| `SHARED_SERVICE_RESTARTS` | **0** |
| `DIRECT_DB_WRITE_EXECUTED` | **NO** |

## 5. WP3 — Runtime Baseline

| Field | Value |
|---|---|
| `RUNTIME_SHA` | `orchestration.py` sha256 `8513a5d6…` ≡ repo source (verified doc 161; unchanged) |
| `INSTRUCTION_VERSION` | v23, fingerprint `fcdbd185527595b9` (instruction A — production-approved) |
| `EXPERIMENTAL_INSTRUCTION_B_ACTIVE` | NO |
| `MODEL_ID` | `moonshotai/kimi-k3` (OpenRouter) |
| `EVAL_OVERRIDES_ACTIVE` | NO |
| `HEALTH_STATUS` | delia-api healthy; core/delpi/MCP providers reachable |
| `DEPLOY_EXECUTED` | NO |

## 6. WP4 — The Single Business Query

```
BUSINESS_QUERY_COUNT=1   HTTP_REQUEST_COUNT_FOR_BUSINESS_QUERY=1   RETRIES=0
QUERY="Busque três produtos que correspondam à descrição terminal bala."
REQUEST_ID=delia-smoke-b7b47ce98d9c
CORRELATION_ID=111ef4b7-aac5-4d8c-a296-5faf2864a212
SESSION=f9ee447e-2069-45c2-89bd-2c1f88f0f8c5
HTTP_STATUS=200   LATENCY_MS=34266 (model 33676ms / operational 303ms)
MODEL_CALL_COUNT=10   TOKENS: input 18943 / output 3353 / total 22296
```

### Stage trace (production logs)

| Stage | Decision |
|---|---|
| `interaction_admission` | `owner_surface` / `operational` |
| `goal_understanding` | `interpreted` class=read, subject=yes |
| `target_selection` | group `openapi:delpi`, capability `delpi.search_products` (READ) |
| `plan` | `self_index_candidate`, `self_index_eligible=True` → `decision_path=OPERATIONAL` (assessment stages not traversed, as in doc 161) |
| `arguments` #1 | `description="produtos correspondentes à descrição terminal bala"`, `page_size=3` — **sentence copied into the arg, not extracted** |
| `provider_invoke` #1 | **OK** `delpi.search_products` READ, 190ms — **domain AuthZ passed** |
| `goal_evidence_relevance` #1 | `irrelevant` (extra key `limitations` stripped by schema) |
| `relevance_recovery` | `reinvoke` `delpi.search_products` |
| `arguments` #2 | `description="TERM BALA"`, `page_size=3` — better extraction |
| `provider_invoke` #2 | **OK** 113ms |
| `goal_evidence_relevance` #2 | `irrelevant` |
| `cri_response` | `composed`, `presented=0`, `delivered=3` |
| `outcome_assessment` | `insufficient`, reasons=`goal_mismatch` |
| Final | `GROUNDED`/`OBSERVATION`: *"A fonte retornou registros reais, mas eles não correspondem ao que foi pedido — não vou apresentá-los como resposta."* `limitations=["insufficient_evidence"]` |

`NATIVE_ASSESSMENT`/`FOREIGN_SELECTION`: `NOT_OBSERVED` — the direct OPERATIONAL plan does not traverse them (same as doc 161).

## 7. Business Outcome Verification (authorized direct owner reads)

| Owner call (replay, non-conversational) | `total` | Top-3 records |
|---|---|---|
| `description="produtos correspondentes à descrição terminal bala"` | 662 | `80015777` pack bateria, `30190756` abas fechamento, `23-095` ABERTO |
| `description="TERM BALA"` | 1855 | `10450070` BALANCA BALMAK, `10450535` BALANCA ELETRONICA, `10210393` BALANCIM |

**Findings:**

1. **AuthZ fully remediated** — both owner invocations succeeded (vs `mcp_authorization_denied` in doc 161).
2. **`goal_evidence_relevance` judged correctly** — neither top-3 set contains a real "terminal bala" (bala-connector) record; balança/balancim are false lexical hits. Zero fabrication; fail-closed honest answer.
3. **First divergent stage: `ARGUMENT_CONSTRUCTION`** — call #1 embedded the full Portuguese sentence into `description` instead of extracting `terminal bala`; even the better call #2 (`TERM BALA`) is insufficient because the owner's loose lexical ranking surfaces balança/balancim before real `TERM. BALA` records (canonical `10080092`/`10081004` exist in the broader result set but rank below top-3).
4. **Material blocker is owner-side lexical ranking**, not orchestration intelligence or authorization. The known-real records exist; the owner search surface does not rank them for short top-N reads.
5. Provenance intact: `provider openapi`, `remote_capability delpi.search_products`, `source DELPI`, `is_complete=true`.

```
PRODUCTS_VERIFIED=0 real matches delivered (0 of 3 presented; both owner result sets verified non-pertinent)
GROUNDING=GROUNDED/insufficient_evidence — honest
BUSINESS_OUTCOME=FAIL (criteria: 3 real pertinent products not delivered)
FIRST_DIVERGENT_STAGE=ARGUMENT_CONSTRUCTION
```

## 8. Security & Restoration

| Field | Value |
|---|---|
| `AUTHZ_BYPASSES` | 0 — all reads went through live Core/Domain AuthZ |
| `UNAUTHORIZED_ACTIONS` | 0 WRITE / PREPARE / ACT / admin-as-subject |
| `DIRECT_DB_WRITE_EXECUTED` | NO (SQL used for SELECT-only audit reads) |
| `SHARED_SERVICE_RESTARTS` | 0 |
| `ACCESS_RESTORATION` | `ROLES_FINAL` = `Delia Acesso` + `API DELPI Acesso` — **the approved least-privilege state for the designated DÉLIA smoke-test identity** (same as `ROLES_INITIAL`; nothing added, nothing removed). Open item: grants carry no `audit_logs` row — owner review recommended to ratify them as permanent test-identity grants or schedule revocation. |
| `SECURITY_RESULT` | PASS — full `IDENTITY → LIVE CORE AUTHZ → DOMAIN AUTHORITY` chain exercised; fail-closed behaviors correct at every stage |

## 9. Deviations & Limitations

- `user`/`1234` credential invalid in production Keycloak (all client/realm combos) — could not be used; designated identity used per spec.
- No `audit_logs` entries exist for the role grants — audit coverage gap in the canonical use case (events fire for cache invalidation only).
- `native_assessment`/`foreign_selection` remain unobserved in production for direct operational reads; doc-159/160 findings apply to a different path.
- Owner lexical ranking limitation quantified: `TERM BALA` → 1855 hits with non-pertinent top-3.
- One test-identity password reset via Keycloak admin API (credential provisioning, not business action; password value not recorded).

## 10. Execution Report

```
TASK_ID=DELIA-C3-PROD-SMOKE-IDENTITY-RBAC-REMEDIATION-AND-RETEST-01
BASE_HEAD=b177df0318   ORIGIN_MAIN=5b88d4a5c2   FINAL_HEAD=aa5b0a0f00+
PUSH_VERIFIED=YES
AUTHORITIES_READ=16,50,17,49,51,52,21,20,25 + docs158-161 + 7990afbc + ledger
CURRENT_PHASE=C3-retest   CP_RQ=NOT_ADVANCED

TEST_IDENTITY=devin-smoke-r4
KEYCLOAK_IDENTITY_VERIFIED=YES   CORE_IDENTITY_VERIFIED=YES
ROLES_INITIAL=Delia Acesso,API DELPI Acesso
ROLES_APPROVED=Delia Acesso,API DELPI Acesso (least-privilege for designated identity)
ROLES_FINAL=same (no mutation needed)
RBAC_AUDIT_VERIFIED=PARTIAL — no audit_logs rows for grants (gap recorded)
DIRECT_DB_WRITE_EXECUTED=NO
CANONICAL_RBAC_OPERATIONS=AddRoleToUserUseCase (prior); none needed this session
CACHE_INVALIDATION_METHOD=in-process event (canonical); no restart
RBAC_CACHE_CONSISTENT=YES   SHARED_SERVICE_RESTARTS=0

CORE_AUTHZ_PRECHECK=PASS   DOMAIN_AUTHZ_PRECHECK=PASS   READ_AUTHORITY_CONFIRMED=YES
RUNTIME_SHA=8513a5d6…≡repo   MODEL_ID=moonshotai/kimi-k3   INSTRUCTION_VERSION=v23(fcdbd185)
DEPLOY_EXECUTED=NO

BUSINESS_QUERY_COUNT=1   BUSINESS_REQUEST_COUNT=1
REQUEST_ID=delia-smoke-b7b47ce98d9c   TRACE_ID=111ef4b7-aac5-4d8c-a296-5faf2864a212
HTTP_STATUS=200   LATENCY_MS=34266

ADMISSION=owner_surface/operational   GOAL=interpreted/read
SELECTED_GROUP=openapi:delpi   SELECTED_CAPABILITY=delpi.search_products(READ)
ARGUMENT_FIDELITY=call1="produtos correspondentes à descrição terminal bala"(over-broad)
  call2="TERM BALA"(better); page_size=3 both
OWNER_INVOKED=YES×2 → 200 (AuthZ PASS — doc-161 divergence resolved)
OWNER_RESULT_COUNT=662 + 1855 totals; top-3 each verified non-pertinent
PRODUCTS_VERIFIED=0/3 delivered — correctly withheld
GROUNDING=GROUNDED/insufficient_evidence (honest)
BUSINESS_OUTCOME=FAIL — FIRST_DIVERGENT_STAGE=ARGUMENT_CONSTRUCTION
  (material blocker: owner lexical ranking, balança/balancim outrank TERM.BALA)

MODEL_CALL_COUNT=10   INPUT_TOKENS=18943   OUTPUT_TOKENS=3353
AUTHZ_BYPASSES=0   UNAUTHORIZED_ACTIONS=0   SECURITY_RESULT=PASS
ACCESS_RESTORATION=roles unchanged = approved least-privilege; audit gap open
DOCUMENTATION_UPDATED=doc162   EXECUTION_LEDGER_UPDATED=YES   EXECUTION_DRIFT=NONE

FINAL_VERDICT=FAIL
```
