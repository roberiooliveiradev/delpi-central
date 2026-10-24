# SC/PC Detail Enrichment — Wireframes e Arquitetura de Informação

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Data editorial: 2026-10-24 · v2 reconciliada P0.R1
> Companheiros: `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md` · `SC-PC-DETAIL-ENRICHMENT-P0.md`

Proposta visual das fichas **Detalhe da SC** e **Detalhe do PC**, construída
**somente** sobre campos comprovados. Seções sem fonte comprovada estão
marcadas `〔FUTURO〕` — não fazem parte de nenhuma entrega autorizada.

## Reconciliação P0.R1 aplicada a esta versão

1. **Sem KPI único de quantidade** — totais de `header` somam quantidades sem
   agrupar por UM e só sobre linhas autorizadas (P0.R1 §A). Hero usa contadores
   e situação, nunca «solicitado 420 un».
2. **«Acompanhamento»** em vez de «Histórico» — `timeline` é trilha derivada,
   não auditoria; `expected_delivery` é data planejada, exibida como marco
   distinto de ocorrência.
3. **404 neutro** — «não localizado entre os pedidos em aberto» (D1 opção A).
4. **Links SC↔PC com tratamento 403/404** neutro; chave composta `(filial, número)`.
5. **PC sem «dias de atraso»** — o contrato PC só tem `delivery_status`
   (`late`/`on_time`/`no_date`); `days_overdue` existe apenas nos pedidos
   enriquecidos do produtor **SC**.

## Componentes do kit reutilizados (inventário)

| Kit | Origem | Uso proposto |
|---|---|---|
| `SuppliesPageHero` + `highlights` | `suppliesUi.ts` (PageHero do plugin-ui) | hero com filial/identidades/datas/badge de situação |
| `SuppliesSectionCard` + `SuppliesSectionHintLabel` | `suppliesUi.ts` | blocos de conteúdo com ajuda contextual |
| `SuppliesStatusBadge` | `suppliesUi.ts` | situação (SC: 7 estágios; PC: late/on_time/no_date) |
| `SuppliesPersonIdentity` | `SuppliesDirectoryIdentity.tsx` | solicitante (nome+foto+link `/users/:userId`) |
| `SuppliesSupplierIdentity` | `SuppliesDirectoryIdentity.tsx` | fornecedor / fornecedor sugerido (rótulo «Sugerido») |
| `SuppliesEventsSection` | `suppliesUi.ts` — existe no kit, sem consumidor | seção «Acompanhamento» (eventos derivados) |
| `SuppliesEntityLink` | `suppliesUi.ts` | links SC↔PC nas duas direções (403/404 neutros) |
| `SuppliesLoadingCard`, `SuppliesEmptyState`, `SuppliesStateBanner` | `suppliesUi.ts` | estados de interface |
| `SuppliesPagePath` | `suppliesUi.ts` | breadcrumb + retorno à lista preservando `?from=` |
| `SimpleKpiCard` (passivo) | plugin-ui | contadores **não somáveis por UM** (itens, pedidos, recebimentos) — sem `onSelect` na ficha |

Nenhum componente novo é proposto para a Fase A.

## Atual → Proposto (Fase A — zero contrato novo)

| Página | Hoje | Fase A |
|---|---|---|
| SC | hero (filial, nº, solicitante, data, estágio, nº itens) + itens (item/produto/qtd/stage/CC-código) | + contadores seguros (pedidos, recebimentos, atraso ⚠) + aprovação c/ nome do aprovador + CCs c/ descrição + colunas UM, necessidade, qtd. pedida, saldo por item + seção Pedidos vinculados c/ recebimentos + «Acompanhamento» |
| PC | hero (filial, nº) + por item: produto, fornecedor, comprador(cód.), SC origem, qtds, preço, valor aberto, delivery_status + recebimentos | + alerta «Em atraso» derivado dos itens + link SC origem + hierarquia de seções + copy neutra de 404 (D1). **Sem header agregado** (contrato `PLANNED`) |

## Wireframe — SC desktop (Fase A, v2)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Início › Solicitações de compra › SC 178764            [? ajuda]     │
├──────────────────────────────────────────────────────────────────────┤
│ SOLICITAÇÃO DE COMPRA 178764             [Situação: Aguardando rec.] │
│ ○ Filial 01 · Santa Catarina   👤 Maria Silva (solicitante)          │
│ ○ Abertura 12/05/2026          CC 4101 · Suprimentos (+1)            │
│ ○ [Aprovada] · por J. Pereira                                        │
├────────────┬────────────┬────────────┬───────────────────────────────┤
│ Itens 4    │ Pedidos 2  │ Entradas 3 │ Atraso: 6d ⚠ (pior pedido)   │
│ visíveis   │ vinculados │ registradas│                              │
├──────────────────────────────────────────────────────────────────────┤
│ ITENS SOLICITADOS                                          [hint ?]  │
│ Item │ Produto          │ UM │ Solic. │ Necess. │ Pedida │ Pend. │CC│
│ 0001 │ TRAFO 15kVA      │ UN │ 100    │ 20/06   │ 100    │ 0     │41│
│ 0002 │ CABO 35mm        │ MT │ 200    │ 20/06   │ 150    │ 50 ⚠  │41│
│      ▼ por item (expansível): fornecedor sugerido · pedidos do item  │
├──────────────────────────────────────────────────────────────────────┤
│ PEDIDOS VINCULADOS                                         [hint ?]  │
│ PC 057175 it.01 │ Eletro S.A.  │ emit.14/05 prev.30/06 │ [Em atraso] │
│   pedida 150 · receb.120 · aberta 30                     → abrir PC  │
│ PC 057190 it.03 │ Cabos BR     │ emit.18/05 prev.10/07 │  no prazo   │
├──────────────────────────────────────────────────────────────────────┤
│ RECEBIMENTOS (por pedido vinculado)                        [hint ?]  │
│ NF 1042-3 │ PC 057175 it.01 │ entrada 12/06 │ qtd 60 │ R$ 8.400,00   │
├──────────────────────────────────────────────────────────────────────┤
│ ACOMPANHAMENTO                                           [hint ?]    │
│ ○ 12/05 SC criada ── ○ 14/05 PC 057175 criado                        │
│ ◇ prev. entrega 30/06 (planejada) ── ○ 12/06 NF 1042-3 entrada       │
│   hint: eventos derivados das datas de pedido e recebimento; não     │
│   inclui aprovações, alterações de prazo ou cancelamentos.           │
└──────────────────────────────────────────────────────────────────────┘
```

Indicadores do hero: **contadores e alerta** — nunca soma de quantidades
(UMs podem divergir e o total cobre só linhas autorizadas). `max_days_overdue`
é provado no header SC → pode exibir «atraso»; quando `has_overdue_order=false`
mostra «sem atraso».

## Wireframe — SC mobile (v2)

```
┌──────────────────────────┐
│ ‹ SC 178764        [?]   │
│ Filial 01 · SC           │
│ Maria Silva · 12/05      │
│ [Aguardando recebimento] │
│ [Aprovada · J. Pereira]  │
├──────────────────────────┤
│ Itens 4 · Pedidos 2      │
│ Entradas 3 · ⚠ atraso 6d │
├──────────────────────────┤
│ ITENS                    │
│ ▸ 0001 TRAFO 15kVA       │
│   100 UN · nec. 20/06    │
│   pedida 100 · pend. 0   │
│ ▸ 0002 CABO 35mm         │
│   200 MT · pend. 50 ⚠    │
├──────────────────────────┤
│ PEDIDOS VINCULADOS       │
│ ▸ PC 057175 · Eletro SA  │
│   [Em atraso] →          │
├──────────────────────────┤
│ ACOMPANHAMENTO (vert.)   │
└──────────────────────────┘
```

Ordem mobile: identidade → situação → solicitante → contadores → itens →
pendências → pedidos vinculados → recebimentos → acompanhamento.
Tabelas viram cartões; nenhuma rolagem horizontal.

## Wireframe — PC desktop (Fase A, v2)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Início › Pedidos de compra › PC 057175                  [? ajuda]    │
├──────────────────────────────────────────────────────────────────────┤
│ PEDIDO DE COMPRA 057175                     [⚠ Em atraso] 〔badge〕 │
│ ○ Filial 01 · Santa Catarina   Emissão 14/05/2026                    │
│ ○ Eletro S.A. (loja 01)        Comprador: código exibido/nome〔F〕   │
├──────────────────────────────────────────────────────────────────────┤
│ ITENS DO PEDIDO                                            [hint ?]  │
│ Item │ Produto │ Pedida │ Entregue │ Aberta │ Prev. entrega │ Status │
│ 01   │ CABO    │ 150    │ 120      │ 30     │ 30/06         │ ⚠ atras.│
│      └ SC origem 178764/0002 →   ▼ Recebimentos (NF|série|dt|qtd|R$) │
│ 02   │ ...                                                       ok  │
│      hint: «entregue» = baixa no pedido; notas registradas podem     │
│      divergir enquanto houver recebimento em processamento.          │
├──────────────────────────────────────────────────────────────────────┤
│ RESUMO DO PEDIDO 〔FUTURO〕  total pedido/recebido — exige contrato  │
│ CONDIÇÕES DO PEDIDO 〔FUTURO〕 C7_COND · C7_MOEDA · obs              │
└──────────────────────────────────────────────────────────────────────┘
```

Sem header agregado e sem «dias de atraso» — nenhum dos dois existe no
contrato PC. O badge «Em atraso» deriva do `delivery_status` dos itens
(apresentação, não cálculo de domínio).

## Wireframe — PC mobile (v2)

```
┌──────────────────────────┐
│ ‹ PC 057175        [?]   │
│ Filial 01 · 14/05/2026   │
│ Eletro S.A. (loja 01)    │
│ [Em atraso]              │
├──────────────────────────┤
│ ITENS                    │
│ ▸ 01 CABO 35mm           │
│   150 ped. · 120 ent.    │
│   aberta 30 · prev.30/06 │
│   SC 178764/0002 →       │
│   ▼ Recebimentos         │
│ ▸ 02 ...                 │
└──────────────────────────┘
```

## Estados de interface (ambas as fichas, v2)

| Estado | Comportamento proposto |
|---|---|
| loading | `SuppliesLoadingCard` por seção (hero primeiro) — padrão existente |
| 403 | `SuppliesStateBanner` «Conteúdo não disponível para o seu perfil» — neutro |
| 404 SC | «Solicitação não localizada ou fora do seu escopo de visualização» — escopo CC pode ocultar SC existente |
| 404 PC | **«Pedido não localizado entre os pedidos em aberto disponíveis para consulta.»** — D1 opção A; nunca afirmar «concluído» |
| erro 5xx | banner + `SuppliesActionButton` retry — existente |
| sem pedidos vinculados | «Nenhum pedido vinculado até o momento» — não afirmar «não existe pedido no ERP» (reconciliação) |
| item sem recebimentos | «Sem recebimentos registrados» por item — existente |
| receipts ≠ delivered | hint «Baixa do pedido pode divergir das notas enquanto houver recebimento em processamento» |
| link destino 403/404 | mesma copy neutra; retorno à ficha anterior preservado |
| `source_request_*` vazio | coluna/célula «—»; sem link |
| timeline vazia | seção omitida ou «Sem eventos registrados» — hint de lacunas sempre presente |
| campo ausente | «—» ou omissão; nunca 0 |

## Navegação, F5, ajuda

- Links bidirecionais `SuppliesEntityLink` com chave composta
  `(filial, número)`; item citado como contexto visual, não como rota.
- Retorno à lista: `?from=` preservado; sem links para rotas inexistentes.
- F5/deep link: sem estado em memória; seções colapsadas voltam ao default.
- Ajuda: nova `SP_HELP` por seção (itens, pedidos vinculados, recebimentos,
  acompanhamento — incluindo o disclaimer de eventos derivados) +
  `*ColumnHelp.ts` das novas colunas + Manual + FAQ (`feature-help-sync`,
  obrigatório em cada etapa de implementação).
- Teclado/foco: expansões `aria-expanded`, links foco visível — padrão do kit.


## Atualização pós-P0.R1 — decisão do PO D1/D2 (2026-10-24)

- **D1 APROVADA:** 404 PC usa «Pedido não localizado entre os pedidos em aberto disponíveis para consulta.»; não anunciar conclusão.
- **D2 APROVADA:** SC deve exibir aprovador junto ao estado de aprovação **se o produtor fornecer nome correspondente ao recurso**, fornecedor sugerido com rótulo inequívoco e **conta contábil na própria ficha principal**, dentro de uma seção contextual/administrativa por item quando a fonte for `lines[].account_code`. Não confundir conta contábil com centro de custo, não agrupar dados de diferentes linhas em um único cabeçalho sem contrato, não inferir valor faltante.
- Esta nota prevalece sobre o wireframe anterior onde conta contábil foi excluída. A distribuição visual definitiva é implementada em fatias posteriores; esta atualização **não representa UI entregue**.
