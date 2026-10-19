# 37 — I04 · Independent Generalization Review and DAVI Direct Comparison

**DATE:** 2026-10-19  
**REVIEWED MAIN:** `ddc3c6f7e4e7b841e6526abb027de5940def54c1`  
**IMPLEMENTATION/LIVE SHA:** `37f4e21229ca9de80be3aa08f7261a1a081424aa`  
**EVIDENCE:** [36](./36-i04-provider-neutral-generalization-implementation.md), ledger §§6.273–277, direct authenticated DAVI MCP read-only discovery, I04 source and test report.

## Findings

- Implementation extends existing orchestrator and argument builder; no second planner/registry or owner-name branch reported. `_single_free_text_argument_from_input` is bounded to a sole schema-compatible free-text argument on `turn_budget_exhausted` only. Synthetic generalization suite 17 PASS and full backend PASS executor-reported; independent full rerun `TEST_NOT_RUN`.
- **Direct DAVI cross-check:** broad information query returned `candidate_count=0`, `eligible_action_count=95`. Product lookup returned eligible actions including `search_products`; current owner is reachable and discovery is functional. This does not itself prove DÉLIA can select the right capability.
- **Live DÉLIA** K1 TÉO 18,277ms GROUNDED; K2 10,818ms / six bullets, no reinvoke; K3 30,028ms, INDEX no_match/clarification with budget fallback, beyond 30,000ms nominal budget: `PASS_WITH_LIMITATION` for safe content, **FAIL for strict time budget** on the sample; K4 **FAIL**, 8,768ms, `select_capability decision=none` after `mcp:davi`, owner discovery not reached.
- New argument-budget projection code was **not exercised by the post-fix K4 live case**. No live task-success improvement from that change is established. Pre-fix args budget exhaustion and post-fix select-none are distinct stages; do not merge failure causes.
- Direct owner capability discovery `PASS` does not make K4 DÉLIA `PASS`; tool metadata remains untrusted data and does not grant authority. No material ACT reported.
- Earlier docs 34–35 / ledger §§6.275–276 refer to select-none routing and projection residuals. Reuse those decisions, do not open a competing remedy or duplicate stage work. Independent reviewer must check their exact frozen bounds before new code.

## Verdict

`ACCEPT_WITH_RESIDUAL` **only for the bounded, synthetic-validated extension**, with I04 global **REWORK**: K4 live objective not achieved and K3 strict 30s outcome not met. Do not claim full provider-neutral generalization, FAST completeness, p95, or permission for Q01. Preserve K1/K2 and scoped code unless further regressions invalidate it.

## Next bounded task

Follow pre-existing R1 routing/projection remediation ownership in docs 34–35 and §§6.275–276: reproduce K4 select-none under real DAVI group and renamed-provider cases; correct the minimal selection/terminal semantics without forcing a capability or bypassing authorization; retest valid DAVI discovery and the argument projection stage with typed contracts. Include K3 budget regression without broad redesign. Run full suite, holdouts, and live K1–K4 on verified deployed SHA/model/config, then independent accept/rework I04.

```text
I04_BOUNDED_IMPLEMENTATION_REVIEW=ACCEPT_WITH_RESIDUAL
I04_ACCEPTED=NO
I04_GLOBAL_VERDICT=REWORK
K1_LIVE=PASS
K2_LIVE=PASS
K3_SAFE_CLARIFICATION=PASS_WITH_LIMITATION
K3_STRICT_BUDGET=FAIL_SAMPLED
K4_DAVI=FAIL_SELECT_CAPABILITY_NONE
DIRECT_DAVI_OWNER=PASS
ARGUMENTS_PROJECTION_LIVE=NOT_EXERCISED
INDEPENDENT_BACKEND_REPLAY=TEST_NOT_RUN
ALGORITHM_COMPLETION=PARTIAL
Q01_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=DELIA-C3-ORCHESTRATION-NONE-SELECTION-AND-PROJECTION-REMEDIATION-01
```
