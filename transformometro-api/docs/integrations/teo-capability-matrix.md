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

## Source of truth

| Concern | Canonical source |
|---|---|
| Domain rules | Transformômetro Application/Domain |
| Entity contracts | `entities.py` + `registration_guide.entity_schemas` |
| Capability metadata | `capability_descriptors` + catalog `capability_surface` |
| Agent intelligence | `teo_agent_intelligence.json` → `TeoAgentIntelligenceService.agent_directives(transport)` |
| Write execution policy | `application/governed_writes/confirmation_policy.py` `_WRITE_POLICIES` — ONE `WritePolicyRecord` per semantic capability; capability/workflow/entity-op names are aliases onto the same record (TEO-WRITE-POLICY-FINAL-DEDUPLICATION-05) |
| Transport parity map | `application/intelligence/capability_registry.py` `CAPABILITY_BINDINGS` (canonical; `interface/mcp/constants.py` derives) |
| Transport projection | `application/intelligence/transport_projection.py` + canonical projections in `capability_descriptors` (`neutralize_for_mcp` only for prose, fail-closed) |
| Actions surface | `openapi_builder.py` → generated OpenAPI (18 ops) |
| MCP surface | `constants.py` / `server.py` registration (24 tools) |
| AuthZ | Core RBAC + domain enforcement |
| GPT Instructions | `docs/gpt-actions/specialist-instructions.md` |
| Methodology | `teo-method-playbooks.md` + `query_methodology_guide` |
| Runtime status | deploy + acceptance evidence (not docs alone) |
| Capability matrix | **this file** |

## PREPARE / POLICY GATE / COMMIT (canonical flow)

Two distinct consumer contracts share the same governed-write engine
(`GovernedWriteOrchestrator`); they are separated at the adapter boundary.
The canonical write-execution policy
(`application/governed_writes/confirmation_policy.py`, sealed on every
proposal as `execution_policy`) classifies each material-write capability:

- `auto_act` — NON_DESTRUCTIVE writes (create/update/duplicate, append-only
  cost adjust, additive diagnostic create): execute directly after governed
  PREPARE. The direct user request is the intent — no conversational
  confirmation round-trip.
- `confirm_before_act` — DESTRUCTIVE/consequential writes (delete,
  activation/supersession, package commit, recalculate, workflow
  transitions, evidence manage, diagnostic manage): exactly ONE explicit
  user confirmation before ACT.

Each semantic write capability owns exactly ONE `WritePolicyRecord`
(`semantic_id`, `execution_policy`, `capability`, optional `workflow_id` /
`entity_operation` aliases). Capability names, workflow ids and entity
operations are indexes onto the same record — a policy change is a single
edit that propagates to the orchestrator seal, both catalog projections,
the Actions `commit_now` compat decision and MCP metadata.

```text
UNDERSTAND → READ CURRENT STATE → PREPARE EXACT CHANGE → VALIDATE → AUTHZ
→ WRITE EXECUTION POLICY GATE

AUTO_ACT:
    ACT → AUTHORITATIVE READ-BACK → VERIFY → REPORT

CONFIRM_BEFORE_ACT:
    SHOW EXACT DESTRUCTIVE CHANGE → ONE EXPLICIT CONFIRMATION
    → ACT → AUTHORITATIVE READ-BACK → VERIFY → REPORT
```

Transport mechanics (adapters only, never canonical policy):

```text
GPT Actions adapter:
  auto_act implemented via commit_now=true + confirmation +
  Idempotency-Key (atomic PREPARE+ACT) — a transport mechanism only.
  confirm_before_act → gpt_commit_proposal requires confirmation:true.

MCP adapter (pure PREPARE):
  prepare_* → proposal_handle + exact_change + execution_policy + expiry
  (persisted=false always; NEVER materializes business state)
  auto_act → commit_proposal in the same turn (no extra Confirma?)
  confirm_before_act → show change → Confirma? → commit_proposal
  ACT → fresh AuthZ → DOMAIN → SAVE → AUTHORITATIVE READ-BACK → VERIFY
```

- **MCP invariant (ARCH-DRIFT-TEO-MCP-PREPARE-ACT-CONTRACT-01):**
  `PREPARE != ACT`. MCP `prepare_*` tools are side-effect-free w.r.t.
  material business writes and expose NO `commit_now` / `confirmation` /
  `idempotency_key` fields — enforced by `tests/test_teo_mcp_prepare_contract.py`.
- `commit_now` exists ONLY in the GPT Actions additive contract; it is not
  reachable through the MCP surface.
- Capabilities `execution_policy=auto_act` (create/update/duplicate/
  cost-adjust/additive diagnostic): **não** pedir Confirma? no chat — o
  pedido direto do usuário é a intenção.
- Destructive (delete/activate/cancel/package/recalculate/evidence
  mutate/workflow/diagnostic manage): uma Confirma? → `gpt_commit_proposal`
  / `commit_proposal`.
- Explicit confirmation ≠ AuthZ (backend revalidates on commit); AUTO_ACT
  also never bypasses AuthZ/validation/audit/read-back/verify.
- Live mutation intelligence: `capability_surface.agent_directives` from
  `teo_agent_intelligence.json`.
- **Knowledge parity (ARCH-DRIFT-TEO-MCP-EXPERT-KNOWLEDGE-DELIVERY-02):**
  `get_catalog` serves one canonical intelligence on both transports via a
  per-transport projection. The Actions projection keeps `gpt_*` names and
  the additive `commit_now` policy; the MCP projection (`transport="mcp"`)
  derives every name from the canonical capability registry (unknown
  mappings fail closed), drops
  Actions-only sections (`write_flow`, `gpt_operations`, `*_actions`
  lists), ships `write_flow_mcp` instead, and contains zero `commit_now` /
  atomic prepare+commit semantics — enforced by
  `tests/test_teo_mcp_transport_projection.py`.
- Technical 2xx ≠ business outcome (need verified read-back).
- Proposal store: in-process, single-replica → **ACCEPT_WITH_RESIDUAL**.

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
| **Process Documentation** | PROVEN CRUD | **C `EXISTING_CATALOG_ENTITY`** `process_document` | `record_read` / `prepare_record_change` / `commit_proposal` | PLANNED | **FULL_PARITY** (Actions+MCP); DÉLIA PLANNED |
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
| Entity CRUD (17 legacy + process_document) | TM | R/W | record_read + prepare_record_change + commit_proposal | gpt_record_read + gpt_prepare_record_change + gpt_commit_proposal | PLANNED | per entity | FULL_PARITY* |
| Activate revision | TM | W | prepare_governed_operation(activate_revision) → commit_proposal | `gpt_prepare_governed_operation` + commit | PLANNED | revisao manage | FULL_PARITY* |
| Recalculate dashboard | TM | W | prepare_governed_operation(recalculate_dashboard) → commit_proposal | `gpt_prepare_governed_operation` + commit | PLANNED | dashboard | FULL_PARITY* |
| Improvement package | TM | W | prepare_governed_operation(commit_improvement_package) → commit_proposal | `gpt_prepare_governed_operation` + commit | PLANNED | package AuthZ | FULL_PARITY* |
| Evidence link/metadata | TM | R/W | evidence_read(list) + prepare_evidence_change → commit_proposal | `gpt_evidence_read` / `gpt_prepare_evidence_change` + commit | PLANNED | manage + confirm_delete | FULL_PARITY* |
| Process timeline | TM | R | `get_process_timeline` | `gpt_get_process_timeline` | PLANNED | view | FULL_PARITY* |
| Shared resource cost adjust | TM | W | prepare_governed_operation(adjust_shared_resource_cost) → commit_proposal | `gpt_prepare_governed_operation` + commit | PLANNED | parity | FULL_PARITY* |
| Meeting minute workflow/manage | TM | R/W | meeting_minute_read + prepare_meeting_minute_change → commit_proposal | `gpt_meeting_minute_read` / `gpt_prepare_meeting_minute_change` + commit | PLANNED | minutes svc | FULL_PARITY* |
| **Diagnostic V1** | TM | R/W | `diagnostic_read`(get\|by_revision) + `prepare_diagnostic_change`(create\|13 manage actions) → `commit_proposal` | — (MCP-native, no GPT ops) | PLANNED | `transformometro.access` + fresh Core AuthZ on ACT | **MCP_ONLY** |
| **Process documentation** | TM | R/W | via record tools | via record entity | PLANNED | `transformometro.access` | FULL_PARITY* |
| Tasks | TM | R/W | collaboration_read + prepare_collaboration_change → commit_proposal | `gpt_collaboration_read` / `gpt_prepare_collaboration_change` | PLANNED | access | FULL_PARITY* |
| Interaction room | TM | R/W | collaboration_read + prepare_collaboration_change → commit_proposal | `gpt_collaboration_read` / `gpt_prepare_collaboration_change` | PLANNED | access | FULL_PARITY* (binary attachments platform_blocked) |
| Helpdesk/GLPI demand | Helpdesk BFF | R/W | `helpdesk_read` (incl. `attachment` binary blocks) + `prepare_helpdesk_change` → `commit_proposal` | `gpt_helpdesk_read` / `gpt_prepare_helpdesk_change` + commit | PLANNED | `helpdesk.access` + GLPI session | FULL_PARITY* (R4.2: attachment read/upload proven live; GPT Actions = metadata + file object) |
| Legacy diagram → native BPMN migration | TM | W | prepare_governed_operation(migrate_legacy_diagram_to_native_bpmn) → commit_proposal | `gpt_prepare_governed_operation` + commit | PLANNED | processo manage | FULL_PARITY* |
| Process workspace UI | MFE | R | — | — | — | — | NOT_APPLICABLE |

\*FULL_PARITY = Actions + MCP mapped to same application services. DÉLIA consumption = **PLANNED / NOT_PROVEN** (no runtime adapter in `delia-api` at this HEAD).

## AuthZ parity

| Capability | MCP | Actions | DÉLIA | Canonical enforcement |
|---|---|---|---|---|
| Process document | User JWT → use case `require_access` | Same dispatch → use case | Must use user delegation when built | `ProcessDocumentUseCases` |
| Entity CRUD (other) | Same as GPT services | Same | PLANNED | Domain + branch_access helpers |
| Writes governed | PREPARE → commit_proposal; confirm flag required only for confirm_before_act | execution_policy gate + backend AuthZ | Must show + human confirm before destructive commit; auto_act direct | Orchestrator / services |
| MCP tool count | **22** (`CAPABILITY_GOVERNED_V2`) | — | — | constants.MCP_SURFACE_BUDGET |
| Explicit confirmation | `commit_proposal` requires `confirmation` only for `confirm_before_act` proposals (auto_act commits without it) | `gpt_commit_proposal` body `confirmation` default `false` (fail-closed for destructive) | Same contract | `GovernedActionsFacade.commit_proposal` policy gate on the sealed `execution_policy` |

Profile/cargo/department/context ≠ AuthZ. Service account must not impersonate user on MCP `/mcp`.

## PREPARE / COMMIT parity (writes)

| Capability | PREPARE | Confirm | COMMIT | Read-back | Surfaces |
|---|---|---|---|---|---|
| create/update/delete/duplicate record (incl. process_document) | MCP `prepare_record_change` | MCP proposal; Actions conversational | MCP/Actions `commit_proposal` | Yes | MCP + Actions |
| activate / package / evidence / cost / meeting | MCP specialized `prepare_*` | confirm_* where required | MCP/Actions `commit_proposal` | Yes | MCP + Actions |
| Tasks / Room | N/A | N/A | N/A | N/A | Not exposed |

## Portal × TÉO parity closure (capability accounting wave)

Every Portal capability is accounted in exactly one class via
`capability_descriptors.build_capability_surface_catalog().exposure_classification`:

```text
EXPOSED = 10 capability groups
PLATFORM_BLOCKED = 7 (binary transport: file upload/download, signature
    image, minute PDF, XLS/CSV/binary exports, .tmbackup.zip package)
TECHNICAL_ONLY = 4 (websocket/presence/locks/health plumbing)
PUBLIC_TOKEN_FLOW = 1 (external meeting-minute signer — never impersonated)
INTENTIONALLY_NOT_APPLICABLE = 4 (UI composition, json_backup bulk
    portability, other-person profile read, navigation helpers)
PARITY_GAP = 0 · TO_INVENTORY = 0 · UNCLASSIFIED = 0
TOTAL = 26 capability groups covering the full Portal route inventory
```

Newly exposed (no new MCP tools — typed actions/views on existing families):

| Intent | Family | Action/view | Owner | Policy |
|---|---|---|---|---|
| Dashboard live views (summary/ranking/alerts/evolution/family/due_dates/strategic/calculated) | `analyze` | 8 views | Dashboard*Service | READ |
| Revision comparison | `analyze` | `process_revision_comparison` | ProcessRevisionCompareService | READ |
| Impact/effort matrix | `analyze` | `impact_effort_matrix` | RevisaoImpactEffortMatrixService | READ |
| Decomposition link validation + draft suggestion | `analyze` | 2 views | DecompositionFlowchartLinkValidator / DecompositionDraftService | READ (no persistence) |
| Diagram validation + BPMN XML export | `analyze` | `diagram_validation`, `diagram_bpmn_xml` | FlowchartValidationService / FlowchartBpmnXmlService | READ |
| Revision merged views + rateio diagnostic | `analyze` | 3 views | Revisao*Merge/Diagnostic services | READ |
| Instance `contexto` | `prepare_record_change` + `record_read` | entity=`instance`, `changes.contexto` | validate_instancia_contexto_v1 + ProcessoInstanciaRepository | auto_act |
| Meeting-minute refuse | `prepare_meeting_minute_change` | `refuse` (reason required) | MeetingMinutesService.refuse | confirm_before_act |
| Signature profile | `get_my_context` (read, permission-gated, no binary) + `prepare_governed_operation` | `update_signature_profile` | UserSignatureService | auto_act |
| BPMN XML import | `prepare_governed_operation` | `import_diagram_bpmn_xml` | FlowchartBpmnXmlService + DiagramWriteService | confirm_before_act |
| Process-file metadata | `evidence_read`/`prepare_evidence_change` | scope=`process` | ProcessoArquivoRepository | per action |

Reclassified: `process_file.metadata_write` (already covered by
`manage_evidence(scope=process)` — same repo, manage AuthZ, audit, read-back);
`bpmn_xml` moved from binary-blocked to text capability (`{xml: str}`);
`meeting_minute.sign` stays excluded (UploadFile signature image + terms =
binary attestation; authenticated `sign` never exposed, public token flow
separate); `json_backup` stays INTENTIONALLY_NOT_APPLICABLE (bulk DB
portability bundle, not a conversational payload); binary stays
PLATFORM_BLOCKED.

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
