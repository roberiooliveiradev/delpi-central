# 34 — Independent review · live routing failures and bounded remediation gate

**DATE:** 2026-10-19  
**REVIEWED EVAL SHA:** `9a8775018f31111ce59b11945efec962e0db73d4`  
**SOURCE:** [33](./33-live-orchestration-decision-and-log-validation.md), current `orchestration.py` `_select_target`, Execution Ledger §6.274.  
**VERDICT:** `ACCEPT_WITH_RESIDUAL` for **diagnostic evidence**, `REWORK` for sampled L02/L06 runtime outcomes. No functional patch accepted or deployed by this review.

## Evidence assessment

| Case | Observed result | Classification |
|---|---|---|
| L01 personal tickets | correct TÉO helpdesk selection; owner `glpi_link_required`, no ticket list/count | `FAIL_TASK / PASS_ROUTING`; personal total still `INCONCLUSIVE` |
| L02 terminal bandeira | `select_group=none`, no owner invocation, 504 at 30,014ms | `FAIL`; exact typed model proposal payload unknown |
| L03 methodology | TÉO grounded READ, 22,313ms | `PASS_WITH_LIMITATION` |
| L04 followup | `recover_invalid_index`, prior evidence used, no reinvocation; wording 'Encontrei 7 registros' | `PASS_WITH_LIMITATION`; `RESPONSE_PROJECTION_FAILURE` |
| L05 VISTA | INDEX 11, weak topic rejected, safe clarification 23,308ms | `PASS_SAFE_CLARIFICATION` |
| L06 DAVI | correct group, `select_capability=none`, no READ, 504 at 30,011ms | `FAIL`; direct DAVI catalog healthy `eligible=95` |

These are n=1/case on the evaluated runtime; stage timings and selected path are executor-collected. Full backend suite and independent live replay were **not** run in this review. Runtime SHA differs from current docs/main: never equate them without deployment proof. This does not reverse accepted scoped I03 on doc32/ledger §6.273; it highlights distinct sampled regressions. `I03_ACCEPTED=YES_WITH_RESIDUAL`, `C3_EXECUTED=NO` remain.

## Code-level confirmation and bounded decision

Current `_select_target` in `OperationalCapabilityOrchestrator` explicitly returns `None` when group selection or capability selection is invalid/unmatched. The diagnostic establishes that downstream live L02/L06 continued until budget exhaustion, but the precise fallback/caller chain and model payload must be verified **before editing**. Protect existing fail-closed behavior for READ/PREPARE/ACT, Core/Domain authorization and owner discovery; `none` must not be treated as permission or a plausible capability.

**Priority remediation group (existing app orchestration and presentation only, no new engine):**

1. **R1 L02/L06**: characterization RED for valid surface + model no-selection under remaining budget; inspect caller/fallback and choose existing truthful clarification or inability outcome immediately when safe, rather than making doomed model calls to 504. Distinguish no-match, unavailable surface, model timeout, and explicit ambiguous WRITE. Verify holdouts where fallback can legitimately select a different safe path, so no premature clarification.
2. **R2 DAVI**: inspect existing typed proposal/owner discovery I03 contracts and live eligible surfaces to determine why the model proposed no capability. Fix only confirmed provider-neutral selection defect; no DAVI-only branch, shadow catalog, fake capability or unauthorized direct invocation. Material contract changes return `ARCHITECTURE_DECISION_REQUIRED`.
3. **R3 L04**: fix projection wording so prior methodology/checklist excerpts are not mislabeled as record lists; preserve provenance and no model factual prose.
4. **R4/R5 Helpdesk**: owner GLPI link prerequisite is real for the evaluated identity; maintain actionable precondition UX without secrets or fabricated count. Personal assigned/requester semantics and paginated totals remain a **separate bounded follow-up** after authorized linked session; don't force this fix while data inaccessible.

**Acceptance required:** live real model on deployed SHA/config and comparison with owner contract for L02/L06, no 504 caused solely by known no-selection when truthful outcome possible; L04 semantic framing; K1/K2/K3/K4 regressions + full backend + provider-neutral, injection, WRITE, Core/domain gates, zero material ACT. At least a pre-registered bounded sample; no PASS based on isolated HTTP 200. Record per RQ/AC and outcome.

**Implementation authorization boundary:** only existing-contract minimal R1+R3 corrective patch is a candidate after HEAD/authorities/consumers review and RED; R2 contract-affecting changes need separate architectural approval. No automatic I04/Q01 advancement; canonical NEXT_MAIN remains I04 per ledger, but this quality repair is prioritized as bounded related work without phase redefinition.

```text
DIAGNOSTIC_REVIEW=ACCEPT_WITH_RESIDUAL
L02_L06_OUTCOME=REWORK
PRIMARY_CAUSES=GROUP_NONE/CAPABILITY_NONE_WITH_BUDGET_EXHAUSTION
L04_PROJECTION=REWORK
L01_PERSONAL_COUNT=INCONCLUSIVE_OWNER_LINK_REQUIRED
I03_ACCEPTED=YES_WITH_RESIDUAL
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT_RELATED=DELIA-C3-ORCHESTRATION-NONE-SELECTION-AND-PROJECTION-REMEDIATION-01
NEXT_MAIN=I04_PROVIDER_NEUTRAL_GENERALIZATION
```
