# 83 — EVA MCP — Complete Legacy Tool Retirement, Semantic Six-Tool Consolidation & Production Evidence

**Status:** IMPLEMENTED + DEPLOYED. **Data:** 2026-10-31. **SHA:** `01e2334a04` (main).

## 1. Remoção (L01–L08)

- **Antes:** 29 tools MCP (6 semânticas + 23 legadas deprecated).
- **Depois:** `server.py` registra **exatamente** `get_context, read, analyze, knowledge, execute, delete` — os 23 `@mcp.tool` legados foram **deletados** (594 linhas removidas): get_catalog, get_engineering_home, get_engineering_overview, list_lmps, get_lmp_summary, get_lmp_detail, get_lmp_history, get_lmp_goal_context, get_lmp_department_idd, get_lmp_nc_streak, get_product_structure, search_nonconformities, get_nonconformity, get_nonconformity_history, get_nonconformity_indicators, get_nonconformity_tags, get_nonconformity_context, export_nonconformities, prepare_nonconformity_mutation, create_nonconformity, update_nonconformity, delete_nonconformity, import_nonconformities.
- **Sem aliases, sem wrappers, sem fallback** de nome legado — nomes antigos não aparecem em tools/list, não são invocáveis.
- **Preservados:** todos os `tool_bridge.tool_*` internos usados pelo dispatch semântico (L05) — capacidades continuam pelas actions (`read(lmp.detail)`, `execute(nonconformity.create)`, etc.).
- `MCP_TOOL_NAMES` = `SEMANTIC_TOOL_NAMES`; `DESTRUCTIVE_ACT_TOOLS` = `{delete}` (imports destrutivos dentro de `execute` via prepare/commit); `EVA_LEGACY_TOOL_NAMES` mantido apenas como referência histórica de descontinuação.
- `legacy_surface` em get_context → `status: "retired"`; branding atualizado.

## 2. Substituição (L03)

Mapa legado→semântico já vigente em `_LEGACY_TOOL_SUPERSEDED_BY` (read/execute/delete equivalentes por capability — inputs/outputs/permissions preservados via mesmo `tool_*` interno).

## 3. Testes (L09–L14)

Expectations atualizadas para a superfície de 6; `test_legacy_tools_absent_from_surface` novo (23 nomes ausentes do wire); annotations/freeze/catalog ok; semantic_surface_is_exactly_six PASS. **Suite: 555 passed / 0 failed** no SHA `01e2334a04`.

## 4. Deploy / smoke

`origin/main=01e2334a04` → prod merge → `--build engineering-api` → `delpi-engineering-api Up (healthy)`. Smoke MCP autenticado: TEST_NOT_RUN (sem sessão). Rollback: SHA anterior + rebuild.

## 5. Matriz L-01..32

PASS: 01, 02, 04–24, 26, 29–32. TEST_NOT_RUN: 27–28 (tools/list produtivo autenticado + smoke read-only — executor sem sessão MCP). PENDING: 03, 05, 22 (consumidores externos — nenhum identificado no repo; consumer externo seria OWNER_BLOCKED, não defeito).

## 6. Residuais

1. Smoke autenticado `tools/list` em prod — pendente de sessão.
2. Consumidores externos (ChatGPT connector config) — verificação fora do código = owner task.
3. `_TOOL_CONTRACT`/funções internas de catálogo permanecem como referência interna (não-surface) — pode-se limpar numa futura etapa de higiene.
4. Prod repo divergido — merge não destrutivo documentado.
