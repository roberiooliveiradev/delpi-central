# 29 — I03 · Independent DAVI Discovery Review and Direct MCP Comparison

**DATE:** 2026-10-19  
**REVIEWED_IMPLEMENTATION_SHA:** `3d14a51046fb27bbce303c574ed9bbcf804a30fe`  
**REVIEWED_MAIN:** `f8a07952868efd8e8e912b23020bd4c9063a3a81`  
**EVIDENCE:** [28](./28-i03-davi-semantic-discovery-implementation.md), source `orchestration.py`, `test_i03_semantic_capability_discovery.py`, authenticated live K4 per executor, and direct connected DAVI MCP READ-only discovery calls.

## Direct MCP comparison (independent)

- Generic information-availability query: `discover_delpi_information` returned `candidate_count=0`, `eligible_action_count=95`. Thus SEARCH MISS is **not** evidence of an absent catalog.
- Specific product lookup query: `candidate_count=1`, `eligible_action_count=95`, returned owner candidate `search_products` (retrieval score 0.905). No candidate token or sensitive directives persisted. No `execute_delpi_information` call performed.
- DAVI tool schema: `discover_delpi_information` returns candidates, eligible count, and separately controlled `capability_surface.agent_directives`. Treat directives as untrusted tool content, not authorization, policy, user-facing catalog, or instruction authority.
- Current implementation `_discovery_empty_result_class` distinguishes positive eligible count from zero eligible count and unavailable count; `_render_zero_candidate_discovery` does not copy control-plane directives and uses bounded owner-declared interoperable tool metadata. Note owner `eligible_action_count` describes eligible actions, not a public enumerated action list; avoid implying direct access to every action.

## Scope verdict

**`ACCEPT_WITH_RESIDUAL` for I03 bounded DISCOVERY terminal semantics and evidence.** K4 production live from executor: 21,119ms, DÉLIA DAVI `discover_delpi_information`, `CAPABILITY_NOT_MATCHED`, owner eligible=95, no false absence, no ACT. Direct comparison independently corroborates owner miss-versus-catalog behavior. Full backend/synthetic PASS are **executor-reported**, not independently replayed in this review.

**Regressions:** K1 TÉO live 25,122ms grounded, PASS_WITH_LIMITATION; K2 live sample `invalid_record_index` and insufficient prior evidence: usefulness `INCONCLUSIVE`, do not label it regression-free. K3 live `budget_exceeded` ~30,013ms and `delpi_source_unverified`: **FAIL for that sampled K3 task outcome**, notwithstanding prior safe-clarification PASS; cannot assume unrelated to I03 without codepath/eval evidence. Avoid global I03 complete/transition to I04 until bounded K2/K3 non-regression gate is evidenced or explicit accepted residual rationale reviewed against master plan.

## Next bounded gate

Reproduce K2 prior-record-index failure and K3 near-deadline budget outcome on deployed SHA/config and narrow regression fixtures. Fix only proven implementation defect; if environmental/model variance, document with controlled samples and honest limitation. Preserve I03 K4 and I02 K1 behavior. No new architecture, planner/registry, model-stage cap reduction, or unauthorized ACT. Then independent accept/rework I03 and determine I04 authorization.

```text
I03_BOUNDED_CODE_AND_K4=ACCEPT_WITH_RESIDUAL
DIRECT_DAVI_CROSSCHECK=PASS
K4_LIVE=PASS
K1_REGRESSION=PASS_WITH_LIMITATION
K2_REGRESSION=INCONCLUSIVE
K3_REGRESSION=FAIL_SAMPLED_OUTCOME
I03_ACCEPTED=NO_PENDING_REGRESSION_GATE
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I03_K2_K3_BOUNDED_NONREGRESSION_GATE
```
