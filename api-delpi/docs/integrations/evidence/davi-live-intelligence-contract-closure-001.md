# DAVI-LIVE-INTELLIGENCE-CONTRACT-CLOSURE-001

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`  
**Task type:** CONTRACT CLOSURE / AUDIT + ADDITIVE SCHEMA CORRECTION  
**Implementation authorized scope:** schema + tests + minimal intelligence wording + docs/evidence  
**New capability authorized:** `NO`

## Bootstrap

| Field | Value |
|---|---|
| BOOTSTRAP MAIN (external) | `54e5f0f48ad5f46fcb4c8c4582459d49c5cf3ea8` |
| Intelligence commit | `de3e7c75089a4dcffa49ea47a4140bd9b0cabdd4` |
| BASE HEAD / origin/main | `54e5f0f48ad5f46fcb4c8c4582459d49c5cf3ea8` |
| EXECUTION_DRIFT (premissas) | **NO** for allowlist/tools/spike; **YES** for discover outputSchema vs runtime |

## Verdict

**PASS_WITH_RESIDUAL**

Contract drift resolved in source. Agent Studio sync and fresh LIVE provider PASS remain residual.

## Source of truth matrix

| Concept | Owner |
|---|---|
| DAVI mission/architecture | `docs/12-roadmap-e-evolucao/davi/README.md` |
| agent_directives content | `api-delpi/app/content/davi_agent_intelligence.json` |
| agent_directives producer | `DaviAgentIntelligenceService` |
| MCP discover/execute schema | `api-delpi/app/interface/mcp/schemas.py` |
| allowlist eligibility | `davi_external_read_allowlist.json` (v9) |
| business AuthZ | canonical backend (api-delpi / Core) |
| Product/drawing PDF storage | api-delpi DrawingPdfLibraryStorage / FILESERVER |
| Agent Studio config | manual provider UI (`openai-workspace-agent-davi.md`) |
| document transport | PENDING / Outcome F / NOT_PROVEN |

## Discover contract drift (PROVEN → RESOLVED)

| Check | Before | After |
|---|---|---|
| Runtime has `capability_surface` | YES | YES |
| Declared `DiscoverDelpiInformationOutput` | NO (`extra=forbid`) | YES (`CapabilitySurfaceOutput`) |
| tools/list `outputSchema` | omitted | includes `capability_surface` |
| Validate structuredContent vs model | FAIL (`extra_forbidden`) | PASS |
| Classification | `DAVI_DISCOVER_OUTPUT_SCHEMA = EXECUTION_DRIFT` | ADDITIVE_CONTRACT_CORRECTION |

Top-level fields after correction:

`query`, `top_k`, `candidate_count`, `eligible_action_count`, `candidates`, `capability_surface`

Nested `agent_directives` remains dynamic mapping (no second copy of JSON fields in Pydantic).

## Agent intelligence

| Field | Value |
|---|---|
| Version | `2026.09.24.2` |
| Bytes (serialized directives) | ~5 KiB (well under `DAVI_AGENT_DIRECTIVES_MAX_BYTES` = 16384) |
| Consumers | `gpt_get_catalog`, `discover_delpi_information` |
| GPT legacy ops | 2 (`LEGACY_TRANSITIONAL`) |
| Misleading GPT execute guidance | mitigated via `surface_parity.note` + flow `gpt_operations` lists |
| Authority wording | clarifies NOT AuthZ/OAuth/RBAC/domain truth |

## Budgets

Empty discover payload ~5.2 KiB with ~97% directives (expected when `candidates=[]`). No redesign: comfortably under 16 KiB local contract; ownership remains intelligence service (sibling to VISTA pattern). Dynamic-read budgets unchanged.

## Security / read-only

No `write_flow` / `commit_now` / PREPARE/ACT / free operationId / PDF JSON. Write-intent query → `candidate_count=0` with `read_only=true`. Spike default OFF → 3 tools / 0 resources.

## Agent Studio

```text
AGENT_STUDIO_SYNC = PENDING_MANUAL_SYNC
AGENT_STUDIO_PREVIEW_AFTER_SYNC = TEST_NOT_RUN
AGENT_INSTRUCTIONS_CHANGE = YES (AuthZ boundary clarification in stable contract)
PROVIDER_REDISCOVERY = RECOMMENDED_AFTER_DEPLOY
```

Manual handoff: replace Agent Studio Instructions from `openai-workspace-agent-davi.md` canonical block; save draft; keep End-user account; rediscover MCP tools after deploy; run preview scenarios A–G; do not mark LIVE PASS from this evidence alone.

## External observed evidence input (Architecture)

Recorded as EXTERNAL_PREVIOUS_EVIDENCE only (not Cursor LIVE PASS): eligible_action_count=17; directives version observed as 2026.09.24.1 before this bump; stock discover→execute path reported ok. Fresh LIVE after this HEAD = TEST_NOT_RUN.

## Tests

Focused: `test_davi_agent_intelligence.py` (+ siblings listed in report) — **93 passed**.

## Gaps

- Authenticated LIVE provider rediscovery/preview after deploy
- Agent Studio manual sync
- Homolog MCP / document transport LEVEL 5 still blocked
