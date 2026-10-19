# 27 — I03 · DAVI Semantic Discovery Implementation Brief

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I03-DAVI-SEMANTIC-DISCOVERY-IMPLEMENTATION-01`  
**STATUS:** `PLANNED_EXECUTION`, not code implementation.  
**ROADMAP:** I03 after I02 scoped ACCEPT_WITH_RESIDUAL ([26](./26-i02-owner-crosscheck-and-acceptance-gate.md)); higher authority/ledger conflict => STOP, not silent phase advance.

## Objective

Correct **discovery of authorized, relevant capabilities** for the DAVI/Domain API path when users ask what information can be consulted. Distinguish an empty semantic search result from confirmed lack of catalog coverage; give a useful, honest discovery answer and, when legitimately appropriate, the next read option, without executing READ/WRITE just to prove discovery.

## Execution contract

1. Reanchor HEAD/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, architecture, product spec, I03 thematic contract, ledger; map actual CP/RQ. Review I00–I02 acceptances, original K4 from report 44, and the DAVI tools' current authentic schemas via direct READ-only connected MCP testing. Do not hardcode DAVI names or owner catalog locally.
2. Trace real responsibility→owner→authoritative catalog/Domain APIs→consumer→contract→implementation→tests→outcome. Prove `EXISTING_EQUIVALENT` and `REUSE_DECISION` before any abstraction (likely extend current orchestrator; not assumed blindly). Search misses are not evidence of absence; `OWNER_CONTRACT_GAP` is legitimate when owner provides no enumerability.
3. RED tests: ambiguous 'what data can I get' / thematic capability discovery, zero semantic matches but discoverable catalog, honest no-match with no list, provider renamed and non-MCP, scope/RBAC denied, tool metadata injection, fabricated capability, compare/multi-owner, explicit WRITE and missing required input, limits/deadline 30 and ACT=0.
4. Implement minimal provider-neutral fix within legitimate boundary, no shadow registry/planner/provider branches. Prefer owner-authoritative discoverability/description; never claim capabilities not backed by live owned catalog. No search-only 0-results→absence conclusion.
5. GREEN targeted/full backend + K1 TÉO, K2 continuity, K3 VISTA no-match regressions. Authorized authenticated live K4 DAVI with SHA/model/config/correlation/provenance, plus 1 renamed-provider test; do not rely on synthetic alone. Compare read-only direct DAVI MCP behavior when useful. Preserve K1/K2/K3 and 30s safety, Core AuthZ/Domain authority, no material ACT.
6. Record outcome, changed files, tests, truthful limits/owner gaps in doc28 (if available), README and ledger; commit/push main preserving concurrent changes; return complete execution report for coordination independent review. No automatic I04/Q01/C3 progression.

## Success criteria

`K4_DISCOVERY`: recognizes or truthfully qualifies authorized possibilities backed by owner contract; differentiates no semantic match vs not enumerable; avoids false promise; connects to action only through proper separate gates. `K1_K2_K3_REGRESSION=PASS_WITH_LIMITATIONS_PRESERVED`. All code tests PASS, real live K4 task outcome when accessible, zero unauthorized ACT. Owner contract impossibility ⇒ `OWNER_CONTRACT_GAP` and scoped inconclusive, not fabricated implementation.

```text
NEXT=EXECUTE_DELIA_C3_I03_DAVI_SEMANTIC_DISCOVERY_IMPLEMENTATION_01
I03_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
```
