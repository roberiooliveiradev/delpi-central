# TÉO Capability Matrix (canonical)

**Status:** CURRENT (HEAD-bound inventory + governance)  
**Owner:** `transformometro-api` (Transformômetro domain)  
**Persona:** TÉO = specialist capability — **not** a parallel AI to DÉLIA.

This file is the **single canonical matrix** for TÉO surface exposure.  
MCP tool detail remains in [`teo-mcp-capability-parity.md`](./teo-mcp-capability-parity.md).  
Do not duplicate the full matrix in Instructions, Knowledge, or DÉLIA docs — link here.

## Architecture decision

| Role | Authority |
|---|---|
| **DÉLIA** | IA / experiência de orquestração da DELPI |
| **TÉO** | Specialist/capability de transformação digital e processos |
| **Transformômetro** | Domain authority (processos, revisões, docs, atas, …) |
| **MCP** | Adapter de capabilities (Plugin/Agent target) |
| **GPT Actions** | Adapter compacto **GOVERNED_PREPARE_COMMIT_V2** (Builder-importable) |

```text
Canonical domain capability
  → Application / use case
    → HTTP domain API
    → MCP adapter
    → GPT Action adapter
    → DÉLIA capability adapter (PLANNED — not proven at this HEAD)
```

**Rules**

- Capability parity ≠ transport parity (1 capability ≠ 1 tool ≠ 1 operation).
- New capability ≠ new GPT Action route (prefer catalog entity / existing ops).
- `TÉO capability ≤ authenticated user capability` on every surface.
- No independent TÉO conversational runtime / `/transformometro/teo/query`.
- No generic proxy (`call_any_route`, SQL, arbitrary HTTP).
- Entity writes: `gpt_prepare_record_change` → opaque `proposal_handle` → `gpt_commit_proposal`.
- Specialized workflows: Action = PREPARE; commit via the same `gpt_commit_proposal` (not a generic proxy).

## GPT ACTION SURFACE BUDGET

Documented project guardrail (not an external vendor claim): prefer **≤ ~30 importable operations** (`custom-gpt-actions-integration.mdc` + `test_openapi_has_at_most_30_operations`).

| Metric | Before V2 | After V2 |
|---|---|---|
| Paths (Builder-visible) | 18 | **18** |
| Importable operations | 21 | **18** |
| Entities in catalog | 19 (`process_document`) | 19 |
| Added | `gpt_prepare_record_change`, `gpt_commit_proposal` | +2 |
| Removed from Builder | create/update/delete/duplicate/commit_improvement_package | −5 |
| Legacy HTTP shims (off-OpenAPI) | create/update/delete/duplicate/commit_package → PREPARE-only | yes |
| Remaining margin vs ≤30 | 9 | **12** |

Meta route `gpt_get_openapi_schema` is **not** importable.

### Action Surface Gate (required before any new operation)

Classify each gap:

| Class | Meaning |
|---|---|
| A `EXISTING_OPERATION` | Already covered |
| B `EXISTING_OPERATION_EXTENDED` | Additive safe extension |
| C `EXISTING_CATALOG_ENTITY` | Governed CRUD entity allowlist |
| D `EXISTING_SPECIALIZED_OPERATION_EXTENDED` | Specialized op can absorb |
| E `NEW_OPERATION_REQUIRED` | Only if A–D fail **and** budget allows |

Rejected by policy: `gpt_call_any_route`, `gpt_http_proxy`, `gpt_run_sql`, `gpt_query_anything`, `gpt_invoke_tool`, `gpt_generic_write`.

## Recent capability mapping decisions

| Capability | Domain | Action mapping | MCP mapping | DÉLIA | Classification |
|---|---|---|---|---|---|
| **Process Documentation** | PROVEN CRUD | **C `EXISTING_CATALOG_ENTITY`** `process_document` | `search_records` / `get_record` / `prepare_record_change` / `commit_proposal` | PLANNED | **FULL_PARITY** (Actions+MCP); DÉLIA PLANNED |
| **Tasks** (`tm_tasks`) | PROVEN | **NOT_EXPOSED** — lifecycle (complete/cancel/my-tasks) ≠ clean CRUD; avoid signature-projection confusion | NOT_EXPOSED | NOT_APPLICABLE | **DOMAIN_ONLY_BY_DESIGN** |
| **Interaction Room** | PROVEN | **NOT_EXPOSED** — human collaboration; TÉO is not a room participant | NOT_EXPOSED | NOT_APPLICABLE | **DOMAIN_ONLY_BY_DESIGN** |
| **Process Workspace** | UI composition | **DOMAIN_COMPOSITION_ONLY** — consume underlying reads | same | same | **NOT_APPLICABLE** |

### PROCESS_DOCUMENTATION_ACTION_MAPPING = `EXISTING_CATALOG_ENTITY`

Justification: list/get/create/update/delete fit governed allowlisted CRUD with explicit schema, validators via `ProcessDocumentUseCases`, AuthZ `transformometro.access`, no arbitrary table/route. Creating five `gpt_*_process_document` ops would waste Action budget without semantic gain.

### TASK_ACTION_MAPPING = `NOT_EXPOSED`

### INTERACTION_ROOM_ACTION_MAPPING = `NOT_EXPOSED`

### PROCESS_WORKSPACE_MAPPING = `DOMAIN_COMPOSITION_ONLY`

## Capability parity matrix (surfaces)

| Capability | Owner | R/W | MCP | GPT Action | DÉLIA | AuthZ owner | Classification |
|---|---|---|---|---|---|---|---|
| User context | TM | R | `get_my_context` | `gpt_get_my_context` | PLANNED | AuthN | FULL_PARITY* |
| Catalog / registration guide | TM | R | `get_catalog` | `gpt_get_catalog` | PLANNED | view | FULL_PARITY* |
| Methodology guide | TM | R | `get_methodology_guide` | `gpt_get_methodology_guide` | PLANNED | view | FULL_PARITY* |
| Process context | TM | R | `get_process_context` | `gpt_get_process_context` | PLANNED | view/process | FULL_PARITY* |
| Dashboard analyze | TM | R | `analyze` | `gpt_analyze` | PLANNED | dashboard | FULL_PARITY* |
| Entity CRUD (17 legacy + process_document) | TM | R/W | search/get + prepare_record_change + commit_proposal | gpt_prepare_record_change + gpt_commit_proposal | PLANNED | per entity | FULL_PARITY* |
| Activate revision | TM | W | prepare_activate_revision → commit_proposal | `gpt_activate_revision` + commit | PLANNED | revisao manage | FULL_PARITY* |
| Recalculate dashboard | TM | W | prepare_recalculate_dashboard → commit_proposal | `gpt_recalculate_dashboard` + commit | PLANNED | dashboard | FULL_PARITY* |
| Improvement package | TM | W | prepare_improvement_package → commit_proposal | validate + commit | PLANNED | package AuthZ | FULL_PARITY* |
| Evidence link/metadata | TM | R/W | list + prepare_manage_evidence → commit_proposal | list + manage + commit | PLANNED | manage + confirm_delete | FULL_PARITY* |
| Process timeline | TM | R | `get_process_timeline` | `gpt_get_process_timeline` | PLANNED | view | FULL_PARITY* |
| Shared resource cost adjust | TM | W | prepare_adjust_shared_resource_cost → commit_proposal | `gpt_adjust_shared_resource_cost` + commit | PLANNED | parity | FULL_PARITY* |
| Meeting minute workflow/manage | TM | R/W | prepare_* + commit_proposal (+ read/analysis) | gpt_meeting_* + commit | PLANNED | minutes svc | FULL_PARITY* |
| **Process documentation** | TM | R/W | via record tools | via record entity | PLANNED | `transformometro.access` | FULL_PARITY* |
| Tasks | TM | R/W | — | — | — | access | DOMAIN_ONLY_BY_DESIGN |
| Interaction room | TM | R/W | — | — | — | access | DOMAIN_ONLY_BY_DESIGN |
| Process workspace UI | MFE | R | — | — | — | — | NOT_APPLICABLE |

\*FULL_PARITY = Actions + MCP mapped to same application services. DÉLIA consumption = **PLANNED / NOT_PROVEN** (no runtime adapter in `delia-api` at this HEAD).

## AuthZ parity

| Capability | MCP | Actions | DÉLIA | Canonical enforcement |
|---|---|---|---|---|
| Process document | User JWT → use case `require_access` | Same dispatch → use case | Must use user delegation when built | `ProcessDocumentUseCases` |
| Entity CRUD (other) | Same as GPT services | Same | PLANNED | Domain + branch_access helpers |
| Writes governed | PREPARE → commit_proposal + confirm flags | Conversational confirm + backend AuthZ | Must show + human confirm before commit | Orchestrator / services |
| MCP tool count | **20** (`CAPABILITY_GOVERNED_V2`) | — | — | constants.MCP_SURFACE_BUDGET |

Profile/cargo/department/context ≠ AuthZ. Service account must not impersonate user on MCP `/mcp`.

## PREPARE / COMMIT parity (writes)

| Capability | PREPARE | Confirm | COMMIT | Read-back | Surfaces |
|---|---|---|---|---|---|
| create/update/delete/duplicate record (incl. process_document) | MCP `prepare_record_change` | MCP proposal; Actions conversational | MCP/Actions `commit_proposal` | Yes | MCP + Actions |
| activate / package / evidence / cost / meeting | MCP specialized `prepare_*` | confirm_* where required | MCP/Actions `commit_proposal` | Yes | MCP + Actions |
| Tasks / Room | N/A | N/A | N/A | N/A | Not exposed |

## DÉLIA readiness

| Item | Status |
|---|---|
| DÉLIA runtime (`delia-api`) | Bootstrap / separate product track |
| TÉO specialist descriptor consumed by DÉLIA | **PLANNED** |
| DÉLIA → Transformômetro DB | **FORBIDDEN** |
| DÉLIA → parallel process rules | **FORBIDDEN** |
| User delegation for specialist calls | **REQUIRED** when integration is built |

## Superseded directions

- Independent TÉO chat runtime / `POST …/teo/query`: **not present**; any historical proposal is superseded by this matrix + ADR `adr-teo-specialist-capability-surfaces.md`.
- Process Documentation “fora de escopo GPT/MCP/TÉO” in ADR V1: **superseded for surface exposure** — domain ADR semantics (doc ≠ ata) remain; exposure via catalog entity is now CURRENT.
