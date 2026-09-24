# E4 Contract freeze — TV-DASHBOARD-PRESENTATION-001

**Status:** FROZEN  
**ADR:** `docs/architecture/adr-tv-full-presentation-authority.md`  
**Catalog version:** `2026.09.24.presentation-authority`

## OWNER / CONSUMERS

| Contract | Owner | Consumers |
|---|---|---|
| TvPresentationPatchV1 | `presentation_mutation/patch_service.py` | VISTA GPT Actions, editor `POST …/presentation-mutations` |
| Ops catalog | `presentation_ops_content.json` | validator, planner, GPT OpenAPI |
| Persist | `TvPresentationWriteService` | commit service, CRUD slides |
| MFE client | `presentationMutationClient.ts` | editor blocks hook |

## ADDITIVE ops

- `create_block`
- `align_blocks`
- `reorder_block_z`
- `duplicate_blocks`

## REQUEST / RESPONSE (editor)

`POST /playlists/{playlistId}/slides/{slideId}/presentation-mutations`

```json
{ "ops": [ { "op": "create_block", "type": "chart_view", "chartType": "line" } ] }
```

Response data: `slide`, `nativeConfig`, `appliedOps`, `fingerprint`, `persisted: true`, `executionMode: editor_mutation_commit`.

## COMPAT

| Change | Class |
|---|---|
| New ops + defaults keys | ADDITIVE |
| New HTTP route | ADDITIVE |
| Existing upsert deep-merge | NONE |

## Abstraction Gate

PASS — extends PresentationMutation only.

## Concurrency

Editor mutations honor `If-Match` / playlist revision via WriteService.
