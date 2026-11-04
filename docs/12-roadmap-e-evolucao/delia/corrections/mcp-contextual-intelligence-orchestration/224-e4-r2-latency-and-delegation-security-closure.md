# 224 — DÉLIA · E4 R2 — latency and delegated-credential security closure

**Date:** 2026-11-03. **TASK_ID:** `DELIA-C3-E4-R2-LATENCY-DELEGATION-AND-DELIVERY-CLOSURE-01`. **EVIDENCE_SHA:** `23648e9ee0` (verified main at coordination review). **STATUS:** `REWORK_REQUIRED`; previous SR01–SR04 etc as executor-reported, not independent real-model pass. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**. Reanchor actual HEAD/status before any diff.

**AUTHORITIES:** .cursor + 16→50→17→49→51→52→21→20→25, ADR58, PO budget doc103, 219–223, ledger, live AuthZ and owner contracts. Follow plan-construction/plan-execution and evidence-driven-execution. Phase/CP/NEXT must be verified on current HEAD; no phase advancement implied.

## 1. Findings and status

- In real local live test, `compare as duas` completed `so_1..3` through DAVI real reads and `evidence_composition decision=differences_found sources=2`, `COMPLETED×4` server-side. **Business outcome at client FAILED: gateway HTTP 504, ~131s elapsed vs ~120s gateway timeout.**
- Auth failure previously observed: JWT of request subject expired after long admission/goal/decomposition; `credential_for` previously rejected before returning a still-valid delegated token. New code `app/infrastructure/interoperability/delegation.py` checks (fingerprint of current subject bearer, resource audience) cache before subject-exp check; cache TTL is limited by delegated-token exp, fixed cap and margin, and invalidation exists. This can be protocol-legitimate but **does not prove continued live business authorization** or revocation handling. Security review mandatory before accepting.
- Source id now comes from owner record's root code, but suffix `#{len(sources)}` is positional rather than explicit occurrence provenance. Treat as provisional identification/disambiguation, not a proven canonical EvidenceRef. Ensure typed owner/capability/record/occurrence refs remain intact; do not conflate two records from different owners sharing code.
- Current graph path is sequential in `_investigate_subobjectives`, which invokes `_governed_owner_path` for each subobjective. Four generated subobjectives include an analysis step that may be unnecessary to answer comparison of already authorized read evidence. Optimize through semantic relevance and existing subobjective graph; no hardcoded product codes or provider branches.
- Do not classify 504 only as gateway misconfiguration; reconcile global interaction 300s, individual 60s and retries with user-visible gateway delivery (~120s), streaming heartbeat/NDJSON and cancellation. A 300s application budget cannot by itself assure a response through a 120s HTTP gateway.
- G04/G05/G07/G12 and SR05/SR06 remain NOT ACCEPTED until client receives accurate grounded comparison within effective transport contract.

## 2. Mandatory security gate on delegated-token cache

**First establish authorization semantics before retaining the change unchanged.**
1. Map authentication vs authorization chain: incoming subject bearer validated at admission; token exchange validates `sub`, `azp`, `aud`, `scope`, exp; Core live AuthZ and Domain owner final policy at each sensitive operation. Identify the exact consumer where a cached token is used and whether a live Core check occurs before each READ. Never equate delegated token validity with current Core authorization.
2. Test subject JWT expired while delegated token is valid (same scope, identity/resource, valid original admission): protocol continuation should be explicitly allowed only if current policy and owner authorize it. Test subject JWT revoked, disabled subject, lost permission/group, session invalidation, audience change, different user, different token fingerprint, mismatched subject, expired delegated TTL, cache invalidation after MCP 401, missing bearer, malformed bearer, old bearer replay in a new request. Confirm fail-closed behavior for new requests, even if an earlier in-flight request can finish under a legitimate already-issued delegation.
3. If the existing Core/Domain gate does not enforce real authority for a cached token, STOP or correct within canonical owner before retaining cache-first behavior; do not invent local user-authorization engine. No permission/grant changes.
4. Document whether ongoing mid-turn continuation is distinct from accepting a new request with expired user bearer; cache reuse may never authorize a new HTTP request. Do not claim revocation support unless verified against actual current Core/Domain semantics.
5. Run security tests with deterministic clocks and real authorized local Keycloak/Core/DAVI probes for effective behavior (no secrets in logs).

**Gate SEC-01:** `PASS` only with demonstrated valid exchange, subject/session isolation, live authorization at legitimate boundary, bounded TTL, negative revocation/expired/new-request cases; otherwise `REWORK` or `ARCHITECTURE_DECISION_REQUIRED`.

## 3. Latency root-cause budget and minimal optimized execution

1. Capture full per-stage wall-clock and token timelines on same local Qwen3 and live DAVI, including admission, turn_goal, decomposition, 4 subobjectives, discovery→execute, `evidence_composition`, synthesis, gateway/NDJSON, after-response work, retries and remaining `TurnDeadline`.
2. Reuse actual LangGraph fan-in/subobjective tracker; minimize redundant subgoals **semantically**. For a request to compare two legitimate read-authorized evidence sets, two verified READ evidence branches and one composition stage are normally sufficient. Do not add unconditional foreign analysis, do not bypass a required owner when its analysis is materially distinct. Confirm existing frozen `skip_comparison_declared` / owner selection contract.
3. Reuse existing goal-aware candidate selection/resume/proposal cache and avoid repeating semantic selection, model invocations and discovery when an authorized semantic result/candidate is still valid. Do not cache business facts without owner revalidation. Do not code keyword/ID-specific rules.
4. Investigate LangGraph `Send` fan-out for independent authorized READ subobjectives only if current engine actually supports it with safe propagation of request identity, contextvars, deadlines, call budget, cancellation, model concurrency and result ordering. Avoid speculative parallelism or racing RPCs with shared mutable state; sequential path acceptable if verified within user-facing budget.
5. Address effective transport deadline as an **end-to-end constraint**: finish or communicate an honest terminal through supported streaming before actual gateway closure. Never fix by changing nginx timeout only; if product requirement genuinely needs >120s, present an explicit contract-level option (streaming heartbeat/progress or approved timeout negotiation) with tests for client/browser and gateway, before deployment.
6. No new planner, stage engine, context service, owner or permission. No unaudited user token refresh inside an agent.
7. Confirm that top-level comparison status depends on verified complete outcome, not `COMPLETED×4` labels alone; inspect rendered final values and compare to deterministic oracle. Unknown/partial/denied must stay honest.

## 4. Full functional acceptance matrix (final SHA)

| ID | Required proof |
|---|---|
| LAT01 | actual post-fix per-stage timing/tokens, retries and gateway/turn budget compatibility |
| LAT02 | no redundant foreign analysis unless user goal/owner contract requires it |
| LAT03 | same-session A01→A02→A03/A04 delivers HTTP/stream terminal *to client* with grounded comparison |
| LAT04 | single-turn compound comparison delivers grounded response to client |
| LAT05 | repeated/long-context Qwen3 tests stay within product latency policy or surface correct bounded limitation, no 504 churn |
| LAT06 | final fact comparison equals independent real owner-backed oracle incl `10030012` exclusion and `10030015` inclusion |
| LAT07 | unauthorized, stale, missing or partial source cannot be silently upgraded to grounded |
| LAT08 | cancellation/disconnect and in-flight provider bounded behavior characterized honestly |
| SEC01 | delegated-token cache semantics pass all negative tests and legitimate Core/Domain authorization gates |
| REG01 | full relevant suites PASS, stage/owner wiring tests and no regressions on final SHA; source refs collision safe |
| G04/G05/G07/G12 | all meet document 221 R1's real E2E acceptance, no false server-side success |

If LAT03 or LAT04 fails by 504, do not mark functional acceptance. If SEC01 is unproven, do not authorize production. The returned result must be `FUNCTIONAL_ACCEPTANCE_CANDIDATE` only with actual evidence, else `REWORK/BLOCKED_WITH_EVIDENCE/INCONCLUSIVE`.

## 5. Executor handoff / bounded prompt

**TASK_ID:** `DELIA-C3-E4-R2-LATENCY-DELEGATION-AND-DELIVERY-CLOSURE-01`

Reanchor main/status, authorities and docs 221–224, ledger. Verify and correct delegated credential cache security (SEC-01) before acceptance; no token/role bypass. Reconstruct actual E4 per-stage timeline and remove redundant work using existing semantic planner/subobjective state, preserving owner boundaries. Optimize legitimate independent READ branches using existing LangGraph mechanisms only if safe and demonstrably useful; otherwise keep simpler verified path. Align effective turn and gateway/stream delivery contract without blindly raising timeouts. Complete actual Qwen3 local authenticated DAVI/Domain E2E both same-session and single-turn; verify full deterministic oracle and actual client-visible response; test denial, revocation, expired JWT, cache isolation, cancellation, negative evidence and model variability. RED→GREEN, full regression, cleanup and safe commit/push main, report SHA/config, latency/tokens, output and precise gate statuses. Continue authorized fixes to functional delivery; do not stop at internal-composition success. If frozen owner/security/timeout policy requires explicit decision, stop affected step with evidence and finish safe independent work. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.
