# SC/PC Detail Enrichment — Wireframes e Arquitetura de Informação

> Status: `DISCOVERY_COMPLETE` · `IMPLEMENTATION_NOT_AUTHORIZED` · `NO_CODE_CHANGE`
> Baseline: `f89e73376c` · Autor: Devin · Companheiro: `SC-PC-DETAIL-DATA-CONTRACT-MATRIX.md`

Proposta visual das fichas **Detalhe da SC** e **Detalhe do PC**, construída
**somente** sobre campos comprovados (ver matriz). Seções sem fonte comprovada
estão marcadas `〔FUTURO〕` — não fazem parte de nenhuma entrega autorizada.

## Componentes do kit reutilizados (inventário)

| Kit | Origem | Uso proposto |
|---|---|---|
| `SuppliesPageHero` + `highlights` | `suppliesUi.ts` (PageHero do plugin-ui) | hero com filial/identidades/datas/badge de situação |
| `SuppliesSectionCard` + `SuppliesSectionHintLabel` | `suppliesUi.ts` | cada bloco de conteúdo com ajuda contextual |
| `SuppliesStatusBadge` | `suppliesUi.ts` | situação (SC: 7 estágios; PC: late/on_time/no_date) |
| `SuppliesPersonIdentity` | `SuppliesDirectoryIdentity.tsx` | solicitante (nome+foto+link `/users/:userId`) |
| `SuppliesSupplierIdentity` | `SuppliesDirectoryIdentity.tsx` | fornecedor / fornecedor sugerido |
| `SuppliesEventsSection` | `suppliesUi.ts` — **já existe, sem consumidor em features** | timeline SC (`request_created`, `purchase_order_created`, `expected_delivery`, `receipt`) |
| `SuppliesEntityLink` | `suppliesUi.ts` | links SC↔PC nas duas direções |
| `SuppliesLoadingCard`, `SuppliesEmptyState`, `SuppliesStateBanner` | `suppliesUi.ts` | estados de interface |
| `SuppliesPagePath` | `suppliesUi.ts` | breadcrumb com retorno à lista preservando `?from=` |
| `SimpleKpiCard` (interativo opcional) | plugin-ui | cartões de totais **passivos** (sem onSelect na ficha) |
| Tabelas existentes das páginas | feature-local | itens, pedidos vinculados, recebimentos |

Nenhum componente novo é proposto para a fase A/B.

## Atual → Proposto (estrutura)

| Página | Hoje renderiza | Proposta (Fase A — zero contrato novo) |
|---|---|---|
| SC | hero: filial, nº, solicitante, data, estágio, nº itens + tabela de itens (item/produto/qtd/stage/CC-código) | + KPIs solicitado/pedido/recebido + aprovação + CCs com descrição + colunas UM, necessidade, qtd. pedida, saldo + seção Pedidos vinculados + timeline |
| PC | hero: filial, nº + por item: produto, fornecedor, status, comprador(código), SC origem, qtds, preço, valor aberto + tabela de recebimentos | + header agregado só com soma client-side dos itens **se aceito** (ou marcado `PLANNED`) + link SC origem + hierarquia de seções; alerta de atraso por item |

⚠️ Header agregado do PC (valor total, total recebido, situação geral): o produtor
não emite agregados — somá-los no MFE é cálculo de domínio no cliente.
**Recomendação: tratar como `PLANNED` (contrato de header na api-delpi), não quick win.**

## Wireframe — SC desktop (proposta Fase A)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Início › Solicitações de compra › SC 178764          [? ajuda]       │
├──────────────────────────────────────────────────────────────────────┤
│ SOLICITAÇÃO DE COMPRA 178764              [Situação: Aguardando rec.]│
│ ○ Filial 01 · Santa Catarina   👤 Maria Silva (solicitante)          │
│ ○ Abertura 12/05/2026          CC 4101 · Suprimentos (+1)            │
│ ○ Aprovada por J. Pereira em —   [badge aprovação]                   │
├────────────┬────────────┬────────────┬─────────────┬────────────────┤
│ Itens 4    │ Solicitado │ Em pedidos │ Recebido    │ Pedidos  2     │
│            │    420 un  │    300 un  │   120 un    │ atraso   6d ⚠  │
├──────────────────────────────────────────────────────────────────────┤
│ ITENS SOLICITADOS                                          [hint ?]  │
│ Item │ Produto           │ UM │ Qtd │ Necess. │ Pedida │ Pend. │ CC │
│ 0001 │ TRAFO 15kVA       │ UN │ 100 │ 20/06   │ 100    │ 0     │ 41 │
│ 0002 │ CABO 35mm         │ MT │ 200 │ 20/06   │ 150    │ 50 ⚠  │ 41 │
│  ... │ por linha: badge de stage + expansão com pedidos do item       │
├──────────────────────────────────────────────────────────────────────┤
│ PEDIDOS VINCULADOS                                         [hint ?]  │
│ PC 057175 item 01 │ Fornec. Eletro S.A. │ emit. 14/05 │ prev. 30/06  │
│   qtd 150 │ receb. 120 │ aberto 30 │ [Em atraso 6d] │ → abrir PC     │
│ PC 057190 item 03 │ Fornec. Cabos BR    │ emit. 18/05 │ prev. 10/07  │
├──────────────────────────────────────────────────────────────────────┤
│ RECEBIMENTOS (por pedido vinculado)                        [hint ?]  │
│ NF 1042-3 │ item PC 01 │ 12/06 entrada │ qtd 60 │ R$ 8.400,00        │
├──────────────────────────────────────────────────────────────────────┤
│ HISTÓRICO                                                            │
│ 12/05 SC criada → 14/05 PC 057175 → prev. 30/06 → 12/06 NF 1042-3    │
└──────────────────────────────────────────────────────────────────────┘
```

Responde: quem, quando, filial/CC, o quê, quanto, situação, aprovação,
pedidos vinculados, quanto comprado/recebido/pendente.
**Não responde (sem fonte):** próximo passo, dono da ação 〔FUTURO〕.

## Wireframe — SC mobile (empilhado)

```
┌──────────────────────────┐
│ ‹ SC 178764        [?]   │
│ Filial 01 · SC           │
│ Maria Silva · 12/05      │
│ [Aguardando recebimento] │
│ [Aprovada · J. Pereira]  │
├──────────────────────────┤
│ Solicitado 420 un        │
│ Em pedidos 300 un        │
│ Recebido  120 un         │
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
│   [Em atraso 6d] →       │
├──────────────────────────┤
│ HISTÓRICO (vertical)     │
└──────────────────────────┘
```

Tabela de itens vira cartões empilhados; pedidos/recebimentos viram listas
colapsáveis; timeline vira lista vertical (o `SuppliesEventsSection` já define
o comportamento responsivo do kit — não criar variante própria).

## Wireframe — PC desktop (proposta Fase A)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Início › Pedidos de compra › PC 057175                  [? ajuda]    │
├──────────────────────────────────────────────────────────────────────┤
│ PEDIDO DE COMPRA 057175                [⚠ Em atraso — pior item]     │
│ ○ Filial 01 · Santa Catarina   Emissão 14/05/2026                    │
│ ○ Eletro S.A. (loja 01)        Comprador: C7_COMPRA→nome 〔FUTURO〕  │
├────────────┬────────────┬────────────┬─────────────┬────────────────┤
│ Itens 3    │ Pedido     │ Entregue   │ Em aberto   │ Atraso         │
│            │ qtd        │ qtd        │ qtd + R$    │ máx. 6d   〔H〕 │
├──────────────────────────────────────────────────────────────────────┤
│ ITENS DO PEDIDO                                            [hint ?]  │
│ Item │ Produto │ Pedida │ Entregue │ Aberta │ Prev. entrega │ Status │
│ 01   │ CABO    │ 150    │ 120      │ 30     │ 30/06         │ ⚠ 6d   │
│      └ SC origem 178764/0002 →   ▼ Recebimentos (NF|série|dt|qtd|R$) │
│ 02   │ ...                                                       ok  │
├──────────────────────────────────────────────────────────────────────┤
│ CONDIÇÕES DO PEDIDO 〔FUTURO〕  C7_COND · C7_MOEDA · obs             │
│ HISTÓRICO DE ENTREGAS 〔FUTURO〕 alterações de prazo, ocorrências    │
└──────────────────────────────────────────────────────────────────────┘
```

## Wireframe — PC mobile

```
┌──────────────────────────┐
│ ‹ PC 057175        [?]   │
│ Filial 01 · 14/05/2026   │
│ Eletro S.A. (loja 01)    │
│ [Em atraso — 6d]         │
├──────────────────────────┤
│ Pedido   │ Entregue      │
│ Aberto qtd + R$          │
├──────────────────────────┤
│ ITENS                    │
│ ▸ 01 CABO 35mm           │
│   150 ped. · 120 ent.    │
│   aberta 30 · prev.30/06 │
│   SC 178764/0002 →       │
│   ▼ Recebimentos         │
└──────────────────────────┘
```

## Estados de interface (ambas as fichas)

| Estado | Comportamento proposto |
|---|---|
| loading | `SuppliesLoadingCard` por seção (hero primeiro, itens depois) — padrão já existente |
| 403 forbidden | `SuppliesStateBanner` de acesso negado — já implementado, preservar |
| 404 not found | `SuppliesEmptyState` + retorno à lista (`?from=`) — já implementado |
| PC entregue/residual | 404 com copy **distinta**: «Pedido não localizado ou já totalmente entregue» — decisão de copy a validar com PO |
| erro 5xx | banner + `SuppliesActionButton` retry — já implementado |
| partial (sem pedidos) | seção Pedidos vinculados → empty state «Nenhum pedido vinculado até o momento» |
| partial (item sem recebimentos) | «Sem recebimentos registrados» por item — já implementado no PC |
| partial (receipts ≠ delivered) | nota rodapé/hint «Baixa do pedido pode divergir das notas enquanto houver recebimento em processamento» |
| campo ausente | «—» ou omissão da linha (padrão atual); nunca 0 |

## Navegação, F5, ajuda

- Rotas canônicas existentes: `/purchase-requests/{branch}/{number}` e
  `/purchase-orders/{branch}/{number}` → links bidirecionais `SuppliesEntityLink`.
- Retorno à lista: `?from=` já existe; preservar nos novos links de seção.
- F5/deep link: sem estado em memória; seções colapsadas voltam ao default.
- Ajuda: nova `SP_HELP` por seção (itens, pedidos vinculados, recebimentos,
  histórico) + `purchaseRequestsColumnHelp.ts`/`purchaseOrdersColumnHelp.ts`
  para novas colunas + Manual + FAQ — **requisito obrigatório** (`feature-help-sync`)
  em qualquer fase futura de implementação.
- Teclado/foco: expansões com `aria-expanded`, links com foco visível — padrão do kit.
