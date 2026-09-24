# DAVI MCP Tool Surface Simplification

**TASK_ID:** `DAVI-MCP-TOOL-SURFACE-SIMPLIFICATION-001`  
**STATUS (source):** PASS  
**STATUS (deploy/live):** filled after push  

## Decision

Intentional breaking provider surface contraction:

| Before | After |
|---|---|
| 3 MCP tools | **2 MCP tools** |
| `search_products` dedicated MCP tool | **REMOVED** |
| Product Master capability `search_products` | **PRESERVED** behind discover→execute |

## Bootstrap

| Field | Value |
|---|---|
| Last externally revalidated | `a732beb14bbfc134dba1aecfc460a39b8b6837a7` |
| Bootstrap HEAD | `854338bba835463435dd167180de5aafcffa6b3b` |
| Ancestry of a732beb | CONFIRMED |
| Post-a732beb commits | VISTA/TV only (non-MCP) |

## Invariants

| Metric | Before | After |
|---|---|---|
| Eligible READ | 53 | 53 |
| Allowlist version | 14 | 14 (unchanged) |
| MCP tools | 3 | 2 |
| Agent intelligence | 2026.09.24.2 | **2026.09.24.3** |
| AuthZ / Keycloak / GPT Actions | unchanged | unchanged |

## Implementation

- Removed dedicated `@mcp.tool search_products` registration and list/call special cases from `server.py`.
- Renamed OAuth schemes to `DAVI_MCP_SECURITY_SCHEMES` (alias retained).
- Updated `davi_agent_intelligence.json`, branding, plugin skill, canonical docs.
- Preserved `SearchProductsInput/Output` schemas (capability I/O; still used by tests/projection contract).
- Preserved `SEARCH_PRODUCTS_OPERATION_ID` / `MCP_TOOL_SEARCH_PRODUCTS` string as operationId alias.

## Tests

Dedicated suite: `tests/test_davi_mcp_tool_surface_simplification.py`  
Plus MCP/oauth/spike/intelligence/wave004/005/drawing/real-user/dynamic_read — **PASS**.

## Known pre-existing residual (not introduced here)

Wave 001/002 ambiguous queries such as bare `produto 10080055` can tie-break to `get_product_production_status` under current retrieval (confirmed on clean `origin/main` before this task).

## Next

Deploy api-delpi → live tools/list = 2 → provider rediscovery PENDING_MANUAL → Wave 006.
