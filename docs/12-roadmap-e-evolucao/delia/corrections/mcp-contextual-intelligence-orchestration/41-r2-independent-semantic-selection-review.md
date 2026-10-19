# 41 — Independent R2 semantic capability-selection review

**DATE:** 2026-10-19. **MAIN/CODE REVIEW:** `d63c0ae98df3bf730e14af552a948f823367c93f`; **LIVE SOURCE/DEPLOYED:** `19843e5cf9f5684f52124f0df25ae8d131b6bb35`. **INPUT:** [40](./40-r2-provider-neutral-capability-selection-quality.md), code commit `19843e5c` diff, ledger §6.281. **VERDICT:** `ACCEPT_WITH_RESIDUAL` for bounded **broad information-coverage inquiry R2**; **I04 GLOBAL=REWORK**. Independent live replay `TEST_NOT_RUN`.

## Code review

- R2 adds selection instruction v12, `role=owner_vocabulary_discovery` only for `DISCOVERY` class, and a PT/EN coverage-intent detector. When **selected group** has a **unique** discovery capability and stage-2 selection returns none for a recognized coverage inquiry, `_select_target` uses that actual contract-backed discovery, not an arbitrary group/tool. No DAVI name in reviewed patch, no new planner/registry/public DTO.
- `_is_information_coverage_inquiry` is finite regex-based intent evidence, not a general semantic understanding guarantee. Language variants, near-miss, contradictory wording, multi-discovery groups, and intent context are not comprehensively proven live. Guard with metamorphic/holdout evals and avoid expanding regex as unconstrained parallel taxonomy.
- `applicable=false` from model is overridden only in constrained owner-discovery case. This is acceptable for scoped coverage inquiry where owner advertises semantic enumeration, but confirmation of safe effect across irrelevant queries and delegated scopes remains a required regression.

## Outcomes and acceptance distinctions

| Case | Executor-reported live | Review |
|---|---|---|
| K4-A broad DAVI | `discover_delpi_information` reached; eligible=95, candidate=0; grounded 16118ms | `PASS` for **honest coverage discovery**; eligible count does NOT mean all are authorized facts/executable |
| K4-B thematic products | `search_products` selected, ask-back for missing fields, 26163ms | `PARTIAL`; no completed product task and no universal recovery |
| K4-C no-match | source-unverified outcome at 30019ms | `FAIL` strict 30s budget; safe no-invention alone does not change timing result |
| L02/L03/L04/L05 | R1 clarification 3560ms; TÉO grounded 16734ms; K2 framing 15420ms; VISTA clarification 21969ms | regression controls `PASS_EXECUTOR_REPORTED` |
| L01 GLPI | linked prerequisite still enforced | `PASS_PRECONDITION`, user-scoped ticket count `INCONCLUSIVE` |

Full backend and T01–T17 reported PASS; independent rerun not executed. SHA live matches R2 **code** commit, while docs final main advanced separately; do not conflate document commit with deployed binary.

## Decision and next bounded correction

Accept the bounded broad-discovery path with explicit residuals; **do not** claim general semantic selection solved or I04 accepted. Next remediation priority: (1) strict 30s budget at response boundary including 30019ms edge, (2) K4-B semantic/argument interpretation against exact `search_products` contract, (3) provider-neutral generalization beyond regex phrasing and discovery singleton, with preregistered live+synthetic holdouts. Preserve R1/R3, safety, Core/Domain owner and 0 ACT. R2 contract changes require Architecture Decision rather than silent implementation.

```text
R2_BROAD_COVERAGE_REVIEW=ACCEPT_WITH_RESIDUAL
K4_A=PASS_EXECUTOR_REPORTED
K4_B=PARTIAL
K4_C_STRICT_BUDGET=FAIL
GENERALIZATION_BROAD=INCONCLUSIVE
FULL_BACKEND=PASS_EXECUTOR_REPORTED
INDEPENDENT_LIVE_REPLAY=TEST_NOT_RUN
I03_ACCEPTED=YES_WITH_RESIDUAL
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I04_BOUNDED_BUDGET_AND_THEMATIC_GENERALIZATION_REWORK
```
