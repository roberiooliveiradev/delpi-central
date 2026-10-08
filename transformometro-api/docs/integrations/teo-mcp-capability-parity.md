# TÉO MCP — Capability parity matrix (write-governance remediation)

> **Canonical multi-surface matrix (Actions + MCP + DÉLIA + budget):**  
> [`teo-capability-matrix.md`](./teo-capability-matrix.md)

Gate (MCP Surface V2 — HEAD capability-driven):

```text
CURRENT_CAPABILITIES (GPT Actions importable) = 20 (family operations)
MCP_COVERED = 20
MCP_NATIVE = diagnostic_v1 (2 family tools)
MCP_TOOLS = 22
MISSING = 0
UNMAPPED GPT = 0
REGRESSED = 0
ENTITY_CATALOG includes process_document (no new MCP entity tools)
TEO_MCP_SURFACE = CAPABILITY_GOVERNED_V2
```

```text
20 GPT Actions capabilities (semantic families)
≠
22 MCP tools
```

Tool Surface Rationalization V1: transports expose **semantic families with
closed `action` enums**, not one tool per route. One GPT capability may map
to READ + PREPARE family operations; all governed writes share
`commit_proposal`. `gpt_get_methodology_guide` and `get_methodology_guide`
share `query_methodology_guide`. Diagnostic V1 (`diagnostic_v1`) is MCP-native —
`diagnostic_read` (get|by_revision) + `prepare_diagnostic_change` (create|13
manage actions) — with no GPT Actions surface.

Composition:

```text
14 READ + 1 DISCOVERY + 6 PREPARE + 1 ACT(commit) = 22
READ includes analyze + get_methodology_guide + collaboration_read +
evidence_read + meeting_minute_read + diagnostic_read + helpdesk_read
PREPARE = prepare_record_change + 5 family prepares
  (governed_operation / evidence / meeting_minute / collaboration / diagnostic)
ACT = commit_proposal only (opaque proposal_handle; capability from store)
commit_proposal schema: proposal_handle and confirmation are BOTH required;
confirmation has NO default — omitted confirmation never means confirmed.
For proposals sealed with execution_policy=auto_act, confirmation is a
protocol assertion of the already-expressed user intent (no extra
conversational gate); confirm_before_act proposals require confirmation=true.
unbound ACT = 0

PREPARE purity (ARCH-DRIFT-TEO-MCP-PREPARE-ACT-CONTRACT-01):
- MCP prepare_* inputSchema exposes NO ACT-collapse controls
  (commit_now / confirmation / idempotency_key absent — enforced by
  tests/test_teo_mcp_prepare_contract.py).
- MCP PREPARE is side-effect-free w.r.t. material business writes:
  orchestrator.act call count = 0 on every prepare_* invocation.
- Material execution occurs ONLY through ACT-class commit_proposal after
  consumer governance per execution_policy.
- GPT Actions has a DISTINCT additive commit_now contract (policy-allowed
  capabilities, confirmation + Idempotency-Key required) — that contract is
  NOT part of the MCP PREPARE surface and cannot be reached through it.
GPT importable operations = 20
meta route gpt_get_openapi_schema is not importable

Knowledge/intelligence parity (ARCH-DRIFT-TEO-MCP-EXPERT-KNOWLEDGE-DELIVERY-02):
- get_catalog serves ONE canonical capability/intelligence source on both
  transports; the canonical surface is transport-neutral; per-transport projections
  derive from tm_app/application/intelligence/capability_registry.py
  (+ transport_projection.py for residual prose).
- MCP get_catalog: only MCP-callable names (prepare_*/commit_proposal),
  write_flow_mcp envelope, parity-neutral surface_version
  (teo-capabilities-v3), zero commit_now / gpt_* — enforced by
  tests/test_teo_mcp_transport_projection.py.
- Actions gpt_get_catalog: unchanged gpt_* operationIds + additive
  commit_now policy + canonical surface_parity.parity_map.
- Canonical parity record (TEO-UNIFIED-BOUNDARY-FINAL-CORRECTION-03):
  tm_app/application/intelligence/capability_registry.py — ONE binding
  table owns capability ids, Actions operationIds, MCP tool names,
  classes and explicit 1→N primary tools. interface/mcp/constants.py
  derives GPT_TO_MCP_TOOLS / TOOL_CLASS / MCP_NATIVE_TOOLS from it
  (adapter depends inward; application never imports interface.mcp).
  Unknown mappings fail closed via ProjectionContractError; MCP PREPARE
  reporting persisted=true now raises prepare_persisted_state_violation
  instead of reporting success (tests/test_teo_capability_boundary.py).
```

## Surface budget

| | Before (V1) | After (V2) | After Rationalization V1 | After Helpdesk V1 |
|---|---|---|---|---|
| Total | 33 | 20→24→28 | 21 | **22** |
| READ | 10 | 10 | 13 (+1 DISCOVERY-classified `get_catalog`) | 14 |
| PREPARE | 11 | 8 | 6 (family prepares) | 6 |
| ACT | 11 | 1 | 1 | 1 |

Principle: new CRUD entity ⇒ **0** new MCP tools; new capability ⇒ a typed
`action` in an existing semantic family by default; a new tool only by
exception with a real business boundary; no automatic new ACT.

## Mapping highlights

| GPT Action | Kind | MCP | AuthZ | Read-back | Status |
|---|---|---|---|---|---|
| `gpt_prepare_record_change` | PREPARE ENTITY | `prepare_record_change` | entity manage | on commit | OK |
| `gpt_commit_proposal` | COMMIT | `commit_proposal` | revalidated | authoritative | OK |
| `gpt_record_read` | READ | `record_read` | view + resource | n/a | OK |
| `gpt_prepare_governed_operation` | PREPARE WORKFLOW | `prepare_governed_operation` → `commit_proposal` | per capability | yes | OK |
| `gpt_evidence_read` / `gpt_prepare_evidence_change` | READ/PREPARE | `evidence_read` / `prepare_evidence_change` | manage + confirm_delete | yes | OK |
| `gpt_meeting_minute_read` / `gpt_prepare_meeting_minute_change` | READ/PREPARE | `meeting_minute_read` / `prepare_meeting_minute_change` | minutes svc | yes | OK |
| `gpt_collaboration_read` / `gpt_prepare_collaboration_change` | READ/PREPARE | `collaboration_read` / `prepare_collaboration_change` | tasks/rooms access | yes | OK |
| `gpt_helpdesk_read` | READ | `helpdesk_read` | `helpdesk.access` + GLPI session (BFF-owned) | n/a | OK |
| — (MCP-native) | READ | `diagnostic_read` | `transformometro.access` | n/a | OK |
| — (MCP-native) | PREPARE | `prepare_diagnostic_change` → `commit_proposal` | fresh Core AuthZ on ACT | authoritative | OK |

## Removed from registration (V1 mechanical pairs + Rationalization V1 tombstones)

`prepare_create/update/delete/duplicate_record`, all `act_*` tools, plus the
pre-family names `task_read`, `prepare_task`, `interaction_room_read`,
`prepare_interaction_room`, `list_evidence`, `prepare_manage_evidence`,
`generate_from_transcript`, `prepare_meeting_minute_workflow`,
`prepare_meeting_minute_manage`, `get_diagnostic`,
`list_diagnostics_by_revision`, `prepare_create_diagnostic`,
`prepare_manage_diagnostic`, `prepare_activate_revision`,
`prepare_recalculate_dashboard`, `prepare_improvement_package`,
`prepare_adjust_shared_resource_cost`.
Bridge wrappers remain for internal callers/tests only — **not**
discoverable via `tools/list`.

## Forbidden residuals

Generic proxy / `execute_capability` / `invoke_tool` / SQL / arbitrary table / service-account impersonation = **NONE**.
