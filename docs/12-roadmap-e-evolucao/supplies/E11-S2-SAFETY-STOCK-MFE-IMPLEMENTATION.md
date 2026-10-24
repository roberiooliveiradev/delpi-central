# E11.S2 — Estoque de Segurança: implementação MFE

**Data:** 2026-10-24 · **BASE HEAD:** `1237cc6eb3` (pós-rebase) · **Escopo:** `plugins/supplies` apenas — zero backend/manifest/deploy.

## Arquitetura

```text
plugins/supplies  SafetyStockPage (route view `safety_stock`)
  → httpClient (Bearer user JWT) → supplies-api GET /safety-stock/*
    → api-delpi → TOTVS
```

O MFE **nunca** chama `api-delpi` nem o legado `estoque-seguranca`. Classificação, déficit e saldos são produzidos pelo servidor — a página só transporta e apresenta.

## Endpoints consumidos (BFF)

| Uso | Endpoint |
|---|---|
| Metadados dos filtros | `GET /safety-stock/filters` (`branch_catalog`, `all_scope`, `product_groups`, `units`) |
| Resumo operacional | `GET /safety-stock/summary` (9 contadores + `deficit_by_unit`) |
| Listagem | `GET /safety-stock/items` (paginação + sort server-side) |

`/items/{code}/details` e `/items/{code}/suppliers` **não** são consultados — detalhe é E11.S3 (zero N+1, sem link quebrado: nenhuma ação de detalhe renderizada).

## Estrutura

`plugins/supplies/src/features/safety-stock/`:

| Arquivo | Responsabilidade |
|---|---|
| `SafetyStockPage.tsx` | composição: PagePath → PageHero (6 tiles de classificação) → FilterBar → Cobertura do recorte (3 contadores + déficit por UM) → DataTable; estados parciais independentes |
| `SafetyStockFilters.tsx` | Filial (select único all\|01\|02), Status, Grupo, UM, Busca (debounce via `useCommittedTextFilter`), toggles `includeBlocked`/`includeWithoutSafetyStock` |
| `SafetyStockListTable.tsx` | `SuppliesDataTable` + `SuppliesCompactPagination` + visibilidade de colunas + font-size (storage keys próprias `supplies:safety-stock:*`) |
| `api.ts` | 3 chamadas BFF + guards de shape (`SafetyStockContractError` — ver residual de envelope) |
| `query.ts` | URL state, params camelCase do BFF, sort helpers, formatters |
| `types.ts`, `content.ts`, `hasActiveFilters.ts`, `safetyStockTableConfig.ts` | contratos/copy/flags/colunas |

Kit reutilizado (`@delpi/plugin-ui` via `app/suppliesUi.ts`): PagePath, PageHero (highlights com tone), SectionCard, FilterBarShell + FiltersRow, SelectField, TextField, **`SuppliesFilterCheckboxField`** (wrapper novo do `createDashboardFilterCheckboxField` já existente no kit — shim tipado atualizado), MultiSelect não necessário (branch é escopo único), DataTable, CompactPagination, DataListToolbar, StatusBadge, EmptyState, LoadingCard, StateBanner, TableColumnVisibilityMenu, TableFontSizeControls.

## Filial = filtro, nunca permission

- Opções vêm de `branch_catalog` do BFF (`OPERATIONAL_UNITS`) com fallback `session.allowedUnits`; `authorized_branches` do produtor **não é consultado**.
- `all` é enviado como `branch=all` em **uma** chamada — sem fan-out no MFE.
- Select único `Todas as filiais | Santa Catarina | Espírito Santo`; nenhum grant por filial.

## URL / estado

Params persistidos: `branch` (omitido quando `all`), `status`, `productGroup`, `unit`, `search`, `includeBlocked` (só `true`), `includeWithoutSafetyStock` (só `false`), `page`, `page_size`, `sortBy`, `sortDirection`. `popstate` restaura; valores inválidos recuperam para defaults; mudança de filtro volta à página 1; sort preserva filtros.

## Summary

Hero: `total_materials`, `with_safety_stock`, `without_safety_stock`, `below_safety_stock` (danger), `at_safety_stock` (warning), `above_safety_stock`. Seção «Cobertura do recorte»: `with_primary_stock`, `without_primary_stock`, `with_work_in_process_stock` + `deficit_by_unit` em chips por UM (sem somar UMs distintas). `0` é valor real; indisponível rende `—`, nunca `0` falso.

## Tabela

11 colunas (`product_code`, descrição+badge «Bloqueado», filial, tipo, grupo, UM, ESTSEG, saldo principal, em processo, déficit, status-badge PT-BR). Sort real no servidor (9 campos da allowlist BFF; numéricos abrem em `desc`, textuais em `asc`), paginação `page_size` ≤ 200, identidade `product_code + branch` preservada para E11.S3.

## Estados

Loading por canal (itens/summary/filtros independentes) · empty real («Nenhum material») · partial (banner por canal sem mascarar o restante) · error com retry que preserva filtros · 401/403 mapeados via `mapSafetyStockFetchError` (copy de acesso) · payload 200 malformado → erro de integração explícito, nunca empty-state.

## Residual de envelope (E11.S1)

`isSafetyStockSummary`/`isSafetyStockItemsResponse`/`isSafetyStockFiltersResponse` validam o shape: `data=null`, `{}` ou lista no lugar de objeto lançam `SafetyStockContractError` → banner de erro (não «Nenhum material»). O comportamento upstream `{}` em envelope inválido permanece residual de backend — documentado para eventual task bounded do owner BFF; **não corrigido** dentro desta fatia MFE.

## Testes

- `query.test.ts` — 20 casos: defaults, `branch=all` em chamada única, camelCase do contrato, round-trip URL A→B→A, URL inválida, toggles, allowlist de 9 sort fields, direções, guards de payload (null/lista/campo ausente), rótulos e variantes de status, `formatQuantity` preservando zero.
- `SafetyStock.structural.test.ts` — 7 casos: wiring no App, BFF-only, sem detalhe/N+1, sem `supplies.unit.*`/`authorized_branches`, kit-first, allowlist, status PT-BR.
- `Inventory.structural.test.ts` — asserção do placeholder `safety_stock` atualizada para a página real.
- **Suíte supplies: 418 passed (45 files)** · `tsc -b` limpo · `vite build` OK · lint sem erros novos (34 problemas preexistentes idênticos na baseline).

## Readiness E11.S3

A tabela já carrega `product_code + branch` por linha (rowKey `branch|code`). E11.S3 (drawer de detalhe) pode consumir `/items/{code}/details` e `/items/{code}/suppliers` com filial concreta sem alterar a listagem.
