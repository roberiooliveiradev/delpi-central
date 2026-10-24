# EN.A2 — SC Detail: Hero enriquecido em 3 níveis

> Status: `DONE` · `NO_BACKEND_CHANGE` · `NO_DEPLOY`
> Baseline: `9aa3e4b181` · Data: 2026-10-24 · Owner: `plugins/supplies`
> Pré-requisito: EN.A1 (`f90b1644d7`) presente + revisão GPT `9aa3e4b1` aceita
> (residual da fixture corrigido nesta fatia — 2º pedido adicionado).

## 1. Escopo executado

Reorganização do cabeçalho da ficha SC em 3 níveis, somente com campos
contratados e tipados em EN.A1 — sem novo contrato, sem cálculo de domínio,
sem alteração da tabela de itens.

## 2. Layout implementado (vs. wireframe v2)

| Nível | Conteúdo | Campos |
|---|---|---|
| 1 — Identificação | unidade c/ nome, nº SC, abertura, situação | `branch` (`formatSuppliesUnitLabel`), `request_number`, `issue_date`, `overall_stage` → `SuppliesStatusBadge` |
| 2 — Contexto | solicitante (identidade c/ foto), centro(s) de custo, aprovação | `requester` (`SuppliesPersonIdentity`), `cost_centers[]` (código + descrição; `+N` com `title` da lista completa), `approval_summary.status` + aprovador granular |
| 3 — Indicadores seguros | itens visíveis, pedidos vinculados, atraso | `visible_items_count`, `countLinkedOrders(purchase_orders)`, `has_overdue_order` + `max_days_overdue` |

## 3. Semântica dos indicadores e campos

- **Pedidos vinculados:** `countLinkedOrders` conta identidades distintas
  `(branch, order_number)` — o produtor emite linhas deduplicadas por
  `(order_number, order_item)`; a cardinalidade por identidade canônica do
  pedido é derivação de apresentação, não fórmula de domínio. Residual de
  contagem de *linhas* de pedido resolvido.
- **Atraso:** badge «Em atraso» + «até N dias» quando
  `has_overdue_order`/`max_days_overdue` provados; «Sem atraso» somente com
  pedidos vinculados e sem atraso; «—» sem pedidos.
- **Aprovação:** `approval_summary.status` → badge canônico
  (Aprovada/Rejeitada/Bloqueada/Não informada — sem inventar «Aguardando»).
  Aprovador: `uniqueApproverNames(lines)` — 1 nome → exibe; N → «N aprovadores»;
  0 → omite. **Nenhum aprovador de linha promovido ao header** (granularidade
  por item preservada; detalhamento fica para EN.A3).
- **Centros de custo:** `code — description`; `+N` quando múltiplos, com
  `title` listando todos — nenhum CC arbitrário apresentado como "o" CC.
- **Quantidades:** proibido total global — `header.*_quantity` não é
  renderizado em lugar nenhum (guard no structural test).

## 4. Kit e componentes

`SuppliesPageHero`, `SuppliesPagePath`, `SuppliesPersonIdentity`,
`SuppliesStatusBadge`, `SuppliesSectionHintLabel`, `SuppliesLoadingCard`,
`SuppliesEmptyState`, `SuppliesStateBanner`, `SuppliesSectionCard`,
`SuppliesActionButton`. `stageBadgeVariant`/`isKnownOverallStage` movidos para
`query.ts` (fonte única — cópias privadas de `PurchaseRequestsListTable` e
`PurchaseRequestsCards` removidas). CSS: 25 linhas novas sob
`.dashboard-supplies-portal` (espaçamento de níveis + notas).

## 5. Help sync

`SP_HELP.purchaseRequestDetail` reescrita (escopo CC, aprovação por item,
atraso derivado, indicadores seguros). Manual atualizado na entrada «Ver o
detalhe de uma solicitação».

## 6. Estados e acessibilidade

Loading/forbidden/not-found/error/empty inalterados; sem fetch novo; sem
estado stale (payload único). Grid responsivo já existente (2 colunas <720px,
1 coluna <400px); sem rolagem horizontal; badges passivos (não parecem
botões); `title` da lista de CCs acessível.

## 7. Testes e evidências

- `PurchaseRequestDetailHero.test.ts` (novo, 5 testes): `countLinkedOrders`
  (dedup por filial+número, irmão multi-item, filiais distintas),
  `uniqueApproverNames` (dedup, trim, nulos), `labelApprovalStatus`/`approvalBadgeVariant` (canônicos).
- `PurchaseRequests.structural.test.ts` atualizado: guards de hero (sem
  `*_quantity`, sem `approver_name` direto, presença dos helpers).
- Fixture EN.A1 ampliada para 2 pedidos/2 fornecedores (residual GPT).
- **452/452** testes · `tsc --noEmit` PASS · `vite build` PASS · lint: 1
  warning pré-existente (`set-state-in-effect` no effect inalterado) ·
  `git diff --check` limpo.

## 8. Limitações e residuais

- Nome do aprovador: granularidade por item; resumo no hero é «1 nome» ou
  «N aprovadores» — detalhamento por item = EN.A3.
- Sem indicador de entradas/recebimentos no hero (não solicitado).
- `header.approval_summary.status` deriva da **primeira linha** no produtor —
  exibido como «Aprovação» com a granularidade por linha preservada (D2).
- Deploy não realizado (não autorizado); smoke autenticado `INCONCLUSIVE`.

## 9. Readiness EN.A3

**READY** — itens já têm `unit`, `request_required_date`, `ordered_quantity`,
`request_open_quantity`, `suggested_supplier`, `account_code` (D2),
`approval`, `purchase_orders[]` tipados. Falta apenas autorização.
