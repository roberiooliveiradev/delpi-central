# 14 — I02-R3 Independent Diagnostic Review and Architecture Decision

**DATE:** 2026-10-19. **REVIEWED_HEAD:** `56d3c0b51bcb316d225d480271a773cde20f247b`. **VERDICT:** `ACCEPT_WITH_RESIDUAL` **for causal diagnosis only**. **I02_ACCEPTED:** `NO`.

## 1. Reviewed sources and limits
Independent GitHub review of [13 — consultant evidence](./13-i02r3-consultant-evidence-and-dependency-analysis.md), `orchestration.py` `_build_arguments`, `_propose`, `_budget_allows_optional_index_probe`, and prior docs 07–11 and ledger §6.251. Backend suites and authenticated live run were executed **by consultant, not independently rerun**. Runtime config fingerprint is a previously recorded R2 value, not recomputed at evaluated HEAD. Current `main` later commits must be reanchored before implementation; review is bounded to cited SHA. Local `git status`, .cursor, and complete canonical document order are implementation-gate obligations.

## 2. Accepted causal diagnosis
- Live K1 correlation `561bb788-5271-4ea8-8c35-80fa4d85d4bd`: model proposals select_group 2,284ms, select_capability 14,778ms, turn_goal 7,021ms, native_assessment 2,398ms, TÉO get_catalog 151ms, arguments 3,015ms and `error_code=timeout`, total ~30,016ms. Methodology owner READ = 0. `K1_TIMEOUT_EXACT_STAGE=PROVEN:delia.capability_orchestration.arguments`. Previous R2 failure consistent; old success logs stale.
- The cheap DISCOVERY outcome cannot help when sequential model stages consume the shared 30s prior to arguments. Characterization tests prove current behavior and safety invariants, **not** efficacy of any remediation.
- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND_CANDIDATE`. No new planner, memory, cache, registry, public schema, or runtime service.

## 3. Architecture decision: staged, evidence-gated remediation
### R3-A — Budget safety/experiment (bounded)
- Reuse the existing `TurnDeadline`, `_propose` reduction-only stage timeout and budget-skip design. Compare **controlled stage caps** (e.g., configured 30s vs code default 10s as experiment, **not** approved blanket production value), while preserving `GLOBAL_TURN_BUDGET_SECONDS=30`. Shorter cap may turn a 30s failure into an earlier **failure**; it must not be labeled functional success.
- Add/adapt *pre-arguments headroom* ONLY if tests prove that the remaining budget cannot support model proposal, authoritative READ and deterministic response. Do not invoke unauthorized empty schema, make up owner vocabulary, silently reuse stale values, or misclassify an incomplete answer as grounded guidance. On insufficiency return truthful, typed limitation with no owner READ.
- Require RED/GREEN characterization for remaining ~3s, sufficient-budget success path, missing required inputs, DISCOVERY failure, write/foreign, K1→K2, VISTA index R2, 30s timeout. Compare model invocation counts, duration and **task outcome** against baseline at same SHA/config. If shorter caps increase failure rate or degrade selection, reject/rollback.
- No production deploy of a stage-cap policy until contract/safety gates, regression and bounded live comparison authorize it.

### R3-B — Critical-path model-call elimination (separate architecture gate)
- Current K1 executes group → capability → goal → native → arguments. Review whether goal/capability proposals can share one **typed result** or whether native assessment can safely short-circuit for a narrow class of native READ, **without** weakening `goal` write semantic finality, foreign evidence requirement, corroboration, owner discovery, and provider-neutral generalization.
- Each proposed omission/consolidation needs explicit input/output dependency map, alternate/fallback rule, owner and consumers, deterministic validations, RED tests, synthetic renamed provider + foreign-required + explicit comparison + ambiguous WRITE + prompt-injection holdouts. No generic heuristic 'READ ⇒ no foreign evidence'; not approved yet.
- Continue to measure token counts only if existing telemetry supports them, with no prompt/payload/secret logging.

**Rejected now:** globally forcing stage timeout 10s as a proven fix; treating a headroom skip as evidence of user-goal completion; parallelizing dependent proposals by convenience; skipping domain safety gates; creating another planner.

## 4. Outcome acceptance gates
K1 must reach TÉO `get_methodology_guide` with useful grounded answer; K2 must reuse that legitimate K1 evidence if sufficient; K3 maintains prior index→topic→nested guidance path; no material ACT, no fictional facts, under global 30s; SHA/provider/config and independent review recorded. If not proven, `FAIL|INCONCLUSIVE|TEST_NOT_RUN`, not PASS. Monitor false-positive Portuguese index metadata heuristic and 30s optional-probe floor residual from R2.

```text
I02_R3_INDEPENDENT_DIAGNOSTIC_REVIEW=ACCEPT_WITH_RESIDUAL
K1_TIMEOUT_STAGE=PROVEN_ARGUMENTS
PRE_OWNER_SEQUENTIAL_MODEL_COST=PROVEN
SAFE_FUNCTIONAL_OPTIMIZATION=NOT_YET_PROVEN
ARCHITECTURE_DIRECTION=R3A_BUDGET_EXPERIMENT_THEN_R3B_CRITICAL_PATH_DECISION
STAGE_CAP_10S_PRODUCTION_APPROVAL=NO
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND_CANDIDATE
SOURCE_CODE_CHANGED=NO
TESTS_INDEPENDENTLY_EXECUTED=TEST_NOT_RUN
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=I02_R3A_BOUNDED_BUDGET_EXPERIMENT_AND_CRITICAL_PATH_EVIDENCE
```
