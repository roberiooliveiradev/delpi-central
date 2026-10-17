# 06 — I02 Independent Review · Rework Decision

**DATA:** 2026-10-17. **TASK:** `DELIA-C3-MCP-CONTEXTUAL-KNOWLEDGE-SYNTHESIS-I02-IMPLEMENTATION-01`. **VERDICT:** `REWORK` (functional acceptance pending). **REVIEWED_HEAD:** `40663f65dbcdb0b831f0845db8096913a1f85e1e`.

## Independent review scope
GitHub diffs for `55b0e9397100dadea10c0180e922afbc4afcaf1d` and post-live fix `cc7d2c8e3ba0d70edd56088df72ee795976c2e2e`, [executor report 05](./05-i02-grounded-knowledge-synthesis-implementation.md), roadmap and ledger §6.243. Independently inspected code changes and documentation. **Did not rerun** backend pytest, server runtime or authenticated model evaluation; their evidence remains executor-reported.

## Findings
1. **Direction approved for continued work, not accepted outcome:** existing `_synthesize_content`, `_synthesis_records`, `render_specialist_outcome` and deterministic projection extended; owner-guidance sections selected by intent; bounded result and no model-authored factual prose. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`. No new planner, catalog, memory or public context contract.
2. **K1 FAIL:** selected TÉO methodology but pre-synthesis goal/selection/discovery time consumed 30,025ms, `model_timeout/delpi_source_unverified`, no useful owner outcome. A presentation-only fix cannot address this exhausted upstream budget.
3. **K2 partial:** 20,373ms deterministic guidance with methods/when-to-use but re-invoked owner because K1 had failed. Not evidence that K1→K2 user outcome is fully solved on evaluated configuration.
4. **K3 partial and SHA mismatch:** live run of `55b0e939...` skipped synthesis at 3,097ms remaining, failed to project nested guidance and presented truncated dump. Subsequent `cc7d2c8...` added nested guide envelope handling, aliases, fallback on skip_budget and deterministic tests, **but post-fix live K3 = TEST_NOT_RUN**.
5. **Bounded risks:** generic PT/EN cue vocabulary and section aliases are heuristic; verify under renamed provider, unknown field shapes, nested payload, meta-first input, large arrays and untrusted text. Ensure guidance fallback never invents leaves, promotes owner metadata to instructions, silently drops limitations or confuses partial projection with complete knowledge.
6. **Evidence trust:** tests I02 S1–S5, I01, security and full suite PASS are executor-reported, not independently reexecuted. No unauthorized material ACT reported.

## Required next bounded work (I02-R1, not I03)
**A. Baseline post-fix live:** evaluate exactly the approved `cc7d2c8...` runtime/config (or later SHA explicitly bound to the change) using an authorized, bounded VISTA guidance case; distinguish projection fix from topic selection mismatch. If live cannot be executed, `TEST_NOT_RUN`—not PASS.

**B. Pre-synthesis latency causal profile:** capture per-stage durations and deadline budget for failed K1, especially goal, live surface, target, discovery/catalog, arguments and owner READ; assess shortest valid path, avoid repeat consultations/model calls without widening the 30s deadline. Propose small correction **after** proving bottleneck; no opportunistic global timeout increase.

**C. Regression/acceptance:** K1 useful owner-guided answer, K2 from same successful K1 with relevant previous-knowledge reuse, K3 VISTA appropriate guidance; test unsupported/renamed/unknown shapes and malicious payload, preserve `GUIDANCE!=DOMAIN_FACT`, `MESSAGE!=ACT`, 0 material ACT, no new planner or memory. Record exactly evaluated SHA/model/config and task outcomes, with independent review.

**D. Scope:** no I03, Q refactor, new owner catalogs, global MCP knowledge copy, new persistence or API contracts. Any incompatible new contract: STOP → `ARCHITECTURE_DECISION_REQUIRED`.

## Decision
```text
I02_INDEPENDENT_REVIEW=REWORK
I02_ACCEPTED=NO
STRUCTURAL_DIRECTION=ACCEPT_FOR_BOUNDED_EXTENSION
LIVE_K1=FAIL
LIVE_K2=PASS_WITH_LIMITATION_NOT_SAME_SUCCESSFUL_K1_CONTINUITY
LIVE_K3=PASS_WITH_LIMITATION_PRE_NESTED_FIX
NESTED_FIX_POST_LIVE=TEST_NOT_RUN
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
GLOBAL_TURN_BUDGET_SECONDS=30
MATERIAL_ACT_COUNT=0_REPORTED
I03_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
PRODUCTION_READINESS=NOT_PROVEN
NEXT=I02_R1_POST_FIX_VALIDATION_AND_PRE_SYNTHESIS_LATENCY_CAUSE
```
