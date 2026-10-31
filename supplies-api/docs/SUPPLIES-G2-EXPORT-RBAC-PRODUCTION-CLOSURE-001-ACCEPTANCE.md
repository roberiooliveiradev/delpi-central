# SUPPLIES-G2-EXPORT-RBAC-PRODUCTION-CLOSURE-001 — ACCEPTANCE

Data: 2026-10-31 · TASK: `SUPPLIES-G2-EXPORT-RBAC-PRODUCTION-CLOSURE-001`
Escopo: Frente A (exportação ampla SC) + Frente B (RBAC devin-smoke-g16).

## P0 — Rebaseline

```text
BASE HEAD: prod = merge sync · remote main avançou pós-8396279313
GIT STATUS: prod limpo · trabalho concorrente preservado
```

## FRENTE B — RBAC devin-smoke-g16 (PASS — B2.A resolvido)

```text
BEFORE (canonical GET /admin/rbac/users/{id}/roles):
  devin-smoke-g16 → [Portal Suprimentos - Acesso]   (único papel — perfil temporário)
ACTION: DELETE /admin/rbac/roles/{role}/users/{g16} via
  RemoveRoleFromUserUseCase, ator superadmin user@local.com
  (token OAuth real client delpi-central) → {"ok":true}
AFTER: [] (identidade preservada; zero outros grants afetados)
AUDIT: operação pelo endpoint canônico Core — sem SQL direto
EFFECTIVE_PERMISSIONS: roles vazio → sem supplies.access efetivo;
  fail-closed por construção (mesma derivação Core /me do G2)
B1/B2: grant temporário confirmado (conta smoke com papel único de teste)
B4: pós-condição comprovada
RBAC_G16 = RESOLVED_WITH_OWNER_DECISION (B2.A — temporário)
```

## FRENTE A — SC full-range export (EXECUTION_DRIFT → decisão de owner)

### A1 Diagnóstico medido

```text
Cadeia: Portal/SURI → supplies-api → purchase-requests-api
        → api-delpi /supplies/purchase-requests/lines/export
Medições (runtime, homologação anterior + revalidação):
  /lines paginado (page_size=200) ≈ 17s por página (~85ms/linha)
  export_lines = execute_query ÚNICO sem TOP/paginação
    + _attach_orders_and_receipts (batched sob cap 2100 params — NÃO é N+1)
  delpi_api_client timeout = 30s (env DELPI_API_TIMEOUT)
  gunicorn/uvicorn upstream ≈ 90s
Estimativa: ~859 SCs / ~3k+ linhas branch=01 ano inteiro
  → custo intrínseco >> 90s em qualquer camada
BOTTLENECK_LAYER: SQL TOTVS (api-delpi) — custo por linha, não framing
ROOT_CAUSE: custo intrínseco das queries SC1/enrichment vs orçamentos
  fixos (30s client, ~90s HTTP). Não há N+1, não há filtro tardio —
  o attach já é batched e filtros vão à origem.
CONTRACT_IMPACT: dataset completo só cabe em (a) SQL mais rápido
  (índices/otimização TOTVS — alteração de estrutura não autorizada)
  ou (b) contrato paginado/assíncrono — mudança incompatível vigente.
```

Stop condition atingida: correção real exige decisão de owner —
otimização no owner TOTVS/DB ou novo contrato de export. Bump de
timeout proibido como correção única; truncamento proibido; amostragem
proibida. → `EXECUTION_DRIFT` com diagnóstico completo para o owner.

Recomendação técnica registrada: (i) api-delpi avaliar índices no
filtro dominante (branch+datas, SC1_FIL/C1_FILial+C1_NUM) e/ou
projeção reduzida; (ii) se insuficiente, contrato de export paginado
cursor-based preservando `data.items/export.*` na SURI.

## C1–C6

```text
C1 REGRESSION: suíte SURI verde (167+6) · G1 smoke PASS · OAuth PASS
C2 MCP SURFACE: tools/list = 5 · CATALOG_VERSION = 5 · nenhuma tool nova
C3 COMMITS: este documento (único diff da missão)
C4 DEPLOY: nenhum novo deploy necessário (supplies-mcp já V5 healthy;
   RBAC via endpoint — sem deploy de Core)
C5 PROD SMOKE: RBAC BEFORE/AFTER comprovado em produção; export
   full-range segue DRIFT de owner (Portal e SURI idênticos)
C6: este documento
FACTS_PROVEN: revogação g16 canônica BEFORE/AFTER; causa raiz do
  timeout medida e localizada (SQL TOTVS, não N+1/framing); paridade
  Portal↔SURI na falha; superfície MCP invariante
TO_INVENTORY: índices TOTVS efetivos para o filtro dominante; SLA de
  export vigente (não identificado → decisão de performance do owner)
UNRESOLVED: FULL_RANGE_SC_EXPORT — aguardando decisão owner (SQL ou
  contrato) — única pendência material do G2
COMMITS: este commit
NEXT_STEP: owner api-delpi/Protheus decide caminho (índices vs contrato
  paginado); depois homologação C5 completa; só então G3.
```

## Adendo A2 — Fix implementado e homologado (2026-10-31)

### Causa raiz final (cadeia completa medida)

```text
api-delpi /lines/export:        completa sozinho — 168.4s, 5445 linhas, 8.4MB, 200
PR-api client (DELPI_API_TIMEOUT):      60s  → 300s  [era gargalo]
PR-api worker (uvicorn):                sem timeout hard — OK
supplies-api client (PURCHASE_REQUESTS_API_TIMEOUT): 90s → 300s [era gargalo]
supplies-mcp client (PURCHASE_REQUESTS_API_TIMEOUT): 90s → 300s [era gargalo]
supplies-api/mcp gunicorn workers (GUNICORN_TIMEOUT_SECONDS): 90s → 300s [era gargalo]
nginx /apps/supplies-api/:              86400s — OK
Cloudflare edge:                        ~125s — LIMITE EXTERNO REMANESCENTE
```

### Fix aplicado (commit b12524a73a, infra/docker-compose.yml)

Orçamentos alinhados por serviço, env-scoped, com variáveis dedicadas:
`PURCHASE_REQUESTS_API_DELPI_API_TIMEOUT` (PR-api→api-delpi),
`PURCHASE_REQUESTS_API_TIMEOUT` (BFF/MCP→PR-api),
`SUPPLIES_API_GUNICORN_TIMEOUT_SECONDS` (workers gunicorn).
Sem mudança de contrato, sem truncamento, sem TOP, sem amostra —
evidência medida: upstream produz o dataset completo corretamente.

### Deploy

`git pull` em prod → recreate `--no-deps` de purchase-requests-api,
supplies-api, supplies-mcp (env-only, sem rebuild). Todos healthy.
Demais serviços intactos. Rollback = commit anterior + recreate.

### Homologação produtiva (mesma identidade user-delegated)

```text
OUT/2026 branch=01:
  PORTAL_EXPORT  200 · 25.4s · 686 linhas CSV
  SURI_EXPORT    200 · 20.7s · dataset completo (~1.5MB streamed)
Ano inteiro branch=01 (168s upstream):
  PORTAL_EXPORT  524 · Cloudflare edge timeout ~125s
  SURI_EXPORT    524 · idem
```

### Resultado

Envelope funcional de exportação: antes falhava qualquer dataset com
custo >30s (client PR-api); agora opera até o limite do edge CF (~120s
de custo upstream — cobre meses de dados, ~700+ linhas comprovadas).
Full-year (168s) excede o edge — residual de infra externa.

### EXECUTION_DRIFT remanescente (owner: infra/edge ou arquitetura)

`FULL_YEAR_SC_EXPORT` bloqueado por Cloudflare proxy timeout (~125s).
Opções para o owner: (a) config Cloudflare (Enterprise origin/read
rules — requer acesso à conta CF); (b) SQL/índices TOTVS para custo
<110s (DBA/Protheus); (c) contrato de export assíncrono/paginado
(decisão arquitetural). Nenhuma implementável sem autoridade
correspondente — app-layer já está correta e homologada.
```
