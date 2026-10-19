# 44 — R45 pagination integrity + select_capability timeout rework

**DATE:** 2026-10-19  
**TASK_ID:** `DELIA-C3-R45-PAGINATION-INTEGRITY-AND-PRODUCTION-SSH-VALIDATION-01`  
**BASE_HEAD:** `154201752f941cab34a84b69531fd0270c6b9bea` (pre-change)  
**SOURCE:** Independent review [43](./43-independent-r4-r5-review-pagination-integrity-gate.md), implementation [42](./42-r4-r5-personal-ticket-count-and-pagination-remediation.md), ledger §6.285.

## 1. Mission

1. Close doc-43 R5 gaps: unsigned `has_more`, isolated last page ≠ total, aggregation integrity.  
2. Diagnose live `select_capability` ~30s timeout before Helpdesk owner READ.  
3. Apply the smallest safe selection recovery covered by existing contracts.  
4. Full `delia-api` pytest, controlled SSH deploy, real-model live validation.  
5. **Not** accept I04 / C3–C5 / Q01; **not** create parallel Helpdesk/GLPI/planner.

## 2. R5 root cause (PROVEN in code)

| Defect | Prior behavior | Required |
|---|---|---|
| Unsigned completeness | `aggregate_paginated_pages` could mark `complete=True` when `has_more=None` | Without authoritative total or explicit `has_more=False` after a first-page contiguous walk → **UNKNOWN** |
| Isolated last page | `resolve_count_semantics` treated `page>1` + `has_more=False` as `COMPLETE_AGGREGATE=len(items)` | Last page alone ≠ query total |
| Integrity | Gaps/dups/failures could still project totals | Fail closed to UNKNOWN |

## 3. R5 fix (minimal)

Extended existing `paginated_result_semantics.py`:

- Walk completeness requires **start at first page**, contiguous page numbers (when present), last `has_more is False`, or owner authoritative total.
- `has_more is None` → `unsigned_completeness` / never complete.
- Isolated `page>1` + `has_more=False` → `PARTIAL_UNKNOWN`.
- Duplicate pages/ids, missing intermediate pages, malformed/failed pages, missing stable ids, authoritative total conflicts → incomplete / failed; count remains unknown.

Invariants locked:

```text
PAGE_SIZE != TOTAL
LAST_PAGE_ITEMS != TOTAL
UNKNOWN_COMPLETENESS != COMPLETE
PARTIAL_AGGREGATION != AUTHORITATIVE_TOTAL
```

## 4. Selection timeout root cause (PROVEN class)

Live L01 (doc 42): `select_group` succeeded (~10s) then `select_capability` model stage exhausted the 30s turn → `model_timeout` → owner Helpdesk **NOT_REACHED**. Not a Helpdesk/GLPI client defect.

**Fix (contract-safe, provider-neutral):** when the user ask is ticket **COUNT/LIST** and the selected group's invocable surface has **exactly one** READ capability whose input schema advertises `action` enum including `tickets`, select that capability structurally and skip the redundant model capability-selection stage. No `if teo`, no forced `helpdesk_read` by name, no global budget increase. Write / non-ticket / multi-match surfaces still use the model path.

## 5. Tests

| Suite | Result |
|---|---|
| R45R-T01…T18 (`test_r45_pagination_integrity_rework.py`) | **PASS** |
| SEL-T01…T12 core + timeout integration (`test_r45_selection_timeout_rework.py`) | **PASS** |
| Original R4/R5 (`test_r4_r5_personal_ticket_count_and_pagination.py`, T10 updated) | **PASS** |
| Full `delia-api` pytest | **PASS** |

## 6. Deploy / live

```text
PRODUCTION_HOST_VERIFIED=srv-api (operador@192.168.1.237)
PRODUCTION_SERVICE=delpi-delia-api
PRODUCTION_SHA_BEFORE=70c7be6a28783189a6934917ee953db14f7a58bb
PRODUCTION_SHA_AFTER=8caba9310f4ea8ab57731091916c5b48ad6443bd
SOURCE_SHA=8caba9310f4ea8ab57731091916c5b48ad6443bd
DEPLOYED_SHA=8caba9310f4ea8ab57731091916c5b48ad6443bd
DEPLOY_METHOD=./infra/scripts/up-prod-sequential.sh --pull --build delia-api
HEALTH_AFTER=healthy {"service":"delia-api","status":"available"}
MODEL_ID=moonshotai/kimi-k3
MODEL_PROVIDER=openai_compatible
MODEL_STAGE_TIMEOUT_SECONDS=30
SUBJECT=password-grant preferred_username=user
HELPDESK_SESSION_LINKED=false
ROLLBACK_EXECUTED=NO
```

| Case | HTTP | ms | Outcome (sanitized) |
|---|---|---|---|
| L01A para mim | 200 | 20966 | `structural_ticket_list_with_goal` → `helpdesk_read` → owner `glpi_link_required`; **no** page-as-total; corr `e2394d09-…` |
| L01B atribuídos | 200 | 27145 | same class; corr `4a22b420-…` |
| L01C eu abri | 200 | 24399 | same; corr `8a150c97-…` |
| L01D em aberto | 200 | 23969 | same; corr `6c25edd0-…` (`arg_keys=action,status`) |
| L01E liste meus | 200 | 27181 | same; corr `899e623e-…` |
| L03 TÉO metodologia | 200 | 30040 | `NON_GROUNDED` budget class (não-ticket; residual I02) |
| K4-C no-match | 200 | 30018 | clarification; sem total fabricado |

```text
OWNER_READ_REACHED=YES (all L01*)
SELECT_CAPABILITY_TIMEOUT=NOT_OBSERVED_ON_L01
STRUCTURAL_DECISION=structural_ticket_list_with_goal
NO_FABRICATED_TEN_AS_TOTAL=PASS
L01_UNLINKED_PRECONDITION=PROVEN (linked=false + glpi_link_required)
L01_LINKED=TEST_NOT_RUN — NO_AUTHORIZED_LINKED_SUBJECT
MATERIAL_ACT_COUNT=0
```

## 7. Acceptance mapping (this task)

| Item | Status |
|---|---|
| R5_EXACT_COUNT integrity | **IMPLEMENTED** — pending independent review |
| R4 personal projection | Preserved |
| Selection timeout avoidable class | **MITIGATED** for unique ticket-list schema COUNT/LIST |
| I03 | `YES_WITH_RESIDUAL` (unchanged) |
| I04 / C3 / C4 / C5 / Q01 | **NO** / not authorized |

```text
IMPLEMENTATION_VERDICT=IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
