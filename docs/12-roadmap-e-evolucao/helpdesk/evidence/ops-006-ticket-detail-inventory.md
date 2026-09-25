# HELPDESK-OPS-006 — Ticket Detail Inventory (Wave A)

**PARENT:** HELPDESK-OPS-006-TICKET-DETAIL-ITSM-PARITY  
**PARENT STATUS:** PENDING  
**CURRENT EXECUTION:** HELPDESK-OPS-006A-TICKET-DETAIL-EXISTING-CONTRACT-SURFACES  
**WAVE:** A  
**BASE HEAD:** `00d14b99fa4d1191c865b6c281501af7ea232e4b`  
**BRANCH:** `main`  
**DATE:** 2026-09-25  

**Disclaimer:** OPS-006 Wave A repository/contract inventory complete; provider expansion inventory pending.  
This document does **not** claim full OPS-006 inventory complete.

**Dirty left untouched:** `.cursor/plans/davi_herda_teo_vista.plan.md`, `minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md`, `plugins/tv-dashboard/tsconfig.tsbuildinfo`

---

## Evidence taxonomy

| Column | Allowed values |
|---|---|
| EVIDENCE_STATE | PROVEN \| TO_INVENTORY \| PLANNED \| TARGET |
| EXECUTION_STATUS | PASS \| FAIL \| PENDING \| INCONCLUSIVE \| TEST_NOT_RUN \| STALE_EVIDENCE |
| GAP_OR_DISPOSITION | EXISTING_READ \| EXISTING_WRITE \| EXISTING_CONTRACT \| MISSING_BFF \| PRODUCT_DECISION_REQUIRED \| PROVIDER_INVENTORY_REQUIRED \| CONSOLE_CANDIDATE \| BLOCKED \| N/A \| FIX_WAVE_A \| BUG |

---

## Wave A verified inventory (repository/contract)

| Feature | Evidence state | Current contract | Gap/disposition | Execution | Wave |
|---|---|---|---|---|---|
| Details/context duplication | PROVEN | N/A — `TicketContextPanel` in main+aside when details | BUG / FIX_WAVE_A | PASS (Wave A) | A |
| Requester read | PROVEN | `requester_display_name` | EXISTING_READ | — | A |
| Assign technician | PROVEN | `PUT …/assignee` + `can_assign` | EXISTING_WRITE | — | A |
| Observer read | PROVEN | `observers_display_name` (string) | EXISTING_READ | — | A |
| Observer CRUD | TO_INVENTORY | write only on create ticket | MISSING_BFF | PENDING | B |
| SLA names (tto/ttr) | PROVEN | `sla_tto`, `sla_ttr` (level **names**, not deadlines) | EXISTING_READ | — | A |
| SLA deadlines | TO_INVENTORY | absent | MISSING_BFF | PENDING | B |
| Dates lifecycle | PROVEN | `created_at`, `updated_at`, `solved_at`, `closed_at` | EXISTING_READ | — | A |
| Approvals list/request/decide | PROVEN | `validations[]`, POST validations, accept/reject, `can_request_approval`, `mine_to_decide` | EXISTING_CONTRACT | — | A |
| Global validation status | TO_INVENTORY | absent on DTO | PROVIDER_INVENTORY_REQUIRED | PENDING | B |
| Statistics / milestones | TO_INVENTORY | absent | PROVIDER_INVENTORY_REQUIRED | PENDING | B |
| Items (Item_Ticket) | TO_INVENTORY | absent | MISSING_BFF | PENDING | B |
| History (Log) | TO_INVENTORY | Timeline followup/task/solution only | MISSING_BFF | PENDING | B |

Validation waiting constant (BFF): `VALIDATION_WAITING = 2` in `helpdesk-api/.../mapping.py` — usable as **row** pending count in UI summary only, not as ticket-global approval status.

---

## Parent residual (not Wave A)

### Wave B candidates
- SLA deadlines (+ internal TTO/TTR if authorized)
- Statistics / milestones
- Observers CRUD
- Items (Item_Ticket)
- History (Log) with privacy AuthZ

### Wave C candidates
- Knowledge Base relations
- Projects / project tasks
- Problems (link vs create-from — distinct capabilities)
- Changes (link vs create-from)
- Contracts
- Related assistance objects

Disposition for Problems/Changes/etc.: `TO_INVENTORY` + `PRODUCT_DECISION_REQUIRED` + `PROVIDER_INVENTORY_REQUIRED` — **not** permanent CONSOLE_ONLY without product decision.

### Wave D candidates
- Costs
- PDF export (+ private AuthZ)
- Previous/next when list context exists
- Generic Save (CONSOLE_CANDIDATE / N/A)
- Delete ticket (PRODUCT_DECISION_REQUIRED; out of Wave A)

---

## Provider inventory note

Future waves use **authoritative provider inventory**: existing BFF/adapter contracts → provider/API capability → homolog/runtime verification when needed. Not HLAPI-only.

---

## Wave A hard boundary

- BACKEND CHANGES: NONE
- CONTRACT IMPACT: NONE
- Surfaces: `conversation` | `details` | `approvals`
- No tabs for History / Items / KB / Costs / Projects / Problems / Changes / Contracts / PDF
