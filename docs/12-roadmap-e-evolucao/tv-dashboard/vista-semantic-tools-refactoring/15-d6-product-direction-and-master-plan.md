# 15 — D-6 Product Direction and Full Refactoring Implementation Master Plan

**Status:** PRODUCT_DIRECTION_RECORDED / OWNER_APPROVAL_PENDING / IMPLEMENTATION_NOT_AUTHORIZED  
**Recorded:** 2026-10-30  
**Reference baseline:** documentation at `f44a24ec67`; revalidate HEAD, worktree, rules, ADRs, contracts, code, tests, and runtime before executing any stage.  
**Authority:** user-requested product direction is not a substitute for architectural, security, domain, or Core owner approvals.

## 1. Product decision — D-6 amendment

The desired VISTA product scope **INCLUDES all eight blocks**, superseding only the previous D-6 *recommendations* to defer or exclude; it does **not** supersede an existing ADR/contract or authorize writes:

| Block | Desired target | Present evidence / owner | Gate |
|---|---|---|---|
| Playlist settings update | INCLUDE | existing REST PATCH; typed coverage partial; TV domain | TV product/domain + contract |
| Playlist activation/deactivation | INCLUDE | existing REST lifecycle routes; TV domain | TV product/domain |
| Slide duplication | INCLUDE | existing REST endpoint; TV domain | TV product/domain |
| Section reordering | INCLUDE | existing REST endpoint; TV domain | TV product/domain; CAS |
| Media and presets read | INCLUDE | REST read endpoints; TV domain | TV domain; media authorization |
| Playlist deletion | INCLUDE | REST delete but no VISTA typed op; TV domain | security consent + TV owner; destructive read-back |
| History restoration, templates and MDD | INCLUDE | restoration REST exists but intentionally not exposed; template lifecycle and MDD preview/apply have separate contracts | **specific ADR/owner decision per workflow**; compatibility & import security |
| Shares, invitations and permissions | INCLUDE | playlist shares/edit-invites REST exists; Core RBAC governs platform grants; owner and boundaries must be proven | **Core security/RBAC + TV resource owner**; explicit approval for access-grant/revoke, no service-account escalation |

Interpretation: `INCLUDE` = in target roadmap, **not** proof of available semantic capability and **not** READY_FOR_EXECUTION. Do not convert every REST endpoint into typed op. Evaluate reuse of approved domain workflows and their specific mutations. The sixth tool surface remains `get_context/read/analyze/knowledge/execute/delete`; operations may have domain-specific governed adapters without creating a parallel business authority.

## 2. Invariants and implementation gates

- HEAD → Project Instructions → .cursor/rules and responsibility-map → TV canonical README + API README → VISTA capability matrix → ADRs → contracts/owners → implementation/tests/runtime. Conflicts = DOCUMENTATION_DRIFT / CONTRACT_DRIFT / EXECUTION_DRIFT.
- TV Dashboard owns PresentationMutation and presentation writes; Core owns RBAC; Keycloak identity; VISTA adapter only. `VISTA capability <= authenticated user capability`.
- Use `READ CURRENT STATE → PREPARE → CONFIRM if required → COMMIT → AUTHORITATIVE READ-BACK → VERIFY`; opaque server-issued handles, CAS, idempotency, honest PARTIAL_COMMIT and OUTCOME_NOT_VERIFIED.
- No generic SQL/HTTP/proxy, no arbitrary dispatcher, no second registry, renderer, mutation engine, AuthZ, or automatic Action per typed op. Retired surfaces stay retired.
- A target echo verifies target identity, **not human consent**. Consent artifacts require independently verifiable human action, actor/plan/target/proposal binding, TTL, replay protection and audit. Host incapable = fail closed. Granfather exception pending security owner sign-off, never automatic.
- Every bounded implementation must specify `GOAL, OWNER, AUTHORITIES, FACTS, ROOT CAUSE / HYPOTHESIS, EXISTING_EQUIVALENT, REUSE_DECISION, ALLOWED/FORBIDDEN SCOPE, CONTRACT, SECURITY, TESTS, ACCEPTANCE, EVIDENCE, STOP`.
- `ARCHITECTURE_APPROVED`, `SECURITY_APPROVED`, `PRODUCT_SCOPE_APPROVED`, `CONTRACT_APPROVED` and `READY_FOR_EXECUTION` are distinct. All remain PENDING unless recorded by authorized owner; this document is not an approval.

## 3. Program A — semantic surface refactoring

| Stage | Deliverable | Dependencies / independent gate | Tests and acceptance |
|---|---|---|---|
| A0 / E0 | ADR supersession proposal review, 6-verb surface approval, D-1/2/3/4/7/9/10 decisions | Architecture owner formal approval, PR merge and HEAD reanchor | ADR, source/contract traceability, no runtime changes |
| A1 / E2 | Extend neutral `capability_surface` + authenticated `get_context`, with accurate capability states | A0; verify Core/PlaylistAccessService can derive effective permissions | A/B identities, scope negatives, surface↔Actions parity, budget |
| A2 / E3 | `read`, `analyze`, `knowledge` as closed dispatch projections over existing handlers | A1, no Program B new capability prerequisite | legacy↔semantic equivalence, strict filters, schema budget, no unauthorized data |
| A3 / E1 | Trusted confirmation contract and implementation, separate from surface migration | Security owner, consent platform/TV ownership, Portal/host proof, grandfather decision, D-8 owner decision for that subpart | consent provenance, mismatched actor/target/plan, expiry, replay, elicit-incapable, rollback safety |
| A4 / E4 | `execute` facade: prepare with operations[], commit with sealed proposal handle, no operations replacement; single-shot direct only | A0, A1, A3 for confirm-capable behavior | compound plans, CAS, idempotency, partial commit, errors, same owner read-back |
| A5 / E5 | `delete` dedicated semantic tool, sharing canonical mutation workflow | A3 and A4; human consent proof verified by transport | destructive negatives, cross-user replay, no consent → no mutation |
| A6 / E8 | Directives, builder instructions, provenance by channel | A1/A2/A4/A5 as relevant; provenance owner proven | instructions/schema budgets; no duplicated rules; audit |
| A7 / E7 | Deprecate legacy tool projections while retaining operability; removal separately approved | semantic adoption and external consumers demonstrated; ≥2 releases is proposal, not proof | legacy still works; adoption telemetry; deprecation OpenAPI |
| A8 / E9 | Final E2E certification of six tools and 12 legacy surfaces | per-stage tests already passed; runtime/staging smoke as needed | unit, contract, wire, permission negatives, editor-preview-TV parity where affected |

**Scheduling rule:** A1/A2 may proceed after architecture approval while A3 security design is still pending. A4/A5 destructive/confirm execution cannot. E9 is *not* first E2E test: each stage has its own acceptance. Preserve compatibility, never silently downgrade security.

## 4. Program B — full capability expansion (independent bounded waves)

Each entry follows `SYMPTOM → REPRODUCTION/USE CASE → OWNER → CONTRACT → EXISTING_EQUIVALENT → REUSE_DECISION → MINIMAL CHANGE → REGRESSION → VERIFIED OUTCOME`. Initial `EXISTING_EQUIVALENT=TO_INVENTORY` at semantic adapter level until HEAD-level trace. Avoid assuming REST endpoints can be wrapped in PresentationMutation without contract review.

### B0 — Per-capability owner/contract inventory and approvals
- Inspect real routes, services, AuthZ, resource scope, data consumers, history, tokens, concurrency, tests and public/client impacts for **every** included block.
- Record whether the owner allows a typed op, existing command facade, dedicated governed workflow or read-only projection. Explicitly reject generic execution adapters.
- For history restore, MDD, template publish/archive and access-grants, create bounded design decisions before code.
- Outcome: owner matrix with scope, authorization, action/consent and rollback policies; product + security + contract approvals per capability.

### B1 — Lower-risk editor capability parity
- Playlist settings patch, activate/deactivate; slide duplicate; section reorder; media/presets list/get.
- Reuse same backend domain services/REST workflows as editor. Add typed ops only when canonical mutation contract accepts them without duplicating owner behavior.
- Test positive, sibling, negative, branch/resource scope, revision/idempotency, editor/preview/TV parity where presentation changes.
- Independent deployment/rollback per capability; not all B1 items share one mandatory release.

### B2 — Templates and content lifecycle
- Inventory template list/get/create/update, clone, publish/unpublish, archive, import/export if present; decide which administrative writes can be semantically offered.
- Preserve publishing lifecycle, resource-scoped AuthZ, preview and asset semantics; never implement second template engine.
- Tests: unauthorized publish, revision conflicts, consumer parity, published template application and rollback.

### B3 — Destructive and restore workflows
- Playlist delete; history restore; other restoration operations only if owner validates contracts.
- Must wait for A3/A5 security artifact mechanism and domain-specific blast-radius/restore confirmation approval. Restore is not an arbitrary patch.
- Tests: target/proposal/actor/plan binding, no consent, wrong actor, wrong resource, stale revision, partial failure, authoritative read-back and history integrity.

### B4 — MDD import/export
- Reuse schema/versioned portable package owner; separate export, preview, validation, import apply. Preview != apply.
- Validate size, media, paths, content trust, branch permissions, roundtrip, invalid files, version compatibility; govern apply with confirmed plan when risk policy requires.
- No generic binary upload tool through model if transport/contract doesn't safely support it; choose approved handoff workflow.

### B5 — Access shares/invites/permissions
- Confirm authority boundary first: Core permission resolver and TV resource-specific shares/invites. Distinguish **platform RBAC** from **playlist sharing**, invite acceptance, public tokens and role administration.
- VISTA may only propose/execute allowed resource-level operations under current end-user identity. **No** granting self privileges, cross-branch escalation, global Core role modification by default, service-account impersonation, or arbitrary ACL endpoint.
- Access grant/revoke requires explicit security-owned approval/consent policy, audience/recipient and role checks, replay-safe auditing, revocation/read-back, and abuse tests. If Core contract does not allow the requested mutation, mark `BLOCKED_BY_OWNER_CONTRACT` rather than invent permission authority.
- Tests: least privilege, target user identity binding, self-elevation, wrong branch/resource, delegated authority, invitation expiry, revoke, audit.

## 5. Cross-program order and stop conditions

```text
HEAD and baseline → A0 approval
                   → A1 → A2 (read-only semantic delivery)
                   → A3 consent approval/implementation → A4 → A5
                   → A6/A7 → A8 certification
B0 scoped approval → B1 → B2
B0 + A3/A5 → B3
B0 + MDD owner/security approval → B4
B0 + Core/TV security/contract approval → B5
```

B waves do not need to await all A stages unless they depend on their consent/surface contract. Split commits/PRs by owner boundary, do not mix Core RBAC and TV domain mutations in an unreviewed patch. E7 deprecation is not removal; consumer migration evidence is mandatory. Preserve unrelated WIP.

## 6. Acceptance and evidence per bounded step

- Baseline HEAD/base SHA, changed and inspected paths, root cause and equivalent/decision.
- Current contract/operationId/OpenAPI version, schema/error/idempotency/security impact; consumer and deploy map.
- Exact positive + sibling + negative tests, contract conformance, permissions by actor/branch/resource, partial failures and genuine end-user outcome.
- Reuse original renderer/editor-preview-TV parity where payload/slide changes. No claim of parity from build-only.
- Measured performance/observability when materially changed; log correlation without tokens/secrets.
- Rollback for deploy and schema compatibility; explicit migration when consent challenge state is persisted.
- Residual search for parallel authorization/handler, retired aliases, stale instructions, new Actions by accident, owner drift.
- Return `VISTA/TV EXECUTION REPORT` and review `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.

## 7. Decision owners and current gates

| Decision | Owner gate | Status |
|---|---|---|
| A0 six verbs/ADR supersession | Architecture | PENDING |
| D-5 consent mechanism, trust, Portal/challenge, grandfather | Security + contract owner | PENDING |
| D-6 all eight target blocks / each B wave | TV Product/domain, plus Core as needed | PRODUCT_DIRECTION_RECORDED / OWNER_APPROVAL_PENDING |
| D-8 conditional data-model delete policy | TV domain + security | PENDING |
| B3 restore/playlist deletion | TV domain + security | PENDING |
| B4 MDD preview/apply contract | TV MDD owner + security | PENDING |
| B5 shares/invites and permissions | Core RBAC + TV resource authority + security | PENDING |

No runtime modification approved by this plan. Do not mark `DECIDED` in ADR without competent owner evidence.
