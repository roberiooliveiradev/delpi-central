# 30 — Cross-specialist ticket-count misrouting and pagination evidence

**DATE:** 2026-10-19. **STATUS:** `EVIDENCE_RECORDED / REMEDIATION_NOT_IMPLEMENTED`. **SOURCE:** User's screenshots of DÉLIA and direct read-only TÉO MCP calls in coordination. **HEAD at investigation:** `f8a07952868efd8e8e912b23020bd4c9063a3a81` (main advanced concurrently; reanchor before implementation). Existing I03 acceptance and K2/K3 nonregression remain separately governed by ledger.

## Reproduction/observation

- User question in DÉLIA: *quantos chamados tem para mim?*
- DÉLIA selected `TEO`, returned **10 records from `transformometro-api`**, including closed/solved records, and reported found-record count rather than verified personal ticket total. The screenshot does not prove a legitimate assigned/requester filter or total across pages.
- Direct TÉO owner MCP `helpdesk_read(action='session')`: `linked=true` (read-only); `helpdesk_read(action='capabilities')`: succeeds; `helpdesk_read(action='tickets',page=1,page_size=10)` returned 10 items and page=2 returned 10 items. Result schema `helpdesk_tickets_v1` contains `page`, `page_size`, `has_more` and each item includes `assigned_user_id` and `requester_id`. No global total field observed. No personal identifier or ticket content persisted.
- This proves list-page size **cannot be represented as total**, and confirms a Helpdesk/GLPI source exists; it does **not** prove the user's actual ticket count nor a specific hardcoded default in DÉLIA. Additional pages need not share assigned/requester user.

## Root-cause candidates (not proven yet)

1. Semantic capability selection may route 'chamados' to generic Transformômetro instead of owner Helpdesk; inspect actual selected capability, provider metadata and intent in correlation logs.
2. An upstream tool/API may cap a page at 10; frontend may show the returned `len(items)` as a count. Inspect owner pagination contract and orchestration projection; never change limits blindly.
3. Personal scope 'para mim' may be lost; distinguish assigned to me, requested by me, and both; resolve authenticated identity via legitimate owner/AuthZ boundary, not name matching or JWT-only permission.

## Bounded remediation gate

Task candidate: `DELIA-C3-I03-HELPDESK-PERSONAL-TICKET-COUNT-ROUTING-01` as an I03 cross-specialist discovery regression or separately authorized bounded correction, **subject to master plan/ledger reanchor**. Existing equivalent: TÉO MCP `helpdesk_read` (YES); reuse by owner contract, no duplicated helpdesk APIs. Require RED tests for count vs page count, status/time scope, assignment/requester filter, pagination aggregation or authoritative total, unknown total honest response, renamed provider and alternative owner, RBAC and zero ACT. Verify correct chosen source and user-scoped outcome live with SHA/model/config; privacy-safe logs. No backend patch or deployment in this review.

```text
DIRECT_OWNER_TEST=PASS_READ_ONLY
DELIA_PERSONAL_TICKET_TOTAL=INCONCLUSIVE
TEN_RECORDS_AS_TOTAL=NOT_VALIDATED
ROOT_CAUSE=TO_INVENTORY
SECURITY_ACT=0
NEXT=REANCHOR_AND_BOUNDED_ROUTING_COUNT_CORRECTION
```
