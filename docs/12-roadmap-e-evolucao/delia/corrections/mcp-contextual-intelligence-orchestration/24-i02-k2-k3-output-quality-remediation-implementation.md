# 24 — I02 K2/K3 · Bounded Output Quality Remediation · Implementation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-I02-K2-K3-BOUNDED-OUTPUT-QUALITY-REMEDIATION-01`  
**BASE_HEAD:** `dfd05a78b8ed608f3632f2222471c1adb2523fef` (post-pull; brief ref `9de23c918a…` is ancestor)  
**AUTHORITIES:** [14](./14-i02r3-independent-diagnostic-review-and-architecture-decision.md)–[23](./23-i02-k2-k3-quality-remediation-execution-brief.md)  
**EXISTING_EQUIVALENT:** `YES`  
**REUSE_DECISION:** `EXTEND` (`OperationalCapabilityOrchestrator` only)  
**I02_ACCEPTED:** `NO`  
**VERDICT:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Problems reproduced

| Case | Baseline (doc 21) | Defect class |
|---|---|---|
| **K2** | Continuity OK, 130 chars, usefulness PARTIAL | Model under-selected prior units; expansion gated only by `len < 120`, so shortish incomplete answers skipped expansion |
| **K3** | INDEX→`display_formats`, relevance PARTIAL | Lexical ranking + model pick accepted weak/adjacent topics; no post-select relevance floor |

## 2. Root causes

**K2:** `_prior_continuation_attempt` treated character length as the primary incompleteness signal. Coverage of available bullet/list units from prior OBSERVATION was not measured, so an incomplete checklist (~130 chars, few units) passed as “transformed”.

**K3:** `_rank_index_options_by_overlap` used plain token overlap only; `_bind_arguments_from_index` accepted any owner-declared id the model returned. Adjacent topics (e.g. display formatting vs panel legibility) were not rejected.

## 3. Implementation

### K2
- `_collect_extraction_units` / `_count_covered_extraction_units` / `_prior_extraction_incomplete`
- Expand via `_extraction_list_from_prior_excerpts` when coverage of available units is incomplete (half of units, min 3), independent of char count
- Preserve limitation-ask carve-out; never invent units absent from prior
- Log: `expand_incomplete_extraction`

### K3
- Index rows carry owner `hints` (summary/description/use_when strings) for ranking only
- Relevance score = lexical + stem affinity + intent-cluster affinity − mismatch penalty (provider-neutral clusters; no VISTA/TÉO hardcodes)
- Bind path: skip model select when best score `< floor`; reject weak/mismatched model picks (`reject_weak_relevance` / `no_relevant_option`)
- INDEX_SELECT instruction: prefer null over weak/partial match
- Honest clarification when catalog has no adequate topic

### Preserved
- R3-B typed capability+goal; FAST telemetry; OPERATIONAL/REASONING paths
- `GLOBAL_TURN_BUDGET_SECONDS=30`; stage-cap 10 OFF; args-headroom OFF
- MESSAGE≠ACT; MODEL_AUTHORED_FACTUAL_PROSE=NONE; no new planner/registry/cache

## 4. Tests

| Suite | Result |
|---|---|
| `tests/test_i02_k2_k3_output_quality.py` | PASS |
| I01 / I02 / R2 / R3 / R3A / R3B / ACR completion / MCP index probe | PASS (fixtures updated to use pertinent topics where nested SUCCESS is the subject under test) |
| Full `delia-api` pytest | PASS |

## 5. Live evaluation

Filled after deploy of implementation SHA:

| Field | Value |
|---|---|
| SOURCE_SHA | _pending commit_ |
| DEPLOYED_SHA | _pending_ |
| MODEL_ID | `moonshotai/kimi-k3` (expected) |
| CONFIG_FINGERPRINT | _pending_ |
| K1 | _pending_ |
| K2 | _pending_ |
| K3 | _pending_ |

## 6. Rollback

```text
git revert <IMPLEMENTATION_SHA>
```

## 7. State

```text
K2_SYNTHETIC=PASS
K3_SYNTHETIC=PASS
LIVE=PENDING_DEPLOY
I02_ACCEPTED=NO
C3_EXECUTED=NO
C4_AUTHORIZED=NO
C5_AUTHORIZED=NO
NEXT=DEPLOY_AUTHENTICATED_LIVE_THEN_COORDINATION_REVIEW
```
