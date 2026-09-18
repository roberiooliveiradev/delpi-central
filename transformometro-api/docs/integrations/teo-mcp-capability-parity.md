# TÉO MCP — Capability parity matrix (write-governance remediation)

Gate:

```text
CURRENT_CAPABILITIES (GPT Actions importable) = 21
MCP_COVERED = 21
MCP_NATIVE = none
MCP_TOOLS = 33
MISSING = 0
UNMAPPED GPT = 0
REGRESSED = 0
```

```text
21 GPT Actions capabilities
≠
33 MCP tools
```

One GPT capability may map to READ + PREPARE + ACT semantic tools.
`gpt_get_methodology_guide` and `get_methodology_guide` share `query_methodology_guide`.
`21 ≠ 33` is not a regression.

Composition:

```text
10 READ + 1 ANALYSIS + 11 PREPARE + 11 ACT = 33
READ includes get_methodology_guide
ACT tools accept only proposal_handle
unbound ACT = 0
GPT importable operations = 21
meta route gpt_get_openapi_schema is not importable
```

Source of truth: `tm_app/interface/mcp/constants.py` (`GPT_TO_MCP_TOOLS`).

| GPT Action (operationId) | Capability | MCP tool(s) | AuthZ (canonical) | Postcondition | Parity |
|---|---|---|---|---|---|
| `gpt_get_my_context` | READ | `get_my_context` | AuthN | N/A | OK |
| `gpt_get_catalog` | READ | `get_catalog` | view | N/A | OK |
| `gpt_get_methodology_guide` | READ guidance | `get_methodology_guide` | view (guide is not AuthZ) | N/A — no write | OK |
| `gpt_get_process_context` | READ | `get_process_context` | view/process | N/A | OK |
| `gpt_analyze` | READ | `analyze` | dashboard view | N/A | OK |
| `gpt_search_records` | READ | `search_records` | capability+view | N/A | OK |
| `gpt_get_record` | READ | `get_record` | capability+view | N/A | OK |
| `gpt_create_record` | WRITE | `prepare_create_record` → `act_create_record` | create + entity manage/admin | re-read created | OK |
| `gpt_update_record` | WRITE | `prepare_update_record` → `act_update_record` | update + manage | re-read updated | OK |
| `gpt_delete_record` | WRITE | `prepare_delete_record` → `act_delete_record` | delete + manage | soft-delete/absent | OK |
| `gpt_duplicate_record` | WRITE | `prepare_duplicate_record` → `act_duplicate_record` | duplicate + manage | re-read duplicate | OK |
| `gpt_activate_revision` | WRITE | `prepare_activate_revision` → `act_activate_revision` | `_require_revisao_manage_access` | re-read revision | OK |
| `gpt_recalculate_dashboard` | WRITE | `prepare_recalculate_dashboard` → `act_recalculate_dashboard` | `_require_dashboard_recalculate_access` | `mode` present | OK |
| `gpt_meeting_minute_workflow` | WRITE | `prepare_meeting_minute_workflow` → `act_meeting_minute_workflow` | MeetingMinutesService | re-read minute | OK |
| `gpt_validate_improvement_package` | PREPARE | `prepare_improvement_package` | view + validate + preflight | ready/missing; proposal | OK |
| `gpt_commit_improvement_package` | WRITE | `act_commit_improvement_package` | bound proposal + write AuthZ | re-read process/instance ids | OK |
| `gpt_list_evidence` | READ | `list_evidence` | view | N/A | OK |
| `gpt_manage_evidence` | WRITE | `prepare_manage_evidence` → `act_manage_evidence` | manage + confirm_delete | `verified` | OK |
| `gpt_get_process_timeline` | READ | `get_process_timeline` | view | N/A | OK |
| `gpt_adjust_shared_resource_cost` | WRITE | `prepare_adjust_shared_resource_cost` → `act_adjust_shared_resource_cost` | parity AuthZ | `verified` | OK |
| `gpt_meeting_minute_manage` | MIXED | `meeting_minute_read` + `generate_from_transcript` + `prepare_meeting_minute_manage` → `act_meeting_minute_manage` | per action | re-read when applicable | OK |

## Annotation decisions

| Class | readOnlyHint | destructiveHint |
|---|---|---|
| READ / ANALYSIS | true | false |
| PREPARE | false | false |
| ACT delete / evidence / activate / workflow / package commit / meeting manage | false | **true** |
| ACT create / update / duplicate / recalculate / cost | false | false |

`generate_from_transcript` is ANALYSIS (no persistence) — not ACT solely because it lived under a mixed GPT tool.

## Proposal mechanism

- Opaque HMAC `proposal_handle` (server-side store)
- Actor binding + capability binding + state fingerprint + expiration + expected postcondition
- TTL default ≈ 15m; consumed after successful ACT (replay → stale/not found)
- ACT accepts **only** `proposal_handle` (exact prepared change)
- ACT revalidates AuthZ + fingerprint → exact change → authoritative read-back
- Failed read-back → `OUTCOME_VERIFICATION_FAILED`

| Runtime | Status |
|---|---|
| Proposal store | in-process |
| Prod replicas | 1 |
| Single-replica operation | **ACCEPTED_WITH_RESIDUAL** |
| Shared store for horizontal scale | **TARGET** (not implemented) |

GPT Actions HTTP façade remains unbound by proposal handles (**LEGACY_TRANSITIONAL_BRIDGE**, 21 importable operationIds) but shares AuthZ/services with MCP ACT execution. Methodology uses the same `query_methodology_guide` on both surfaces.

## Live ChatGPT acceptance (2026-09-17)

| Layer | Status |
|---|---|
| Capability coverage (matrix) | 20/20 |
| Provider tool discovery | 32/32 PASS on 2026-09-17; expected after this change = **33**. ChatGPT refresh of the published app = **TEST_NOT_RUN** |
| READ (`get_my_context`, `get_catalog`, `search_records`) | PASS |
| PREPARE via ChatGPT | **TEST_NOT_RUN** |
| ACT / WRITE BUSINESS OUTCOME | **TEST_NOT_RUN** |

Do not promote PREPARE/ACT to PROVEN from code-only or READ-only smoke.
