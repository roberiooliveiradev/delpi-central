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
