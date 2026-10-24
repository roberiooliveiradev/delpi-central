# EN.A3–A7 — Fichas SC/PC enriquecidas (implementação única)

> Status: `DONE` · `NO_BACKEND_CHANGE` · `DEPLOY_AUTHORIZED`
> Baseline: `be33a414a0` · Data: 2026-10-24 · Owner: `plugins/supplies`
> Pré-requisitos: EN.A1 (`f90b1644d7`), EN.A2 (`485c65abe1` + revisão `be33a414a0`),
> D1/D2 aprovadas (`dc9d7011`).

## 1. Escopo executado

| Etapa | Entrega |
|---|---|
| EN.A3 | Itens da SC: UM+quantidades, necessidade, CC c/ descrição, estágio, aprovação+aprovador, fornecedor sugerido, conta contábil (D2) |
| EN.A4 | Seções «Pedidos vinculados», «Recebimentos» e «Acompanhamento» na ficha SC |
| EN.A5 | Links SC→PC e PC→SC com identidade canônica; `countLinkedOrders` corrigido para ignorar identidades incompletas (residual EN.A2) |
| EN.A6 | Ficha PC: indicadores seguros (itens em aberto, atraso por item), link para SC origem, mensagem D1 neutra |
| EN.A7 | Tooltips, ajuda contextual e Manual sincronizados |

## 2. Decisões de implementação

- **Fonte dos pedidos vinculados:** `header.purchase_orders` é um resumo
  deduplicado (6 campos). Quantidades/datas/recebimentos vivem em
  `lines[].purchase_orders` — `collectLinkedOrders(lines)` deduplica por
  `(branch, order_number, order_item)`.
- **`countLinkedOrders`:** identidades incompletas (filial ou número vazios)
  são ignoradas — coleção só de referências quebradas nunca vira «1».
  Link SC→PC só renderiza quando `hasCompleteOrderIdentity`.
- **PC→SC:** a SC origem compartilha a filial do PC (única identidade
  disponível no contrato); 403/404 da ficha SC seguem neutros. O item da SC
  permanece como contexto textual (`numero / item`), fora da URL.
- **Situação de entrega (contexto SC):** vocabulário do produtor
  `received/overdue/on_time/not_applicable` → «Recebido», «Em atraso»,
  «No prazo», «Não aplicável» — distinto do vocabulário da lista PC
  (`late/on_time/no_date`), sem conversão entre eles.
- **Acompanhamento:** `SuppliesEventsSection` (kit) com `timeline[]` real;
  `expected_delivery` marcado «(prevista)» + tom `info`; nunca «histórico».
- **PC hero:** indicadores derivados somente de campos contratados por item
  (`delivery_status === "late"`); nenhum «dias de atraso» (ausente do contrato).
- **D1:** `detailNotFound` = «Pedido não localizado entre os pedidos em aberto
  disponíveis para consulta.» — nunca implica conclusão.
- **D2:** `account_code` por item (string, zeros à esquerda), fornecedor
  sugerido via `SuppliesSupplierIdentity`, aprovador por linha — nada agregado.
- **`buyer` residual:** `_enrich_order` emite `buyer: null` (campo
  inexistente na linha SQL); inofensivo, não tipado — exibido
  `order_user_name`/`buyer_code` quando necessário futuramente.

## 3. Componentes do kit

`SuppliesEventsSection` (1º uso em feature), `SuppliesEntityLink`,
`SuppliesSupplierIdentity`, `SuppliesStatusBadge`, `SuppliesSectionHintLabel`,
`SuppliesSectionCard`, `SuppliesEmptyState`. CSS: `__line-head`, `__line-meta`,
`__table-wrap`/`__table` (ficha SC), `__indicators`/`__scope-note` (ficha PC).

## 4. Semântica preservada

- Quantidades sempre com a UM da linha (`formatQuantityWithUnit`); nenhum
  total global de quantidade (guard estrutural reforçado para escopo header).
- Aprovação nunca promovida ao header (`approval_summary.approver_name`
  proibido por guard).
- Acompanhamento ≠ auditoria (hint explícito; guard `histórico|audit` ausente).
- AuthZ/backend intactos: zero endpoint, zero permission, zero fetch novo.

## 5. Help sync (EN.A7)

- `purchaseRequestDetail` — inclui itens, pedidos, recebimentos, acompanhamento.
- Novas: `purchaseRequestDetailOrders`, `purchaseRequestDetailReceipts`.
- `purchaseOrderDetail` — semântica do universo aberto + link SC + atraso
  derivado sem «dias».
- `purchaseOrderDetailItems` — SC origem clicável.
- Manual: «Ver o detalhe de um pedido» e «Ver o detalhe de uma solicitação»
  reescritas.

## 6. Testes e evidências

- `PurchaseRequestDetailHero.test.ts`: +8 testes (identidade incompleta,
  `hasCompleteOrderIdentity`, `collectLinkedOrders`, `collectReceipts`,
  `formatQuantityWithUnit`, labels/variant de entrega, tone/referência de
  timeline).
- Structural SC: guards de `header.*_quantity`/`approver_name` estreitados ao
  escopo header; novas asserções EN.A3–A5; guard anti-«histórico».
- Structural PC: D1 exata, link SC, indicadores sem `days_overdue`.
- **460/460** testes · `tsc --noEmit` PASS · `vite build` PASS · lint limpo
  nos arquivos tocados (escapes pré-existentes no structural PC corrigidos;
  `_branches` não usado em `purchase-orders/query.ts` é erro pré-existente
  fora do diff, mantido) · `git diff --check` limpo.

## 7. Residuais

- PC→SC usa a filial do PC como identidade da SC (contrato não carrega
  filial de origem); SC em outra filial → 404 neutro.
- `buyer: null` emitido pelo produtor — residual cosmético do payload.
- Recebimentos em «Acompanhamento» exibem eventos derivados, não trilha
  completa (aprovações/alterações continuam lacuna documentada).
- Smoke autenticado: `INCONCLUSIVE` até evidência de sessão federada.


## Parecer GPT — aceite técnico e publicação (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL` para EN.A3–A7 em código; deploy `PASS_DEPLOYED` reportado pelo executor; smoke autenticado `INCONCLUSIVE`.** Inspecionados no commit `a4def81ee7`: `PurchaseRequestDetailPage.tsx`, `PurchaseOrderDetailPage.tsx`, `purchase-requests/query.ts` e este registro. Estão presentes seções de itens, pedidos vinculados, recebimentos e acompanhamento via kit; conta contábil e fornecedor sugerido por item, links SC↔PC e copy neutra D1. Os resultados de 460 testes, build/typecheck e detalhes do deploy são relatados pelo executor e não foram reexecutados nesta revisão.

**Residuais conhecidos e aceitos:** (1) a navegação PC→SC utiliza filial do PC porque o contrato não informa filial da SC de origem; um vínculo interfilial pode retornar consulta não localizada; tratar 403/404 de modo neutro, não inferir inexistência; (2) `buyer: null` é residual informativo do produtor; (3) timeline é derivada, não auditoria; (4) não há evidência de QA autenticado desktop/mobile/teclado no runtime. **Não reabrir inventário para esses pontos sem evidência de defeito real.** EN.A3–A7 concluídas em código, mas **`GATE-FEATURE` permanece `INCONCLUSIVE`** até evidência de jornada autenticada. Próximo passo: homologação visual única SC→PC→recebimentos e correções pontuais que ela revelar; nenhuma Fase B–D foi autorizada.
