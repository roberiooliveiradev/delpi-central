# 62 — G0 bounded I04 remediation (compare outcome + C02 budget)

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I04-G0-SINGLE-BOUNDED-REMEDIATION-01`  
**BASE_REFERENCE:** `fc93fbf3591a8115bd238a4c05af6c5b8a1c7361`  
**AUTHORITY:** Option A §6.304 / doc 61 §8 — `G0_REMEDIATION_AUTHORIZED=YES`; `Q01_AUTHORIZED=NO`  
**STATUS:** `IMPLEMENTATION_CANDIDATE`

## Reuse gate

| Responsibility | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Prior continuation / synthesis | YES | **EXTEND** (compare ≠ list replay) |
| Interaction admission instruction | YES | **EXTEND** (formats/guidance catalogs → owner) |
| Conversational fallback after NOT_APPLICABLE | YES | **EXTEND** (stage cap + soft-land on timeout) |
| New planner / provider branches / free factual prose | — | **FORBIDDEN** |

## G0-01 — Compare vs list

**ROOT_CAUSE (PROVEN):** `recover_empty_selection` projected prior bullets as a list SUCCESS for compare/analyze asks (F33). Live L5 returned «Recuperei 2 itens…» counted as continuity latency PASS but **FAIL_TASK_OUTCOME** for comparison.

**FIX:** When `comparison_requested` / compare|analyze, never recover empty synthesis as a list. Prefer deterministic segment diffs from prior bullet units (`a — b — c`), else explicit insufficiency (`LIMITATION_INSUFFICIENT_EVIDENCE`). List replay after a successful synthesis is replaced the same way.

**TESTS:** `test_g0_01_compare_empty_selection_is_not_list_success`, opaque-prose insufficiency, segment helpers; CONT-T03 updated.

## G0-02 — VISTA C02 HTTP 504

**ROOT_CAUSE (PROVEN from prod logs, corr `089e31c8` / request `aa47991a`):**
1. `interaction_admission` classified «Quais formatos de dados estão disponíveis?» as **conversational** (~4.9s).
2. Orchestrator returned `NOT_APPLICABLE`.
3. Handler free-form fallback invoked the general model until **`model_timeout`** → HTTP **504** (~30s).

Not a VISTA owner hang: owner was never selected. Sibling earlier turn wrongly selected TEO methodology for a formatos-like ask (selection residual; not patched with specialist branches).

**FIX (provider-neutral):**
1. Admission instruction: owner-published formats/topics/guides/panels catalogs require `requires_owner_surface=true` / `operational`.
2. After governed `NOT_APPLICABLE`, cap conversational fallback stage at 12s and soft-land timeout into bounded NON_GROUNDED content (`turn_budget_limited`) instead of raising `MODEL_TIMEOUT`→504.

**TESTS:** soft-land timeout; admission instruction lock; fallback timeout ≤12s.

## Live

Password-grant for subject `user` returned `invalid_grant` at execution time; cached JWTs expired. **LIVE_POST_FIX=`TEST_NOT_RUN`** (auth blocker). Historical C02 stage chain remains the proven baseline for the patch.

## Gates

```text
I04_ACCEPTED=NO
G0_REMEDIATION_EXECUTED=YES
Q01_AUTHORIZED=NO
Q02_AUTHORIZED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_G0_REVIEW
```
