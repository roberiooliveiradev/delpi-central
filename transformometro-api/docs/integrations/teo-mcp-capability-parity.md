# TÉO MCP — Capability parity matrix (write-governance remediation)

> **Canonical multi-surface matrix (Actions + MCP + DÉLIA + budget):**  
> [`teo-capability-matrix.md`](./teo-capability-matrix.md)

Gate (MCP Surface V2 — HEAD capability-driven):

```text
CURRENT_CAPABILITIES (GPT Actions importable) = 18
MCP_COVERED = 18
MCP_NATIVE = diagnostic_v1 (4 tools)
MCP_TOOLS = 24
MISSING = 0
UNMAPPED GPT = 0
REGRESSED = 0
ENTITY_CATALOG includes process_document (no new MCP entity tools)
TEO_MCP_SURFACE = CAPABILITY_GOVERNED_V2
```

```text
18 GPT Actions capabilities
≠
24 MCP tools
```

One GPT capability may map to READ + specialized PREPARE; all governed writes share `commit_proposal`.
`gpt_get_methodology_guide` and `get_methodology_guide` share `query_methodology_guide`.
`18 ≠ 24` is not a regression: meeting manage projects to multiple tools **and** Diagnostic V1
(`diagnostic_v1`) is MCP-native — `get_diagnostic`, `list_diagnostics_by_revision`,
`prepare_create_diagnostic`, `prepare_manage_diagnostic` — with no GPT Actions surface.

Composition:

```text
12 READ + 1 ANALYSIS + 10 PREPARE + 1 ACT(commit) = 24
READ includes get_methodology_guide + 2 Diagnostic reads
PREPARE includes prepare_record_change + specialized workflow prepares + 2 Diagnostic prepares
ACT = commit_proposal only (opaque proposal_handle; capability from store)
commit_proposal schema: proposal_handle and confirmation are BOTH required;
confirmation has NO default — omitted confirmation never means confirmed.
unbound ACT = 0
GPT importable operations = 18
meta route gpt_get_openapi_schema is not importable
```

## Surface budget

| | Before (V1) | After (V2) |
|---|---|---|
| Total | 33 | 20 |
| READ | 10 | 10 |
| ANALYSIS | 1 | 1 |
| PREPARE | 11 | 8 |
| ACT | 11 | 1 |

Principle: new CRUD entity ⇒ **0** new MCP tools; new workflow ⇒ specialized PREPARE only by default; no automatic new ACT.

## Mapping highlights

| GPT Action | Kind | MCP | AuthZ | Read-back | Status |
|---|---|---|---|---|---|
| `gpt_prepare_record_change` | PREPARE ENTITY | `prepare_record_change` | entity manage | on commit | OK |
| `gpt_commit_proposal` | COMMIT | `commit_proposal` | revalidated | authoritative | OK |
| `gpt_search_records` / `gpt_get_record` | READ | same names | view + resource | n/a | OK |
| `gpt_activate_revision` | PREPARE WORKFLOW | `prepare_activate_revision` → `commit_proposal` | revisao manage | yes | OK |
| `gpt_validate_improvement_package` | PREPARE WORKFLOW | `prepare_improvement_package` → `commit_proposal` | package | yes | OK |
| `gpt_manage_evidence` | PREPARE WORKFLOW | `prepare_manage_evidence` → `commit_proposal` | manage + confirm | yes | OK |
| — (MCP-native) | READ | `get_diagnostic` / `list_diagnostics_by_revision` | `transformometro.access` | n/a | OK |
| — (MCP-native) | PREPARE | `prepare_create_diagnostic` / `prepare_manage_diagnostic` → `commit_proposal` | fresh Core AuthZ on ACT | authoritative | OK |

## Removed from registration (V1 mechanical pairs)

`prepare_create/update/delete/duplicate_record`, all `act_*` tools.
Bridge wrappers remain for unit tests only — **not** discoverable via `tools/list`.

## Forbidden residuals

Generic proxy / `execute_capability` / `invoke_tool` / SQL / arbitrary table / service-account impersonation = **NONE**.
