# HELPDESK-OPS-004 — GLPI Action Card Field Inventory

**TASK:** HELPDESK-OPS-004-GLPI-ACTION-CARD-PARITY  
**BASE HEAD:** `e5f3d9e97989119c7dcbc0de837fd2d43d5c5ef0`  
**BRANCH:** `main`  
**DATE:** 2026-09-25  
**DIRTY LEFT UNTOUCHED:** `.cursor/plans/davi_herda_teo_vista.plan.md`, `minha-delpi-ai-api/docs/knowledge/_generated/api-delpi-openapi-catalog.md`, `plugins/tv-dashboard/tsconfig.tsbuildinfo`

## GLPI VERSION

| Item | Value | Evidence |
|---|---|---|
| GLPI_VERSION | **11.0.5** | `mapping.py` L1; `docs/.../02-arquitetura.md`; ledger H0.1 |
| INTERFACE VERSION | central / technician UI (not self-service) | `10-conversa-do-chamado.md` (ticket 1114) |
| API / HLAPI VERSION | **2.2.0** | live `GET https://helpdesk.centraldelpi.com.br/api.php/doc.json` → `info.version`; header `GLPI-API-Version: 2.2.0` |
| Plugins relevantes | none required for schemas below | OpenAPI generated from core + enabled plugins |

Live OpenAPI used as **provider field authority**. Classic UI screenshots = leads only. Classic `PendingReason` is **not** in HLAPI 2.2 schemas.

---

## Method

1. Code inventory of BFF/MFE/adapter (CONFIRMADO_NO_CODIGO).
2. Download live HLAPI OpenAPI from DELPI GLPI instance.
3. Extract POST schemas for Timeline Followup/Task/Solution/Validation/Document + Dropdown catalogs.
4. Cross-check prior matrices `15-capacidades-glpi.md` (note drift: X-45 still CONSOLE while POST `/tasks` exists).
5. UI form click-through / authenticated POST probes: **TO_INVENTORY** (no technician session in this agent run). Fields below marked PROVEN mean **HLAPI schema + path exist**; write acceptance still needs live postcondition before PARITY=PASS.

---

## REPLY / FOLLOWUP

| FIELD | GLPI LABEL (lead) | PROVIDER FIELD | PROVIDER ENDPOINT | REQ | CURRENT BFF | CURRENT MFE | STATUS |
|---|---|---|---|---|---|---|---|
| content | Comentário | `content` (html) | `POST …/Timeline/Followup` | yes | `content` | rich text | **PROVEN** (wired) |
| is_private | Privado | `is_private` | same | no | not written; read strips private | absent | **MISSING_BFF** write; read filter intentional (X-41). Enabling write without projecting private to authorized viewers breaks postcondition → treat as **BLOCKED** until private-read AuthZ |
| request_type / source | Origem | `request_type.id` → RequestType | same + `GET /Dropdowns/RequestType` | no | absent | absent | **MISSING_BFF** / **MISSING_MFE** (schema PROVEN) |
| template | Modelo | catalog only — **no** `template_id` on Followup | `GET /Dropdowns/FollowupTemplate` | no | absent | absent | **MISSING_BFF** catalog; apply = prefill content/is_private/request_type (**PROVEN** pattern) |
| pending reason | Motivo pendência | — | **not in HLAPI Followup schema** | — | — | — | **BLOCKED** (HLAPI); classic UI = CONSOLE lead |
| add to KB | Base conhecimento | KnowbaseItem paths exist; no Followup field | separate Knowbase APIs | — | — | — | **TO_INVENTORY** / likely **CONSOLE_ONLY** |
| attachment | Documento | Document / Document_Item | H12 legacy upload to Ticket | no | ticket-level attach | composer attach | **PROVEN** ticket-level; per-followup link **CONSOLE/FORA** (A-07) |
| promote to ticket | — | — | — | — | — | — | **CONSOLE_ONLY** (X-42) |

---

## SOLUTION

| FIELD | PROVIDER FIELD | ENDPOINT | CURRENT BFF/MFE | STATUS |
|---|---|---|---|---|
| content | `content` | `POST …/Timeline/Solution` | content only | **PROVEN** wired |
| type | `type.id` → SolutionType | + `GET /Dropdowns/SolutionType` | absent | **MISSING_BFF/MFE** (schema PROVEN) |
| template | catalog → prefill content/type | `GET /Dropdowns/SolutionTemplate` | absent | **MISSING_BFF** catalog |
| status | `status` 1..4 (None/Waiting/Accepted/Refused) | read on Solution | BFF returns ticket `status_id` after create | lifecycle claim MFE **DRIFT** vs tooltip; create effect **TO_INVENTORY** live |
| is_private | **not** on Solution schema | — | BFF sends `is_private:0` anyway | write flag may be ignored; keep public force |
| attachment | Document | H12 ticket attach | not on solution card | **MISSING_MFE** optional; same ticket Document |
| KB | — | — | — | **TO_INVENTORY** / CONSOLE |

---

## TASK (highest gap)

| FIELD | PROVIDER FIELD | ENDPOINT | CURRENT | STATUS |
|---|---|---|---|---|
| content | `content` | `POST …/Timeline/Task` | content + force `is_private:0` | **PROVEN** wired |
| state | `state` enum 0=Information,1=To do,2=Done | same | absent | **MISSING_BFF/MFE** (schema PROVEN) |
| duration | `duration` integer (unit **TO_INVENTORY**; classic actiontime=seconds) | same | absent | **MISSING_BFF/MFE** |
| category | `category.id` → TaskCategory | + `GET /Dropdowns/TaskCategory` | absent | **MISSING_BFF/MFE** |
| user_tech | `user_tech.id` → User | + users catalog | absent | **MISSING_BFF/MFE** |
| group_tech | `group_tech.id` → Group | + `GET /Administration/Group` | absent | **MISSING_BFF/MFE** |
| planned_begin / planned_end | `planned_begin`,`planned_end` date-time | same | absent | **MISSING_BFF/MFE** (planning PROVEN in schema) |
| is_private | `is_private` | same | forced 0 | **BLOCKED** toggle until private-read AuthZ |
| template | TaskTemplate catalog → prefill | `GET /Dropdowns/TaskTemplate` | absent | **MISSING_BFF** catalog |
| pending reason | — | not on TicketTask schema | — | **BLOCKED** HLAPI |
| reminder | Reminder entity (not ticket timeline task field) | `/…/Reminder` | — | **CONSOLE_ONLY** / conflation risk |
| attachment | Document on ticket | H12 | not on task card | optional ticket attach **TO_INVENTORY** semantics |

---

## DOCUMENT / ATTACHMENT

| FIELD | PROVIDER | CURRENT | STATUS |
|---|---|---|---|
| upload file | legacy `Document` + `Document_Item` itemtype Ticket | `POST /attachments` | **PROVEN** ATTACH FILE |
| HLAPI Timeline/Document | JSON Document schema (name, filename, comment, mime) — no multipart in OpenAPI | unused | **TO_INVENTORY** vs H12 |
| title (`name`) | Document.name | filename only | **MISSING_BFF** optional |
| category | DocumentCategory dropdown; **not** on Timeline Document schema | absent | **TO_INVENTORY** / likely CONSOLE |
| link existing | — | absent | **CONSOLE_ONLY** until proven useful |
| attach vs create document | product split | single attach action | semantic = ATTACH FILE (**PROVEN**); CREATE DOCUMENT entity extras **TO_INVENTORY** |

---

## APPROVAL

| FIELD | PROVIDER FIELD | CURRENT | STATUS |
|---|---|---|---|
| approver user | live write uses `itemtype_target=User`,`items_id_target` (proven e10); OpenAPI also lists `requested_approver_type`/`requested_approver_id` | `approver_user_id` | **PROVEN** user path |
| approver group | `requested_approver_type=Group` in schema | absent | **MISSING_BFF/MFE** (schema PROVEN; live write **TO_INVENTORY**) |
| submission_comment | `comment_submission` / `submission_comment` | `content` | **PROVEN** |
| requester | `requester` object (likely server-set) | not editable | **PROVEN** read-only display candidate |
| template | ValidationTemplate (+ approval_step) | absent | **MISSING_BFF** catalog; create schema **lacks** template_id / step id → prefill comment only until live proves step field |
| approval step | `GET /Dropdowns/ApprovalStep` (min_required_approval_percent) | absent | catalog **PROVEN**; bind on create **TO_INVENTORY** (not on TicketValidation schema) |
| attachment | — | absent | **TO_INVENTORY** |
| accept/reject | PATCH status 3/4 (live e10; OpenAPI enum text inconsistent) | wired | **PROVEN** |

---

## TIMELINE TYPES

| Kind | Provider | BFF | MFE filter | STATUS |
|---|---|---|---|---|
| Description | Ticket content | opening bubble | description | **PROVEN** |
| Followups | Timeline Followup | `kind=followup` | followups | **PROVEN** |
| Tasks | Timeline Task | `kind=task` | tasks | **PROVEN** |
| Documents | Timeline Document → `attachments[]` | attachments | documents | **PROVEN** (not timeline kind) |
| Approvals | Timeline Validation → `validations[]` | validations | approvals | **PROVEN** (not timeline kind) |
| Solutions | Timeline Solution | `kind=solution` | solutions | **PROVEN** |
| Automatic reminders | PendingReason / cron — **not** HLAPI timeline type | — | — | **BLOCKED** / CONSOLE |
| History | GLPI History log | — | — | **CONSOLE_ONLY** / **TO_INVENTORY** (no BFF source) |

Task list popover = client filter of `kind=task` — same source (**PROVEN**).

---

## PERMISSIONS (current vs target)

| Capability | Current | Notes |
|---|---|---|
| can_followup | status ≠ closed | POST followup **does not** enforce gate — gap |
| can_create_solution/task/request_approval | session_user_id ∈ technicians ∧ not closed | coarse “technician” |
| can_assign | list_users ACL | separate |
| can_private_followup / see private | — | all private stripped | **TO_INVENTORY** rights |
| can_plan_task | — | planning fields on schema; right **TO_INVENTORY** |
| Granular GLPI rights projection | not implemented | fail-closed; do not invent flags |

---

## CURRENT BFF GAPS (summary)

1. Writes: only `content` (+ forced public on solution/task; validation user target).
2. No dropdown catalogs for templates/types/task category/request type/groups/approval steps.
3. Timeline entries lack task/solution metadata for field-level postcondition.
4. Private content never projected.
5. Doc drift: `15` X-45 vs implemented POST task.

---

## PROPOSED CONTRACT CHANGES (FREEZE — additive)

### Catalogs (GET, pattern like `/ticket-categories`)

- `GET /request-types` — RequestType (`is_visible_followup` filter when supported)
- `GET /followup-templates`
- `GET /solution-types`
- `GET /solution-templates`
- `GET /task-categories` — TaskCategory (`is_helpdesk_visible` when present)
- `GET /task-templates`
- `GET /task-statuses` — static `{id,name}` from schema enum 0/1/2
- `GET /groups` — Administration/Group (task + future approval)
- `GET /validation-templates`
- `GET /approval-steps`

Templates are **catalog + prefill**; POSTs do **not** accept `template_id` (absent from HLAPI create schemas).

### Writes (extra=forbid, additive optional fields)

- `POST /followups`: `request_type_id?` — **not** `is_private` until private-read AuthZ
- `POST /solutions`: `solution_type_id?`
- `POST /tasks`: `state?`, `duration_seconds?`→`duration`, `category_id?`, `user_tech_id?`, `group_tech_id?`, `planned_begin?`, `planned_end?` — keep force `is_private:0`
- `POST /validations`: keep `approver_user_id`; additive `approver_type?: "user"|"group"` + `approver_id?` **only after** live Group write PROVEN

### Timeline projection (additive)

- task entries: `state`, `duration_seconds`, `category_name`, `user_tech_display_name`, `group_tech_display_name`, `planned_begin`, `planned_end`
- solution entries: `solution_type_name`, `solution_status`

### Explicitly NOT in freeze

- pending reason, KB save/search, history, automatic reminders, private toggle, admin CRUD of dropdowns, fake approval step on create without schema field, Document category without proven write path

---

## CONSOLE ONLY

- CRUD templates/types/categories/groups/approval steps
- Promote followup to ticket
- Full technician console tabs (costs, projects, items, …)
- GLPI Reminder tool as personal reminder
- History tab

## Wave status (2026-09-25)

| Wave | Escopo | Status |
|---|---|---|
| 1 | BFF catalogs + task/solution/followup write enrichment + Task MFE card | DONE (local, uncommitted) |
| 2 | Reply (template+origem) + Solution (template+tipo) + Approval (template prefill) MFE | DONE (local, uncommitted) |
| 3 | Approval title/category, approval group/step live, private AuthZ, live homolog | PENDING |

PARITY overall: **NOT PASS** — operational fields still need live postcondition + remaining gaps (private, pending reason, history, KB).
