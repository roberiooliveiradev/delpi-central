# 24 — I02 K2/K3 · Bounded Output Quality Remediation · Implementation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I02-K2-K3-BOUNDED-OUTPUT-QUALITY-REMEDIATION-01`  
**BASE_HEAD:** `dfd05a78b8ed608f3632f2222471c1adb2523fef` (brief ref `9de23c918a…` is ancestor)  
**IMPLEMENTATION_SHA / DEPLOYED_SHA:** `ddf0bef7870201850745c6f88b00bc6a169360b6`  
**AUTHORITIES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md)–[23](./23-i02-k2-k3-quality-remediation-execution-brief.md)  
**EXISTING_EQUIVALENT:** `YES`  
**REUSE_DECISION:** `EXTEND` (`OperationalCapabilityOrchestrator` only)  
**I02_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Problems reproduced

| Case | Baseline (doc 21) | Defect class |
|---|---|---|
| **K2** | Continuity OK, 130 chars, usefulness PARTIAL | Model under-selected prior units; expansion gated only by `len < 120` |
| **K3** | INDEX→`display_formats`, relevance PARTIAL | Lexical ranking + unbound model pick accepted weak/adjacent topics |

## 2. Root causes

**K2:** Character length was the primary incompleteness signal; coverage of available prior bullet/list units was not measured.

**K3:** Index bind accepted any owner-declared id the model returned without a relevance floor; adjacent topics could win.

## 3. Implementation

### K2
- `_collect_extraction_units` / `_count_covered_extraction_units` / `_prior_extraction_incomplete`
- Expand when unit coverage is incomplete (not char-count-only); limitation-ask carve-out
- Log: `expand_incomplete_extraction`

### K3
- Index rows include owner `hints` for ranking only
- Relevance score: lexical + stem + intent clusters − mismatch
- Skip/reject below floor (`no_relevant_option` / `reject_weak_relevance`); prefer clarification over weak nested READ
- INDEX_SELECT instruction: null over weak/partial match

### Preserved
R3-B typed merge; FAST telemetry; OPERATIONAL/REASONING; budget/stage 30; stage-cap10 OFF; args-headroom OFF; MESSAGE≠ACT; no new planner.

## 4. Synthetic tests

| Suite | Result |
|---|---|
| `tests/test_i02_k2_k3_output_quality.py` | PASS |
| I01 / I02 / R2 / R3 / R3A / R3B / ACR / MCP index | PASS |
| Full `delia-api` pytest | PASS |

## 5. Live evaluation (authenticated, MESSAGE-only)

| Field | Value |
|---|---|
| TARGET | `srv-api` `delpi-delia-api` healthy |
| MARKERS | `expand_incomplete_extraction` + `_index_selection_is_relevant` in image |
| MODEL | `moonshotai/kimi-k3` / `openai_compatible` |
| BUDGET / STAGE | **30** / **30** |
| SAMPLE | K1=1, K2=1 same session, K3=1 — no retries |

### K1 — TÉO (sha256-8 `2a8147e1`)

**Correlation:** `8acfc611-55f0-4120-9808-2406a51d9786`

```text
HTTP=200 TOTAL_MS=17010 SPECIALIST=teo CAPABILITY=get_methodology_guide
TYPED_WITH_CAPABILITY=YES DECISION_PATH=OPERATIONAL GROUNDING=GROUNDED
CONTENT_CHARS=2032 LIMITATIONS=result_truncated MATERIAL_ACT=0
```

**K1_RESULT:** `PASS_WITH_LIMITATION` (functional regression OK vs 20199ms baseline).

### K2 — checklist continuity

**Correlation:** `f090331b-655b-4531-bab2-a17c04318214`

```text
prior_evidence_sufficient=yes
prior_continuation=transformed excerpts=12
OWNER_REINVOCATION=NO
HTTP=200 TOTAL_MS=18570 GROUNDING=NON_GROUNDED (continuity)
LIMITATIONS=prior_turn_evidence_only
CONTENT_CHARS=219 (baseline 130 / historical 48)
BULLET_LINES=5 covering required_inputs + questions from prior guide
MATERIAL_ACT=0
UNSUPPORTED_CLAIMS=0 (verbatim prior units)
```

**K2_RESULT:** `PASS_WITH_LIMITATION` — substantive extraction of inputs/questions; usefulness improved; residual: not every prior unit always expanded when model coverage already meets the gate.

### K3 — VISTA relevance / honest no-match

**Correlation:** `7f19aa58-1a06-446b-998d-34b7f249004c`

```text
SPECIALIST=vista CAPABILITY=get_product_guide TYPED_WITH_CAPABILITY=YES
INDEX_READ=YES identifiers=11
INDEX_SELECT=no_match (model null / weak rejected — NOT display_formats)
NESTED_GUIDANCE=NOT_REACHED (correct for inadequate match)
CLARIFICATION=YES (asks which guide theme: legibility/layout/visualization)
HTTP=200 TOTAL_MS=28993 GROUNDING=NON_GROUNDED MATERIAL_ACT=0
```

**K3_RESULT:** `PASS` for safe absence-of-adequate-topic handling (not nested-guidance success). Avoids prior PARTIAL `display_formats` mis-selection.

## 6. Rollback

```text
git revert ddf0bef7870201850745c6f88b00bc6a169360b6
```

## 7. State

```text
K2_SYNTHETIC=PASS
K3_SYNTHETIC=PASS
K1_LIVE=PASS_WITH_LIMITATION
K2_LIVE=PASS_WITH_LIMITATION
K3_LIVE=PASS_SAFE_CLARIFICATION
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
