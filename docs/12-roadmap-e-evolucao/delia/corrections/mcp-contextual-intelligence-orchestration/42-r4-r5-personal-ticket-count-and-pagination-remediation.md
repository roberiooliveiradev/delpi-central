# 42 — R4/R5 personal ticket count and pagination remediation

**DATA:** 2026-10-19  
**TASK_ID:** `DELIA-C3-HELPDESK-PERSONAL-TICKET-COUNT-AND-PAGINATION-REMEDIATION-01`  
**AUTHORITIES:** docs 30, 33–35, 38–41; ledger §§6.271–6.282; Helpdesk contrato `docs/.../helpdesk/03-contrato.md`; TÉO `helpdesk_read`  
**MODE:** `REUSE` Helpdesk BFF/TÉO MCP boundary; `EXTEND` `OperationalCapabilityOrchestrator` + pure semantics module  
**BASE_HEAD (task start):** `6e6024c952…` (brief REFERENCE_HEAD `5574be62…` superseded; concurrent audio foundation landed as `7fede85f9f` before this commit)  
**I03_ACCEPTED:** `YES_WITH_RESIDUAL` (unchanged)  
**I04_ACCEPTED:** `NO` (unchanged)  
**C3_EXECUTED:** `NO`  
**C4_AUTHORIZED:** `NO`  
**C5_AUTHORIZED:** `NO`  
**Q01_AUTHORIZED:** `NO`

## 1. Reanchor

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
HELPDESK_OWNER=helpdesk-api (BFF) via transformometro-api TÉO MCP helpdesk_read
DELIA_AUTHORITY=orchestration projection only — never ticket/AuthZ/identity owner
MATERIAL_ACT_COUNT=0
ARCHITECTURE_DECISION_REQUIRED=NO (no public contract change; owner gaps recorded)
```

## 2. Owner contract evidence (PROVEN)

| Surface | Evidence |
|---|---|
| List response | `items`, `page`, `page_size`, `has_more` — **no** `total_count` on BFF `TicketListPage` |
| Filters | `assignee_id` (legacy Search); **no** `requester_id` query filter |
| Session | `{linked, profile_sync?}` — **does not** expose GLPI `user_id` to MCP |
| Identity | BFF resolves session user internally; JWT/name/email ≠ assignee filter authority |
| Precondition | `409 glpi_link_required` preserved end-to-end |

## 3. Root causes

### R4 — personal scope

DÉLIA had no deterministic distinction between `ASSIGNED_TO_ME`, `REQUESTED_BY_ME`, `MY_TICKETS_AMBIGUOUS`, and visible-list queries. Ambiguous “para mim” could reach a ticket page and be framed as a personal total. Model-proposed `assignee_id` without provenance is already demoted by `_unproven_identifier_inputs`; personal assigned/requester counts still cannot be completed because the owner session contract does not expose a filterable self id / requester filter.

### R5 — page size as total

Owner pages feed `_synthesis_records` → `_render_synthesis` → `_list_header(len(selections))` (“Encontrei N registros”), equating page length with found total when `has_more=True`. No authoritative total field; no governed page walk.

## 4. Implementation (bounded)

| Surface | Change |
|---|---|
| `paginated_result_semantics.py` | Pure classifier + envelope extract + page aggregate + count resolution + personal-scope texts |
| `orchestration.py` | `_project_paginated_personal_or_count`; `_maybe_aggregate_paginated_count` (COUNT + non-personal); `_list_header(has_more)`; `render_specialist_outcome` early projection; pass `invocation_arguments` into synthesis |
| Tests | `test_r4_r5_personal_ticket_count_and_pagination.py` R45-T01…T22 + orch integration |

**Not created:** Helpdesk client paralelo, GLPI direto, cache local, RBAC novo, planner novo, branch de especialista, `total_count` no BFF.

### Behavioral contract after patch

| Input class | Behavior |
|---|---|
| Ambiguous personal count/list | Clarification (assigned vs requester) — never page-as-personal-total |
| Assigned without proven `assignee_id` | Honest identity/filter limitation |
| Requested without requester filter | Honest owner-contract limitation |
| Visible/non-personal COUNT + `total_count` | Authoritative total |
| Visible COUNT + `has_more` | Bounded same-capability page walk; complete aggregate or honest unknown |
| Visible COUNT + last page | Complete aggregate = `len(items)` |
| List + `has_more` | Header states page slice ≠ total |
| `glpi_link_required` | Unchanged precondition path; no fabricated count |

## 5. Tests

| Gate | Result |
|---|---|
| R45-T01…T22 + orch pagination | **PASS** |
| R1/R3 | **PASS** |
| R2 | **PASS** |
| I04 / ACR / presentation | **PASS** |
| Full `delia-api` pytest | **PASS** |

## 6. Live (operador@192.168.1.237)

```text
SOURCE_SHA=31a10b866956d3ac3ee3d80b5376f6430ca27095
DEPLOYED_SHA=31a10b866956d3ac3ee3d80b5376f6430ca27095
HOST_GIT_HEAD=31a10b866956d3ac3ee3d80b5376f6430ca27095
DEPLOY=./infra/scripts/up-prod-sequential.sh --pull --build delia-api
MODEL_ID=moonshotai/kimi-k3
MODEL_PROVIDER=openai_compatible
CONFIG_FINGERPRINT=DELIA_LLM_PROVIDER=openai_compatible;BUDGET=30;STAGE=30
AUTHENTICATED_SUBJECT_CLASS=password-grant Keycloak user (preferred_username=user)
HELPDESK_SESSION_LINKED=false
CONTAINER_R45_PYTEST=PASS (28)
SYMBOLS=_project_paginated_personal_or_count=YES; paginated_result_semantics=YES
```

| Case | HTTP | ms | Outcome |
|---|---|---|---|
| L01A `Quantos chamados tem para mim?` | 200 | ~30025 | `SOURCE_UNAVAILABLE` / `NON_GROUNDED`; **no** page-as-total; corr `e8726102-…` select_group ok then select_capability **timeout** |
| L01A2 retry | 200 | 30054 | same class; corr `1f44d5be-…` select_group ~9961ms then select_capability timeout ~19751ms |
| L01B assigned | 200 | ~30016 | same timeout class; no fabricated total |
| L01C requester | 200 | ~30041 | same |
| L01D visible count | 200 | ~30015 | same |
| L02 control | 200 | ~30039 | same timeout class (LLM budget) |

```text
PERSONAL_COUNT_LIVE=INCONCLUSIVE
REASON=MODEL_SELECT_CAPABILITY_TIMEOUT_UNDER_30S + SUBJECT_GLPI_UNLINKED
L01_UNLINKED_PRECONDITION=PROVEN_VIA_HELPDESK_SESSION_linked=false
L01_GLPI_LINK_OWNER_HINT=NOT_REACHED (orchestration timed out before owner READ)
L01_LINKED=TEST_NOT_RUN
NO_FABRICATED_TEN_AS_TOTAL=PASS (all live cases)
MATERIAL_ACT_COUNT=0
```

Deterministic / container tests cover pagination, unknown total, personal gates, and `glpi_link_required` presentation. End-to-end personal count against a linked subject remains **blocked** on owner identity exposure / requester filter and was not exercised live (subject unlinked + model stage timeout).

## 7. Residuals / BLOCKED (owner)

1. **ASSIGNED personal total** — requires owner-exposed authorized technician id (session does not publish `user_id` to MCP).  
2. **REQUESTED personal total** — requires `requester_id` (or equivalent) list filter on Helpdesk BFF.  
3. **Authoritative `total_count` on list** — optional owner enhancement; legacy Search already knows `totalcount` internally but does not project it.  
4. Live linked-subject outcome verification.  

These are **OWNER_CONTRACT_GAP** / environment gaps — not DÉLIA parallel authority.

## 8. Phase / acceptance mapping

| AC | Status |
|---|---|
| AC-01 routing Helpdesk | Preserved (prior L01); this task does not regress selection |
| AC-02 personal scope distinguished | **PASS** (deterministic) |
| AC-03 identity via legitimate boundary | **PASS** (no invent; unproven assignee demoted) |
| AC-04 GLPI link preserved | **PASS** (tests + no bypass) |
| AC-05 page size ≠ total | **PASS** |
| AC-06 authoritative or complete pagination | **PASS** for visible/non-personal; personal assigned/requested **BLOCKED** owner |
| AC-07 unknown total honest | **PASS** |
| AC-08 status filters | **PASS** (forwarded; not reinvented) |
| AC-09 pagination bounded | **PASS** |
| AC-10 no undue personal data | **PASS** |
| AC-11 no material ACT | **PASS** |
| AC-12 R1/R2/R3 preserved | **PASS** (regression) |
| AC-13 backend full PASS | **PASS** |
| AC-14 SHA/config/model live | **PASS** (SOURCE=DEPLOYED=`31a10b8669`, kimi-k3) |
| AC-15 live unlinked | **PARTIAL** — `linked=false` proven; owner `glpi_link_required` **NOT_REACHED** (model timeout before READ) |
| AC-16/17 linked personal outcome | **TEST_NOT_RUN** / **BLOCKED** owner identity |
| AC-18 docs/ledger | This document + §6.284 |
| AC-19 commit/push | `31a10b8669` pushed; live docs follow-up |
| AC-20 no parallel authority | **PASS** |

```text
IMPLEMENTATION_VERDICT=IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW
I03_ACCEPTED=YES_WITH_RESIDUAL
I04_ACCEPTED=NO
C3_EXECUTED=NO
NEXT=COORDINATION_INDEPENDENT_REVIEW
```
