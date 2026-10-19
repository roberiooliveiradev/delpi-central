# 54 — Provider-neutral semantic provenance and continuity rework

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-PROVIDER-NEUTRAL-SEMANTIC-PROVENANCE-AND-CONTINUITY-REWORK-01`  
**REFERENCE_HEAD:** `db2645108bdf4713c01fd67a7cab53da6e63ec8c`  
**STATUS:** `IMPLEMENTATION_CANDIDATE`

## Reuse gate

| Responsibility | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Orchestrator / TurnDeadline / InvokeModel | YES | REUSE |
| Argument proposal + schema validation | YES | REUSE |
| Free-string budget-skip gate | YES (`_free_string_grounded_in_user_input`) | **EXTEND** (coverage, not intersection) |
| Prior continuation / goal typed fields | YES | **EXTEND** (compare/analyze probe + budget stop) |
| New planner / provider branches / intent regex | — | **FORBIDDEN** |

## Root causes (proven)

1. **PROVENANCE_VALIDATION_FAILURE:** `_free_string_grounded_in_user_input` accepted any shared ≥3-char token or `haystack in proposed`, so `description="terminal pino industrial especial aprovado"` for user «Mostre terminais pino» passed.
2. **CONTEXT_CONTINUITY_FAILURE / BUDGET_EXHAUSTION:** compare follow-ups with `prior_evidence_sufficient=false` often skipped the prior-transform probe (cue regex too narrow), then fallthrough to full owner path exhausted the 30s budget (L5 504).

## Fix

1. Provenance: every material token of the proposal must be covered by the user message (exact or shared stem); exact folded substring of user text still OK; containing the short user text inside a longer invented proposal is **not** OK. Paraphrases like `TERM. PINO` ↔ «terminais pino» remain allowed.
2. Continuity: typed `comparison_requested` / `goal_class in {compare,analyze}` authorizes prior-transform probe without new intent regex; GOAL instructions clarify anaphora/subset/compare; probe-insufficient stops when resolver headroom is gone instead of burning the turn on owner reselection.
3. No DAVI/TÉO/VISTA/product hardcode; no planner; no timeout increase.

## Tests

`test_provider_neutral_semantic_provenance_and_continuity.py` — PROV-T01/T02/T03/T04/T06/T09/T10 + CONT-T01/T03/T08/T12.  
Full `delia-api` pytest PASS. Existing PROD/i02r2/i01/SEMARG green.

## Live

Filled after deploy in ledger §6.296.

## Gates

```text
I04_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
