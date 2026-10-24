# E11.P0 — Estoque de Segurança: Contract Freeze e Readiness

**Data:** 2026-10-23 · **BASE HEAD:** `c4a6ceddff` · **Tipo:** contract freeze read-only (zero código/runtime) · **Autoridade AuthZ:** ADR-009 + decisão PO `611cb8c0dc` ([BRANCH-AUTHZ.DOCS.R1](./BRANCH-AUTHZ-DOCS-R1-GLOBAL-RECONCILIATION.md))

## Executive summary

O produtor `api-delpi` já expõe **todos** os contratos de leitura que a página E11 precisa — `/supplies/safety-stock/{filters,summary,items}` + detalhe/fornecedores/histórico de preço — e **já possui o bypass contratual para o Portal**: chamadas com caller `supplies-api` + service token interno pulam o `BranchAccessGate` (`is_trusted_supplies_bff_call()`), porque o BFF já decidiu acesso e escopo. **`BRANCH_AUTHZ_RECONCILIATION = COMPATIBLE` — nenhuma mudança no produtor é necessária.** O legado `plugins/estoque-seguranca` é referência funcional (não código). Falta apenas: rotas BFF no `supplies-api`, página MFE e Help. **`E11_P0_STATUS = READY_WITH_RESIDUAL`; `E11_S1_READY_TO_AUTHORIZE = YES`.**

---

## 1. Inventário do produtor (P0.A) — `api-delpi`

Router: `api-delpi/app/interface/http/routes/supplies/safety_stock_router.py` · DTOs: `application/dto/supplies/safety_stock_request.py` · SQL: `infrastructure/persistence/totvs/supplies_repositories/safety_stock_{sql,query_repository}.py` · Domínio (owner das regras): `domain/services/supplies/safety_stock_*.py` · Testes: 17 arquivos `tests/test_safety_stock_*.py`.

| Rota | Params | Resposta (envelope `api_delpi_success` → `data`) | Erros |
|---|---|---|---|
| `GET /supplies/safety-stock/filters` | `branch` (`all`\|`01`\|`02`, default `all`), `includeBlocked` | `branch, product_groups[], units[], statuses[] (4), warehouses[], primary_warehouse, work_in_process_warehouses[], work_in_process_note, authorized_branches[]` ⚠¹ | 400/500 |
| `GET /supplies/safety-stock/summary` | `branch, includeBlocked, productGroup, unit, search, status, includeWithoutSafetyStock` | `total_materials, with/without_safety_stock, below/at/above_safety_stock, with/without_primary_stock, with_work_in_process_stock, deficit_by_unit[]` | 400/500 |
| `GET /supplies/safety-stock/items` | filtros acima + `page` (≥1), `page_size` (tier `page_50_200`: default 50, máx 200), `sortBy` (9 campos), `sortDirection` | `items[]` + `page/page_size/total/total_pages/sort_by/sort_direction` | 400/500 |
| `GET /supplies/safety-stock/items/{code}/details` | `branch`, path `code`; `peer_branch` derivado (filial irmã) | item + `available_stock`, `secondary_unit`, `conversion_*` + `sections`: `open_purchase_orders, open_purchase_requests, open_commitments, stock_projection, monthly_consumption, annual_comparison` | 400/404/500/503 |
| `GET /supplies/safety-stock/items/{code}/suppliers` | `branch`, `code` | fornecedores vinculados (`code`, `store`, `name`, …) | 400/500/503 |
| `GET /supplies/safety-stock/items/{code}/suppliers/{supplier_code}/purchase-price-history` | `branch`, `supplierStore` (obrigatório) | histórico de preço por fornecedor | 400/500/503 |
| `GET /supplies/safety-stock/consumption-analysis/{summary,items,items/{code}}` | análogo + `analysisStatus` | **E12 — fora do escopo E11** | 400/404/500/503 |

⚠¹ `authorized_branches` é derivado das permissions do **usuário** via `BranchAccessGate`; em chamada BFF confiável (service token sem contexto de usuário) tende a `[]`. **O Portal NÃO consome esse campo** — o catálogo de filiais do Portal é `OPERATIONAL_UNITS = ("01","02")` do próprio `supplies-api`.

**Item** (linha da tabela): `product_code, product_description, product_type, unit, product_group, branch, blocked, safety_stock, primary_stock, work_in_process_stock, warehouse_{50,98,99}_stock, work_in_process_{committed,available}, deficit_quantity, status`.

**Status canônicos** (`safety_stock_classification_service.py`): `without_safety_stock | below_safety_stock | at_safety_stock | above_safety_stock`. Regra: saldo disponível = armazéns **01 + 98 + 99**; `deficit = max(ESTSEG − disponível, 0)`; WIP = 50 + 98 + 99.

**Sort items:** `product_code, product_description, product_group, unit, safety_stock, primary_stock, work_in_process_stock, deficit_quantity, status`.

**Semântica de branch:** `normalize_branch_scope` aceita `all`/`01`/`02` (+ aliases PT); `all` → SQL sem predicado (união 01+02, cada linha carrega `branch`). `details` aceita escopo mas o contrato de detalhe trabalha sob filial concreta (peer = outra filial). **`branch` inválido → 400.**

## 2. Reconciliação de AuthZ legada (P0.B)

| Elemento | Local | Comportamento |
|---|---|---|
| `SAFETY_STOCK_ACCESS = estoque-seguranca.access` | `api_delpi_permissions.py` | permission global do app legado |
| `SAFETY_STOCK_BRANCH_VIEW_PERMS` = `estoque-seguranca.view.filial-{sc→01, es→02}` | idem | gate por filial para chamadas **diretas** |
| `BranchAccessGate` | `interface/http/branch_access_gate.py` | 403 por filial/consolidado — **somente para callers diretos** |
| `require_any_permission_or_supplies_bff(...)` | `supplies_bff_service_access.py` | permission legada **OU** caller `supplies-api` + service token |
| `branch_access_error()` | `safety_stock_branch_access.py` | **retorna `None` para trusted BFF call** — o gate por filial não se aplica ao Portal |

Docstring canônica do módulo: *"The Portal Suprimentos BFF already decided supplies.access and unit scope. api-delpi must not copy that membership. Direct callers keep the route's own permission and branch gate."*

**`BRANCH_AUTHZ_RECONCILIATION = COMPATIBLE`.** O produtor já reconhece o contrato BFF (`X-Delpi-Caller-App: supplies-api` + service token interno) — precedente ativo usado hoje pelo Overview (`KPI-CRITICAL-MP` → `get_safety_stock_summary`). Filial segue sendo filtro de domínio validado no BFF contra `OPERATIONAL_UNITS`; nenhum grant `supplies.unit.*` é criado ou exigido; proteção dos callers diretos permanece intacta.

## 3. Inventário do legado (P0.C) — `plugins/estoque-seguranca`

App standalone que chama **`api-delpi` direto** com `estoque-seguranca.access`. Duas telas via `EssPageNav`: `monitor` (SafetyStockPage) e `analysis` (ConsumptionAnalysisPage).

| Capacidade legada | Fonte | Destino |
|---|---|---|
| Filtros: filial, produtos bloqueados, grupo, UM, busca, status, sem ESTSEG | `SafetyStockFilters` + `/filters` | `IN_SCOPE_E11` |
| KPIs summary (9 contadores + déficit por UM) | `SafetyStockSummary` | `IN_SCOPE_E11` |
| Tabela paginada/ordenável + export | `SafetyStockTable` | `IN_SCOPE_E11` (export: `TO_INVENTORY` em S1 — não bloqueia P0) |
| Busca rápida de produto | `ProductQuickSearch` | `IN_SCOPE_E11` (busca na FilterBar cobre; quick-search dedicado opcional) |
| Modal detalhe: saldos, projeção, POs abertos, SC abertas, empenhos | `SafetyStockDetailModal` + `/items/{code}/details` | `IN_SCOPE_E11` (via página/drawer — decisão de UX em S2) |
| Fornecedores vinculados + histórico de preço | `SafetyStockLinkedSuppliersSection`, `…PriceHistoryPanel` | `E11` fornecedores vinculados; histórico de preço = `E18` (só deep link futuro) |
| Consumo mensal/anual do detalhe | sections `monthly_consumption/annual_comparison` | `E11` (vem embutido no detalhe; não é a página E12) |
| Página Análise de Consumo completa | `ConsumptionAnalysisPage` | **`E12`** |
| `authorized_branches` / bootstrap por tentativa | `safetyStockApi.ts` | `LEGACY_ONLY` — Portal usa catálogo fixo |
| Gráficos/charts dedicados do legado | `Ess*Chart.tsx` | `LEGACY_ONLY` — kit-first no Portal |

## 4. Escopo funcional E11 (P0.D) — congelado

**Página `/apps/supplies/safety-stock`:** hero + FilterBar (filial `Todas|01|02`, status, grupo, UM, busca, toggles blocked/sem-ESTSEG) + Summary hero (9 contadores + déficit por UM) + tabela server-side (paginação, ordenação, URL/F5) + detalhe do item (seções ESTSEG: saldos, projeção, POs/SCs/empenhos, consumo, fornecedores vinculados). Refresh manual; estados loading/empty/partial/error/403/404.

**Fora de E11:** página Análise de Consumo (E12), Product 360 (E17 — deep link futuro por `product_code` somente quando contrato existir), Histórico de Preços dedicado (E18 — os dados de fornecedor vinculado ficam no detalhe E11; a página completa é E18). Nenhuma fórmula/threshold novo — 100% dos indicadores vêm do produtor.

## 5. Boundaries (P0.E)

| Etapa | Owner da regra | Superfície | Compartilhado |
|---|---|---|---|
| E11 Estoque de Segurança | `safety_stock_*` (api-delpi) | `/safety-stock` | detalhe expõe consumo/projeção/fornecedores como seções read-only |
| E12 Análise de Consumo | `safety_stock_consumption_analysis_*` | página própria futura | reusa mesmo produtor; link futuro |
| E17 Produto 360 | `product_routes.py` | `/products/{code}` futuro | `product_code` = chave do deep link |
| E18 Onde Usado / Preços | `product_routes.py` + `purchase-price-history` | futuro | endpoint já existe — E11 não o consome em P0 (ou só como link) |

Sem duplicação: composições E17/E18 não entram no BFF de E11.

## 6. Contrato BFF proposto (P0.F) — `supplies-api`

Blueprint novo `safety_stock_bp` espelhando `inventory_routes.py` (`@require_policy(can_use_operations)` → `supplies.access`; service valida `branch` contra `OPERATIONAL_UNITS`; `DelpiApiGateway` com `X-Delpi-Caller-App: supplies-api` + service token; erros → `unauthorized/forbidden/not_found/unprocessable/bad_gateway`).

| Rota BFF (`/apps/supplies-api`) | Upstream | Observações |
|---|---|---|
| `GET /safety-stock/filters?branch=` | `/supplies/safety-stock/filters` | BFF **descarta** `authorized_branches` e devolve `branch_catalog = OPERATIONAL_UNITS` |
| `GET /safety-stock/summary?branch=all|01|02&…` | `/supplies/safety-stock/summary` | `all` → repassa `all` (produtor une 01+02) |
| `GET /safety-stock/items?branch=&page=&page_size=&sort=&…` | `/supplies/safety-stock/items` | `sort` Portal = `sortBy|sortDirection`; validar contra ALLOWED_SORT_FIELDS |
| `GET /safety-stock/items/{code}/details?branch=` | `/items/{code}/details` | `branch` concreta obrigatória (peer_branch automático do produtor) |
| `GET /safety-stock/items/{code}/suppliers?branch=` | `/items/{code}/suppliers` | fornecedores vinculados do detalhe |

Gateway: estender `SuppliesDelpiReads` (já tem `get_safety_stock_summary`/`get_safety_stock_items`) com filtros, details e suppliers — permitindo `branch="all"` onde o produtor aceita escopo. Sem Postgres, sem escrita, timeout do gateway canônico, degrade parcial na composição (summary ≠ items).

## 7. UX e componentes (P0.G)

Kit `@delpi/plugin-ui` disponível: `DataTable`/`DataTableSection`, `Pagination`/`CompactPagination`/`TablePaginationNav`, `ConfigurablePresentationTable`, `DataCardsGrid`, `TableColumnVisibilityMenu`, `SeriesSparkline`/`CompareSparkline`, `StatusBadge`/feedback, `SectionCard`/layout, formulários/MultiSelect, help. Reuso do padrão `features/inventory` (E10) e `purchase-requests`: FilterBar + tabela server-side + URL state + `SuppliesLoadingCard`. Placeholder `safety_stock` existe em `App.tsx`; rota já no manifest (`supplies.access`, `showInMenu:false`, order 39, icon `shield`). `.dashboard-supplies-portal` preservado; zero CSS do legado.

## 8. RQ/AC (P0.H)

| RQ | AC verificável |
|---|---|
| RQ-01 `supplies.access` | 401 sem JWT; 403 sem capability; 200 com `supplies.access` |
| RQ-02 filial = filtro | `01`/`02`/`all` funcionam para qualquer `supplies.access`; filial inválida → 422/400; **sem** teste de «sem permissão de filial» |
| RQ-03 BFF-only | MFE nunca chama api-delpi; gateway carrega caller+service token |
| RQ-04 indicadores reais | BFF/MFE não recomputam status/déficit/saldos — passthrough do produtor |
| RQ-05 tabela paginada | `page/page_size` honrados, `total/total_pages` exibidos |
| RQ-06 filtros + URL | estado completo serializado na URL; F5 restaura |
| RQ-07 sort server-side | apenas campos de `ALLOWED_SORT_FIELDS`; inválido → 422 |
| RQ-08 detalhe contratado | seções compostas do produtor; 404 → empty-state |
| RQ-09 estados | loading/empty/partial(error de bloco)/error/403/404 renderizados |
| RQ-10 status map | 401/403/404/422/502 mapeados do gateway |
| RQ-11 Help | entrada no manual + FAQ sincronizados no mesmo PR |
| RQ-12 a11y/responsive | claro/escuro, teclado, mobile |
| RQ-13 sem duplicação de regra | nenhuma fórmula de ESTSEG/déficit/projeção no BFF/MFE |
| RQ-14 performance | page_size ≤ 200; chamadas paralelas summary+items; timeouts gateway |
| RQ-15 zero escrita | nenhum POST/PUT; nenhum flag alterado |
| RQ-16 smoke federado | bundle contém `safety-stock`; rota 401 anônima; clique autenticado fecha gate |

Testes: positive/sibling/negative por endpoint; `01`, `02`, `all`, filial inválida, sem `supplies.access`, erro produtor (502/503→502), empty real, paginação, sort inválido, URL/F5.

## 9. Receita E11.S1–S5 (P0.I) — **não autorizada**

| Etapa | Conteúdo | Dependência |
|---|---|---|
| **S1 BFF** | `safety_stock_bp` + service + extensão `SuppliesDelpiReads`; 5 rotas; testes contract/auth/filtro/erros | E11.P0 (este doc) |
| **S2 MFE** | `features/safety-stock/`: FilterBar, Summary hero, DataTable, URL/F5, estados; wire `App.tsx`+`pluginRoutes` | S1 |
| **S3 Detalhe** | drawer/rota do item: saldos, projeção, POs/SCs/empenhos, consumo, fornecedores vinculados | S2 + contrato details validado |
| **S4 Help+testes** | manual `/help`, FAQ, tooltips; cobertura unit/contract; a11y | S2/S3 |
| **S5 Deploy+gate** | build, deploy federado `supplies-api`+`supplies`, smoke 401 + autenticado, `GATE-FEATURE E11` | S4 |

## 10. Gates de readiness

| Gate | Resultado |
|---|---|
| `E11_P0_STATUS` | **PASS** (este documento) |
| `BRANCH_AUTHZ_RECONCILIATION` | **COMPATIBLE** — bypass BFF já implementado no produtor |
| `PRODUCER_CONTRACT_READY` | **PASS** — 7 endpoints + seções compostas + 17 test files |
| `BFF_CONTRACT_READY` | **PASS** — congelado em §6 (espelha padrão E10) |
| `UI_SCOPE_READY` | **PASS** — escopo §4, kit inventariado §7 |
| `BUSINESS_RULES_READY` | **PASS** — classificação/déficit/armazéns têm owner (`safety_stock_classification_service`); sem fórmulas novas |
| `RQ_AC_READY` | **PASS** — §8 |
| `E11_S1_READY_TO_AUTHORIZE` | **YES** |

## 11. Residuais e riscos

- **`authorized_branches` do produtor** pode vir vazio em chamada BFF — mitigado: BFF usa `OPERATIONAL_UNITS` e documenta o campo como não consumido.
- **Export de planilha** do legado sem contrato dedicado inventariado — `TO_INVENTORY` em S1 (pode virar paginação completa ou CSV server-side futuro).
- **Smoke autenticado** continua pendente como residual de gate (mesmo padrão E10).
- Sem bloqueio de AuthZ, contrato ou owner → `EXECUTION_DRIFT` não disparado.

## 12. Próxima decisão do PO

Autorizar **E11.S1** (BFF safety-stock, receita §9) com base neste freeze — ou ajustar escopo (ex.: incluir/excluir detalhe em S3, export).


## Revisão GPT — E11.P0 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para contract freeze documental. A matriz do produtor, as cinco rotas BFF e o recorte E11/E12/E17/E18 foram inspecionados no documento do commit `da39aa1450` e em `API-ROUTES.md`. Evidência de 198 testes PASS é reportada pelo executor, não reexecutada nesta revisão. **`E11_S1_READY_TO_AUTHORIZE=YES`**, mas S1 somente começa após autorização explícita do PO; não há implementação/deploy nesta revisão.

**Guardrails obrigatórios de S1:** validar na implementação e nos testes que o reconhecimento trusted-BFF do produtor exige credenciais reais, e não apenas header de caller; `branch=all` é filtro de dados repassado ao produtor sem fan-out, enquanto detalhe requer filial concreta como chave de consulta, sem autorização por filial; preservar erro 404 de recurso inexistente distinto de lista vazia e falhas upstream distintas de sucesso vazio; não acrescentar exportação sem contrato. Manter `supplies.access` efetiva pela Core, ausência de `supplies.unit.*`, BFF-only e zero escrita ERP.

**Residual:** smoke autenticado end-to-end e evidência visual são futuros gates S5; não podem ser inferidos dos testes do produtor nem da documentação. `X4.PROD-C1` permanece bloqueado e independente.
