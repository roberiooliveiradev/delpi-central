# PC Detail UX Enrichment — ficha do Pedido de Compra

> Status: `DONE` · `NO_BACKEND_CHANGE` · `DEPLOYED`
> Baseline: `c06515b49b` · Data: 2026-10-24 · Owner: `plugins/supplies`
> Pré-requisitos: EN.A1–A7 (`a4def81ee7`), D1/D2 aprovadas, SC homologada pelo PO.

## 1. Delta sobre EN.A6

A ficha PC já tinha: hero de 2 níveis (identificação + indicadores),
cards por item com fornecedor/SC/quantidades/preços, recebimentos por item,
link PC→SC e mensagem D1. Este incremento completou o delta pedido:

| Área | Antes | Depois |
|---|---|---|
| Cabeçalho | Filial + Pedido + indicadores | **+ Fornecedor e Comprador** com granularidade fiel |
| Fornecedor | só por item | cabeçalho: 1 fornecedor → `SuppliesSupplierIdentity` (link E14); N → «N fornecedores»; nunca o primeiro arbitrário |
| Comprador | só por item (`buyer_code`) | cabeçalho: 1 comprador → `SuppliesPersonIdentity`; N → «N compradores» |
| Recebimentos | coluna NF combinada `numero-serie` | **Série em coluna própria** (NF \| Série \| Item \| Qtd \| Preço \| Valor \| Emissão \| Entrada) |

## 2. Semântica e limites de contrato (residuais)

- **Valor em aberto no cabeçalho:** **não exibido** — o contrato PC detail
  só traz `open_value` por item; somar no MFE seria cálculo de domínio
  proibido. O `total_open_value` existe apenas no resumo da LISTA (owner:
  produtor). Registrado como residual até o produtor agregar.
- **Acompanhamento/timeline:** **não criada** — o contrato PC não emite
  eventos; datas permanecem nos itens (emissão, prevista, entradas NF).
  Fabricar marcos por suposição foi descartado; guard estrutural impede
  `SuppliesEventsSection` na página.
- **Atraso:** badge derivado de `delivery_status === "late"` por item;
  nenhum «dias de atraso» (ausente do contrato).
- **D2:** aprovador/fornecedor sugerido/conta contábil **não** foram
  copiados para o PC — pertencem à ficha SC.
- Distinção preservada: «Entregue» (baixa C7_QUJE) ≠ recebimentos NF (SD1).

## 3. Implementação

- `query.ts`: `uniqueSupplierIdentities(items)` (dedup por `code|store`),
  `uniqueBuyerCodes(items)`; correção do erro pré-existente `_branches`.
- Página: novo nível de contexto no hero (`__context`), coluna Série,
  remoção de `invoiceLabel`/`PurchaseOrderReceipt` sem uso.
- Help: `purchaseOrderDetail` atualizada (fornecedor/comprador no
  cabeçalho); Manual sincronizado.

## 4. Evidências

- `PurchaseOrderDetailHeader.test.ts` (novo): dedup por (código, loja),
  nome sem código exibível, zeros à esquerda do comprador, vazios.
- Structural PC: asserções de cabeçalho, Série, e guards — sem
  `items.reduce`/`total_open_value`, sem `SuppliesEventsSection`.
- **463/463** testes · `tsc --noEmit` PASS · `vite build` PASS ·
  lint limpo nos arquivos tocados · `git diff --check` limpo.

## 5. Deploy

`up-prod-sequential.sh --build supplies` em srv-api — ver relatório de
execução para SHA/imagem/bundle/health.


## Revisão GPT — PC Detail (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para o código `4d34f60bca`. Conferidos `PurchaseOrderDetailPage.tsx`, `purchase-orders/query.ts` e este documento: o cabeçalho apresenta fornecedor/comprador respeitando a cardinalidade observada dos itens; a tabela de recebimentos separa número e série da NF; os demais campos e o vínculo PC→SC foram preservados. Sem agregação de valor de domínio no MFE, sem timeline inexistente no contrato. **463 testes, tsc, build, lint e deploy `supplies` são reportados pelo executor, não reexecutados no review.**

**Residuais aceitos:** valor total aberto no cabeçalho depende de contrato do produtor; acompanhamento histórico do PC e dias de atraso não estão contratados; navegação PC→SC entre filiais permanece condicionada à identidade disponível; smoke autenticado e verificação visual continuam `INCONCLUSIVE`. A falha de TypeScript 7 em `plugins/controllership-finance/tsconfig.app.json` foi relatada em outro worktree/contexto, sem relação material demonstrada com este diff e não deve ser corrigida nesta fatia. **Próximo passo:** homologação visual única da ficha de PC publicada, comparando desktop/mobile e recepção de NF com série; corrigir apenas defeitos reproduzidos. Não iniciar fases B–D por inferência.


## PC DETAIL UX.S2 — Refinamento pós-homologação

### Problemas observados (homologação visual autenticada, PC 01/057175)

1. **Título «Recebimentos» duplicado** no estado vazio: o item-card
   renderiza `<h3>Recebimentos` + hint e, dentro do painel,
   `SuppliesEmptyState` repetia o mesmo título antes da mensagem.
2. **Comprador «—»** no cabeçalho e no item.
3. **Recebimentos parciais** não exercitados visualmente.

### Causas provadas

- **Duplicação:** `SuppliesEmptyState` é criada com `withTitle: true`
  (`suppliesUi.ts`) — sempre renderiza `<h3>{title}</h3>`. Passar
  `title={C.receiptsTitle}` sob um heading já existente duplicava o texto.
  Mesma causa-raiz existia na ficha SC («Pedidos vinculados» e
  «Recebimentos») — defeito irmão provado, corrigido com o mesmo fix.
- **Comprador «—»:** `buyer_code` vem de `SC7.C7_COMPRA`
  (`build_purchase_order_detail_sql`, `include_origin_and_buyer=True`) →
  `_optional_text` → BFF `get_portal_purchase_order` pass-through → MFE.
  O campo chega íntegro; no PC 057175 `C7_COMPRA` está vazio no TOTVS,
  logo «—» é o fallback neutro correto — **ausência de dado, não defeito**.
  Nome do comprador: não existe contrato canônico de identidade de
  comprador (o `RequesterIdentityService` resolve apenas `requester` de
  SC). Exibição de nome exigiria evolução de contrato no owner —
  classificado **`TO_INVENTORY`**, sem lookup/endpoint/SQL novo nesta fatia.

### Correção

- Nova variante `SuppliesInlineEmptyState` em `suppliesUi.ts`
  (`emptyStateCardBemClasses`, `withTitle: false` → só `<p>` no card do
  kit). Nenhum componente compartilhado do `plugin-ui` alterado.
- PC: `receipts.length === 0` → `<SuppliesInlineEmptyState
  message={C.receiptsEmpty} />`; heading único mantido em ambos os estados.
- SC (defeito irmão provado): mesma troca nos estados vazios de
  «Pedidos vinculados» e «Recebimentos».
- **Erro latente de tipagem corrigido:** as seções SC passavam JSX em
  `SuppliesSectionCard.title` (contrato `title: string`); o Dockerfile só
  roda `vite build`, então `tsc -b` nunca validou essas linhas no deploy.
  Corrigido para o uso canônico: `title` string + `hint` = tooltip
  (`SP_HELP`); `ordersHint`/`receiptsHint` viraram strings mortas e foram
  removidas de `content.ts`. Visual preservado (um único «?» no título).

### Recebimentos parciais — validação

A tabela por item já cobre: NF, Série (`"—"` quando ausente), item NF,
quantidade, preço unit., valor, emissão e entrada; `formatQuantity`/
`formatMoneyBr`/`formatDatePtBr` retornam «—» para `null`/`NaN`. Nenhuma
soma/reconciliação de NF vs. `delivered_quantity` no MFE (guard
`receipts.reduce` no structural test). Distinção «Entregue» (baixa) ≠
notas fiscais preservada.

### Testes

- Structural PC: `SuppliesInlineEmptyState` presente, sem
  `<SuppliesEmptyState title={C.receiptsTitle}`, sem `receipts.reduce`.
- Structural SC: mesmo guard para `ordersTitle`/`receiptsTitle`.
- Resultados completos: ver relatório de execução (suite MFE, tsc,
  build, lint).

### Residuais

- Nome do comprador: `TO_INVENTORY` — depende de contrato canônico de
  identidade de comprador (owner: api-delpi/supplies-api).
- Smoke autenticado desta revisão: pendente conforme relatório.
