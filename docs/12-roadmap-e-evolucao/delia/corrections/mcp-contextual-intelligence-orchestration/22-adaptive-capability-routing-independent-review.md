# 22 — Adaptive Capability Routing · Independent Implementation Review

**DATE:** 2026-10-19  
**REVIEWED_IMPLEMENTATION_SHA:** `c2ae80e364b361761bd48c0a4bfce3be11975023`  
**REVIEWED_MAIN:** `4dda68530f3a610486885a19d0c82c44bfbf2180`  
**SOURCES:** [21](./21-adaptive-capability-routing-completion-implementation.md), relevant `orchestration.py` methods, `test_adaptive_capability_routing_completion.py`, prior [20](./20-i02r3b-independent-live-outcome-review.md), ledger §6.262.  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` (bounded implementation and reported live outcomes only); **ALGORITHM_COMPLETION=PARTIAL**, **I02_ACCEPTED=NO**.

## Observations

- `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND`: implementation extends `OperationalCapabilityOrchestrator` and existing `select_decision_path`; no new engine/registry found in reviewed diff.
- **FAST:** uses existing decision-path selection for telemetry. Automatic singleton selection was reverted because singleton availability does **not** prove applicability; correct fail-closed decision. Not a complete deterministic autonomous routing path.
- **OPERATIONAL:** R3-B capability+goal cold-start typed merge preserved. `_deterministic_arguments_from_schema` handles closed owner-schema values; opaque TÉO methodology remains model-bound.
- **REASONING/native:** multi-group assessment can omit one model call only for explicit comparison with a non-write target, while maintaining corroboration routing; ordinary READ and write targets still assess. Verify foreign-required and comparison interaction in further holdouts if behavior changes.
- **K2 quality:** extraction helper and thin-text expansion added; logged live answer length improved 48→130 chars, but current sample did not exercise expansion (already >=120). Therefore do **not** attribute the live increase causally to the new expansion gate; usefulness remains partial.
- **K3:** lexical ranking and selected identifier logging added; logged `display_formats` for the legibility/visualization ask, still `TOPIC_RELEVANCE=PARTIAL`. Lexical overlap alone does not establish semantic match.
- **Live as reported:** K1 TÉO 20,199ms, typed merge, owner `get_methodology_guide` READ reached, grounded/truncated; K2 21,066ms, owner reuse, 130 chars, non-grounded continuity; K3 VISTA 15,294ms, INDEX→topic→guide, grounded but partially relevant. n=1/case, differing run conditions; no causal speedup or p95 claimed.
- **Tests:** completion suite, I01/I02/R2/R3A/R3B and full backend PASS reported by executor; not independently rerun in this remote GitHub review (`TEST_NOT_RUN`). No unauthorized ACT reported.

## Decision and bounded next step

Accept the bounded implementation with residuals. Do not accept global I02 or claim full adaptive FAST routing. Preserve K1 operational success; prioritize specific quality criteria: (1) K2 substantive answer/evidence sufficiency without invented content or owner reinvocation; (2) K3 semantically relevant owner-declared topic or honest clarification when unmatched. Any prospective FAST selector requires deterministic proof of applicability beyond singleton surface and full security/generalization regression. Avoid redesign by convenience, blanket READ skips, 10s stage cap or headroom default changes.

```text
INDEPENDENT_REVIEW=ACCEPT_WITH_RESIDUAL
FAST_PATH=TELEMETRY_ONLY
OPERATIONAL_PATH=IMPLEMENTED_BOUNDED
REASONING_PATH=PRESERVED
DETERMINISTIC_ARGUMENTS=ELIGIBLE_SCHEMA_ONLY
K1_LIVE=PASS_WITH_LIMITATION
K2_USEFULNESS=PARTIAL
K3_RELEVANCE=PARTIAL
LIVE_CAUSAL_IMPROVEMENT=INCONCLUSIVE
INDEPENDENT_TEST_REPLAY=TEST_NOT_RUN
ALGORITHM_COMPLETION=PARTIAL
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I02_K2_K3_BOUNDED_OUTPUT_QUALITY_REMEDIATION
```
