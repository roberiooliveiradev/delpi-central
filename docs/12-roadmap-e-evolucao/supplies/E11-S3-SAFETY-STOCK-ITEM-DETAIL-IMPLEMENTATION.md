# E11.S3 — Detalhe do Item de Estoque de Segurança (MFE)

**Status:** implementado · **Owner:** `plugins/supplies` · **BFF:** `supplies-api` (E11.S1, sem alteração)

## Baseline

- BASE HEAD: `664eec398c` (inclui revisão GPT `1b409ae84f` de E11.S2 — `ACCEPT_WITH_RESIDUAL`, `E11_S3_READY_TO_AUTHORIZE=YES`).
- Contrato produtor revalidado em HEAD: `get_safety_stock_item_details_use_case.py`, `safety_stock_stock_projection_service.py`, `safety_stock_purchase_coverage_service.py`, `safety_stock_query_repository.py` (shapes reais de coleções, projeção, consumo e fornecedores).

## Decisão UX: modal (`SuppliesModal`)

O kit `@delpi/plugin-ui` expõe `ModalShell` (wrapper `SuppliesModal`, já comprovado em `SupplierDetailPage`/`SupplierCreatePage`/`EnrichmentSection`); **não existe drawer no kit** e criar overlay paralelo é proibido. O volume de seções cabe em scroll interno do modal; Escape/botão de fechar/overlay são suportados pelo componente.

## Interação de abertura

- Botão «Ver detalhes» por linha (`aria-label` inclui o código do produto) + `onRowClick` da `DataTable` do kit.
- Identidade: `product_code + branch` da própria linha — na visão `all`, cada linha abre sua filial concreta.
- Zero N+1: nenhum fetch de detalhe durante a listagem; os dois endpoints só são chamados após a abertura (2 requests por abertura, em paralelo).

## Endpoints consumidos (somente `supplies-api`)

| Uso | Endpoint |
|---|---|
| Detalhe composto | `GET /safety-stock/items/{code}/details?branch=XX` |
| Fornecedores | `GET /safety-stock/items/{code}/suppliers?branch=XX` |

Filial concreta obrigatória; `branch=all`/ausente/inválido não abre detalhe (guard `parseDetailTargetFromSearch` + `onOpenDetail`).

## Seções (dados reais do produtor, passthrough)

- **Identificação**: código, descrição (+badge «Bloqueado»), filial, UM, UM secundária + fator de conversão, grupo, tipo, status.
- **Estoque e cobertura**: ESTSEG, saldo disponível (01+98+99), armazém principal, 98, 99, em processo, déficit, último inventário; `purchase_coverage` (status `sufficient|partial|none`, elegível, falta comprar, próxima entrega, warnings).
- **Abastecimento**: `open_purchase_orders`, `open_purchase_requests`, `open_commitments` (badge «UM divergente» quando `unit_compatible=false`; warnings de empenhos).
- **Projeção**: `stock_projection.summary` (status `sufficient|temporary_shortage|projected_deficit`, saldos inicial/final/mínimo, primeira ruptura, a comprar) + extrato `items` com `date_status` (hoje/agendado/vencido/sem data).
- **Consumo**: `monthly_consumption` (série + consumo do período) e `annual_comparison` (pivot mês × ano).
- **Fornecedores vinculados**: endpoint próprio, canal independente; `supplier_code + supplier_store`; última compra quando `has_last_purchase`.

Nada é recalculado no MFE; seção ausente no payload = «indisponível» (nunca zero/vazio falso).

## URL / F5

Detalhe endereçável por `item` + `itemBranch` na mesma query-string dos filtros (sem rota/manifest novo). Abrir/fechar via `pushState`; `popstate` restaura lista e detalhe; F5 reproduz o item; filtros/paginação preservados.

## Estados

Loading por canal (detalhe e fornecedores independentes) · empty real por coleção · partial (fornecedores falham sem derrubar o detalhe; seção não retornada = indisponível) · error + retry por canal · 401/403 → copy de acesso · 404 → «Material não encontrado nesta filial» · 422 → mensagem do BFF · payload malformado → `SafetyStockContractError` (guards `isSafetyStockItemDetail`/`isSafetyStockSuppliersResponse`) · troca rápida de item aborta respostas atrasadas e zera estado anterior.

## Arquivos

- Novo: `SafetyStockDetailModal.tsx`.
- Alterados: `types.ts` (+contratos de detalhe), `api.ts` (+2 fetchers + guards), `content.ts` (+`SAFETY_STOCK_DETAIL_CONTENT` + labels de status), `query.ts` (+`item`/`itemBranch` + `parseDetailTargetFromSearch`, `formatDatePtBr`, `formatCurrencyPtBr`), `safetyStockListTable.tsx` (ação + `onRowClick`), `SafetyStockPage.tsx` (estado de detalhe na URL), `helpTooltips.ts`, `index.css` (`.sp-safety-stock-detail__*`, `.sp-safety-stock__row-action`), `SafetyStock.structural.test.ts`, `query.test.ts`.

## Testes / build

- +12 testes (37 na feature): round-trip URL do detalhe, filial concreta obrigatória, guards `{}`/null/shape inválido, N+1 (1 chamada por fetcher), seções do contrato, identidade fornecedor.
- Suíte `plugins/supplies`: **428 pass (45 files)** · `tsc -b` limpo · `vite build` OK.
- Lint: 10 erros idênticos à baseline; +2 warnings `set-state-in-effect` (mesmo padrão aceito dos efeitos de fetch do codebase).
- Evidência visual autenticada: `TEST_NOT_RUN` (pendente do gate E11).

## Residuais

- Envelope BFF `{}` com HTTP 200 em payload upstream malformado permanece mitigado por guards MFE (correção bounded é do owner `supplies-api`).
- `peer_branch_stock` não é enviado pelo BFF (parâmetro `peer_branch` não exposto) — não renderizado; registrar como `TO_INVENTORY` se o PO quiser comparativo SC×ES.
- Evidência visual/smoke federado: `TEST_NOT_RUN`.
