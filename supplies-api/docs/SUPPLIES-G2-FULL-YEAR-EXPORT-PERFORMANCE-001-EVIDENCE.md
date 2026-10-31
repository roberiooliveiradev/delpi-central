# SUPPLIES-G2-FULL-YEAR-EXPORT-PERFORMANCE-001 — EVIDENCE

Data: 2026-10-31 · TASK: `SUPPLIES-G2-FULL-YEAR-EXPORT-PERFORMANCE-001`
Objetivo: resolver o timeout da exportação anual de SC preservando
completude e paridade Portal ↔ SURI.

## P0–P1 — Rebaseline e inventário

```text
BASE HEAD: origin/main avançou durante a sessão (worktree isolada /tmp/exp-wt)
Cadeia confirmada: Portal/SURI → supplies-api → purchase-requests-api
  → api-delpi /supplies/purchase-requests/lines/export → TOTVS (SC1/SC7/SD1)
Budgets pré-fix já alinhados (300s) pelo commit b12524a73a;
gargalo remanescente era custo interno, não orçamento.
```

## P2 — Perfil SQL (medido em produção, api-delpi)

```text
BASE_SQL (SC1, filtros branch+ano):   0.2s   — NÃO era o gargalo
NORMALIZE (5445 linhas):              0.2s
ATTACH ORDERS (SC7, 10 batches OR-keys): 62.8s (≈6.3s por batch)
ATTACH RECEIPTS (SD1, 18 batches):       95.2s (≈5.3s por batch)
TOTAL:                                158.6s → 168.4s end-to-end
BOTTLENECK: execução SERIAL das ~28 batches independentes de
  enriquecimento (orders/receipts) — não a query base, não N+1,
  não serialização, não índice.
```

## P3 — Implementação (menor diff, owner api-delpi)

`purchase_request_lines_repository.py`:
- `_fetch_key_batches()` — fan-out limitado (`_ATTACH_BATCH_MAX_WORKERS=4`,
  bem abaixo do TOTVS_POOL_MAX_SIZE=10) sobre as batches OR-key.
- Cada worker usa `type(self)()` → conexão própria do pool (cursor/conn
  de `self` não são thread-safe). `executor.map` preserva ordem de batch
  (determinístico). Single-batch → caminho serial sem thread.
- SQL idêntica, mesmos resultados, sem TOP/truncamento/contrato novo.

Teste novo: `tests/test_purchase_request_lines_repository.py` (3 casos —
completude por batch, ordem determinística, caminho serial single-batch,
fan-out real medido). Commit `8a24b50181`.

## P4–P5 — Benchmark e decisão

```text
export_lines branch=01 ano inteiro:
  BEFORE: 158.6s (medido) / 168.4s (histórico HTTP interno)
  AFTER:   58.0s          — 2.7× mais rápido, ROWS=5445 completas
Sem necessidade de alternativa arquitetural (P5 não acionado):
  solução síncrona cabe no orçamento do edge com folga.
```

## P6 — Testes e segurança

```text
api-delpi unit: 3/3 novos PASS (container produtivo, imagem nova)
Invariantes: capability + unit_scope + resource_scope + business_rule
  preservados — mudança puramente concorrente, zero semântica.
Portal_global por unidade intocado; nenhuma permission criada.
```

## P7–P8 — Commit e deploy

```text
COMMITS: 8a24b50181 (perf api-delpi + teste)
DEPLOY:  rebuild infra-api-delpi → recreate apenas delpi-api-delpi
OLD_IMAGE: e58d996e4b78 (tag rollback: infra-api-delpi:pre-export-perf-rollback)
NEW_IMAGE: 4af8fe187cf1 — container healthy, restart limpo
Serviços não tocados: supplies-api/mcp, PR-api, core, keycloak, gateway.
```

## P9 — Homologação produtiva (identidade user-delegated real)

```text
FULL-YEAR branch=01 (2026-01-01→2026-12-31):
  PORTAL_EXPORT: 200 · 52.3s · 5445 linhas CSV
  SURI_EXPORT:   200 · 65.6s · export={format:json,row_count:5445,
                 portal_file_formats:[csv,xlsx]} · ~24MB streamed
  DATASET_COMPLETE = TRUE · NO_TIMEOUT · NO_TRUNCATION · AUTHZ PASS
  UNIT_SCOPE = PASS (filial 01 fixada)
Regressão: PO_SEARCH 200 success=true total=343 · SC calls 200
  streaming ok · supplies-mcp/supplies-api/PR-api/api-delpi healthy
MCP: CATALOG_VERSION=5 · TOOL_COUNT=5
```

## P10 — Estado final

```text
FULL_YEAR_EXPORT_ROOT_CAUSE = PROVEN (attach batches serializadas)
SQL_PERFORMANCE            = IMPROVED (58s upstream / ~52–66s público)
DATASET_COMPLETENESS       = PASS (5445 linhas, row_count match)
PORTAL_FULL_YEAR_EXPORT    = PASS
SURI_FULL_YEAR_EXPORT      = PASS
G2_FINAL_GATE              = READY_FOR_REVIEW

FACTS_PROVEN: gargalo real = serialização das batches SC7/SD1;
  fan-out limitado resolve dentro do edge budget (~125s) com margem;
  dataset integral preservado; paridade Portal↔SURI mantida.
TO_INVENTORY: se o volume anual crescer >2×, reavaliar custo por batch
  (possível tuning de _line_keys_or_clause) ou worker count.
EXECUTION_DRIFT: nenhum nesta missão (Cloudflare permanece constraint
  conhecido: ~125s; custo atual ~60s com folga ~2×).
RESIDUAL: nenhum funcional.
NEXT_STEP: G2 pode ser marcado CLOSED pelo GPT Arquiteto; G3 aguarda.
```
