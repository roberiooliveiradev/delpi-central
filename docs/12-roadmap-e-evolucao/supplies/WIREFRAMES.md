# WIREFRAMES — Portal Suprimentos

Shell comum (desktop / tablet / mobile ≤768 / light / dark):

```text
┌─ .dashboard-supplies-portal ─────────────────────────────────┐
│ TopBar  Portal Suprimentos          [Ajuda] [Ctrl+K] [ações] │
│ UnderlineNav  (caps)                                         │
│ PagePath (internas)                                          │
├──────────────────────────────────────────────────────────────┤
│ conteúdo                                                     │
│ loading: LoadingActivityCard · empty · error · 403           │
└──────────────────────────────────────────────────────────────┘
```

Touch ≥44×44. Tabelas ≤768px → cards. Gráficos responsivos.

Matriz rota × WF: ver [DESIGN-IA](./DESIGN-IA-SUPRIMENTOS.md) § 2.

**RBAC nos wireframes:** o campo Permission é só o **eixo A**. Dado TOTVS exige também `supplies.unit.filial-{TOTVS}` ([ADR-006](./adr/ADR-006-unit-permissions.md)). O seletor de filial lista apenas `allowedUnits` — não há tela “versão SC” e “versão ES”.

---

## WF-01 Início

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Ação e descoberta — não BI |
| Persona | Todas com `supplies.access` |
| Rota | `/apps/supplies` |
| Permission | `supplies.access` (alias: qualquer legado que abra o portal na E3) |
| Fonte | BFF `/home/attention` + catálogo de rotas + Core favoritos |
| Filtros | filial (default preferência) |
| KPIs | chips compactos: SC pendentes, atrasos, OTD, críticos — **só se cap** |
| Tabelas | não |
| Ações | buscar, abrir card, palette |
| Drilldowns | cada card → WF destino |
| Empty | «Nada na sua fila» + atalhos |
| Loading | skeleton chips + cards |
| Error | banner retry |
| 403 | sem access — portal não monta o app |
| Responsividade | cards 1 col mobile |
| Light/dark | tokens `--sp-*` |
| Ajuda | O que é Início vs Visão geral |

```text
┌─────────────────────────────────────────────────────────────┐
│ Bom dia, <nome>                          [filial ▾] [ações] │
│ [SC pendentes] [Pedidos atrasados] [OTD] [Críticos]         │
│ Atenção  AlertQueue                                         │
│   • fornecedor X atrasado                                   │
│   • material Y abaixo ESTSEG                                │
│   • SC Z aguardando ação                                    │
│ 🔎 CatalogSearchBar  Buscar no Portal Suprimentos…          │
│ Favoritos  HubChipRow     Recentes  HubChipRow              │
│ Compras     SectionRouteCard × N                            │
│ Fornecedores / Estoques / Gestão  (caps)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## WF-02 Visão Geral

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Cockpit 6–8 indicadores + tendência + exceções |
| Persona | Analista / gestor (`analytics.view`) |
| Rota | `/overview` |
| Permission | `supplies.analytics.view` |
| Fonte | `/analytics/overview` = api-delpi + SI |
| Filtros | período, competência, filial (consolidado se vazio) |
| KPIs | OTD, valor estoque, giro vezes, CPV, savings, SC pendentes, atrasos, críticos — omitir KPI-COVERAGE até P-08 |
| Tabelas | top exceções (5–10 linhas) |
| Ações | export P1 |
| Drilldowns | KPI → WF-11/15/18/04/07/16 |
| Empty | período sem movimento |
| Loading | KPI skeletons |
| Error / 403 | sem analytics |
| Responsividade | KPI 2×2 mobile |
| Ajuda | cada KPI = tooltip da ficha |

Não é dashboard de 25 KPIs. Sem worklist completa.

---

## WF-03 Minhas Atividades

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Worklist pessoal |
| Persona | Comprador / solicitante |
| Rota | `/my-tasks` |
| Permission | `supplies.access` |
| Fonte | composição TOTVS + `supply_tasks` |
| Filtros | tipo, status, filial |
| KPIs | abertas / vencidas |
| Tabelas | WorklistItem |
| Ações | concluir, criar follow-up |
| Drilldowns | ref → 360 / SC / PC |
| Empty | «Fila limpa» |
| Loading / Error / 403 | padrão |
| Ajuda | o que é tarefa vs dado TOTVS |

---

## WF-04 Solicitações de Compras

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Paridade do MFE purchase-requests |
| Persona | Solicitante / comprador |
| Rota | `/purchase-requests` |
| Permission | `purchase-requests.view` + unit |
| Fonte | PR-api C1 |
| Filtros | contrato 0.2 (branch obrigatório, datas, nº, solicitante, CC, produto, fornecedor, pedido, estágio) |
| KPIs | contagem no escopo |
| Tabelas | linhas item; modal detalhe |
| Ações | export se cap; abrir PC/NF |
| Drilldowns | produto 360, fornecedor 360 |
| Empty | fail-closed = empty honesto «sem escopo» ≠ erro |
| 403 | filial |
| Ajuda | resíduo, view-all, CC |

---

## WF-05 Pedidos de Compra

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Lista operacional de PC (hoje sem MFE) |
| Persona | Comprador |
| Rota | `/purchase-orders` |
| Permission | `purchase-orders.view` + unit |
| Fonte | `purchase-order-otd` / panel |
| Filtros | branch, datas, fornecedor, status atraso |
| KPIs | abertos / late |
| Tabelas | linhas PC |
| Ações | abrir WF-06 |
| Empty / 403 | padrão |
| Ajuda | PC ≠ SC; número reutilizado entre filiais |

---

## WF-06 Detalhe do Pedido

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Ficha PC: itens, prometida, recebimentos, SC origem |
| Persona | Comprador |
| Rota | `/purchase-orders/:branch/:number` |
| Permission | purchase-orders.view |
| Fonte | panel + linked receipts |
| Filtros | — |
| Tabelas | itens + SD1 |
| Ações | follow-up; deep link NF/frete |
| 404 | PC inexistente na filial |
| Ajuda | D1_ITEMPC |

---

## WF-07 Entregas / Atrasos

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Exceções de entrega |
| Persona | Comprador |
| Rota | `/deliveries` |
| Permission | purchase-orders.view |
| Fonte | OTD late + panel |
| Filtros | filial, período, fornecedor |
| KPIs | late lines, ranking |
| Tabelas | atrasos |
| Drilldowns | WF-06, WF-10 |
| Ajuda | relação com BI atraso (P-03) |

---

## WF-08 Importações

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Jornada importação **se** dump Core/TOTVS existir |
| Persona | Analista |
| Rota | `/imports` |
| Permission | cap futura **não** `importados.access` copiado |
| Fonte | BLOQUEADO até P-05 |
| Empty | «Em homologação — use o app atual se disponível» |
| Ajuda | coexistência |

---

## WF-09 Fornecedores

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Busca/lista SA2 no recorte |
| Persona | Comprador |
| Rota | `/suppliers` |
| Permission | suppliers.view |
| Fonte | busca produto/fornecedor api-delpi (reuso; gap = search SA2) |
| Filtros | filial, texto, CNPJ |
| Tabelas | código, loja, nome, OTD chip se disponível |
| Ações | abrir 360 |
| Ajuda | loja TOTVS |

---

## WF-10 Fornecedor 360

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Uma ficha, vários owners |
| Persona | Comprador / analista |
| Rota | `/suppliers/:code/:store` |
| Permission | suppliers.view |
| Fonte | ver tabela abaixo |
| Filtros | filial de contexto |
| KPIs | OTD, volume, atrasos abertos |
| Tabelas | produtos, PCs, entregas, inspeções (se cap qualidade) |
| Ações | nota interna, tarefa, deep link inspeções/frete |
| Ajuda | o que é TOTVS vs nota Delpi |

| Bloco | Owner | Fonte |
|-------|-------|-------|
| Identificação, CNPJ, loja | api-delpi | SA2 |
| Contatos | TOTVS se campo existir; senão omitir | — |
| Produtos / part numbers | api-delpi | SA5 |
| Pedidos abertos / entregas | api-delpi | SC7 / OTD |
| Histórico preço / últimas compras | api-delpi | SD1 / price-history |
| OTD / lead time | api-delpi | OTD + BZ_PE (P1) |
| Volume / savings | DERIVAVEL / Sheets | |
| Qualidade | Qualidade HTTP | inspecoes pendentes/histórico |
| Notas / ações | supplies-api | supplier_notes / tasks |

Não duplicar ranking de inspeção.

---

## WF-11 OTD Fornecedores

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Paridade página OTD do dashboard |
| Persona | Analista / comprador com analytics ou PO view |
| Rota | `/suppliers/otd` |
| Permission | analytics.view **ou** purchase-orders.view |
| Fonte | `get_supplies_otd` |
| Filtros | iguais dashboard |
| KPIs | % OTD, on-time, late, meta SI |
| Tabelas | ranking lateSuppliers + amostra |
| Charts | evolução mensal |
| Ajuda | universo MP/3019 |

---

## WF-12 Produtos / Matérias-primas

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Busca SB1 |
| Persona | Comprador |
| Rota | `/products` |
| Permission | products.view |
| Fonte | `search_products` / part-number |
| Filtros | texto, tipo/grupo |
| Tabelas | código, desc, UM |
| Ações | abrir 360 |

---

## WF-13 Produto / MP 360

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Unir fragmentação item |
| Persona | Comprador |
| Rota | `/products/:code` |
| Permission | products.view |
| Fonte | composition: stock, ESTSEG, parents, suppliers, last-purchase, purchases, SC abertas, PCs |
| KPIs | saldo, ESTSEG, déficit, cobertura SC7/SD4 |
| Abas/seções | cadastro · estoque · onde usado · fornecedores · preços · documentos SC/PC |
| Ações | simulação consumo (deep WF-17) |
| Ajuda | SC1 não entra na projeção ESTSEG |

Resolve: onde-usado + estoque + ESTSEG + última compra + histórico + fornecedores **numa jornada**.

---

## WF-14 Onde o Item é Usado

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Hierarquia pais |
| Persona | Comprador |
| Rota | `/products/:code/where-used` |
| Permission | products.view |
| Fonte | `get_product_parents` |
| Tabelas | árvore/lista pais |
| Empty | sem estrutura |
| Ajuda | ≠ BI até P-01 |

---

## WF-15 Controle de Estoques

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Valor + saldos (não ESTSEG) |
| Persona | Analista / comprador inventory |
| Rota | `/inventory` |
| Permission | inventory.view ou analytics.view |
| Fonte | stock-value + stock-balances |
| Filtros | branch, location |
| KPIs | valor, qty, locais, médio |
| Charts | por localização / unidade |
| Tabelas | balances items |
| Ajuda | diferença vs WF-16 e vs BI SC |

---

## WF-16 Estoque de Segurança

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Paridade monitoramento ESTSEG |
| Persona | Compras / planejamento |
| Rota | `/safety-stock` |
| Permission | inventory.view + unit |
| Fonte | safety-stock filters/summary/items/details |
| Filtros | filial, grupo, UM, situação, busca |
| KPIs | déficit por unidade |
| Tabelas | itens; modal extrato |
| Ações | export; SC1 toggle; fornecedores |
| Ajuda | README ESTSEG |

---

## WF-17 Análise de Consumo

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Simulação ESTSEG leitura |
| Persona | Analista |
| Rota | `/safety-stock/consumption-analysis` |
| Permission | inventory.view |
| Fonte | consumption-analysis \* |
| Filtros | iguais plugin |
| KPIs | distribuição vs BZ_PE |
| Tabelas | comparativo + série item |
| Ajuda | não grava Protheus; alias legado `/analise-consumo` |

---

## WF-18 Savings / Negociações

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Paridade negotiation-savings |
| Persona | Analista |
| Rota | `/negotiations` |
| Permission | negotiations.view ou analytics.view |
| Fonte | Sheets via api-delpi + meta SI |
| Filtros | unidade, período |
| KPIs | total, lançamentos |
| Charts | por unidade |
| Ajuda | planilha é origem do lançamento |

---

## WF-19 Histórico de Preços

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Série de preço item×fornecedor |
| Persona | Comprador |
| Rota | embebido no 360 + `/products/:code/price-history` |
| Permission | products.view |
| Fonte | purchase-price-history (produto e/ou safety-stock) |
| Charts | 12 meses |
| Ajuda | última compra ≠ média |

---

## WF-20 Indicadores

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Gestão: KPIs + link SI |
| Persona | Gestor |
| Rota | `/indicators` |
| Permission | analytics.view |
| Fonte | mesmos do Overview + deep SI |
| Ações | DEEP_LINK MFE strategic-indicators |
| Ajuda | Portal lê; SI cadastra meta |

---

## WF-21 Administração

| Campo | Conteúdo |
|-------|----------|
| Objetivo | Mapping Protheus, escopos CC, settings, auditoria funcional |
| Persona | Admin |
| Rota | `/administration` |
| Permission | `supplies.manage` |
| Fonte | PR-api admin C1; portal_settings; notes não |
| Tabelas | mappings, scopes |
| Ações | CRUD escopo; verificar mapping |
| 403 | sem manage |
| Ajuda | fail-closed; filial |

---

## Mobile — tabelas (todas WF com grid)

1. Colunas essenciais visíveis; demais em detalhe.
2. `DataRecordCard` ou row expand.
3. Filtros em sheet host-contained, não overlay de sidebar.
4. Export pode ficar no menu overflow.
