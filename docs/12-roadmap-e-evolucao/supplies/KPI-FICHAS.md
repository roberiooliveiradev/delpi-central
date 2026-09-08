# KPI-FICHAS — Portal Suprimentos

Legenda: `CONFIRMADO` · `PARCIAL` · `NECESSITA_VALIDACAO_FUNCIONAL` · `BLOQUEADO`.

Fórmulas abaixo vêm do help/código atuais. Não inventar regra. Owner de negócio ainda depende de homologação quando indicado.

## Regra transversal de escopo

**Consolidado nunca significa empresa inteira implicitamente.** No Portal, qualquer KPI consolidado deve representar somente a união das unidades efetivamente autorizadas ao usuário (`allowedUnits`).

Se uma fonte externa, como Strategic Indicators, só oferecer consolidado corporativo maior que o escopo do usuário, esse valor não pode ser exposto como autorizado sem uma forma canônica de recalcular/filtrar o mesmo recorte.

## Regra transversal de tempo

Cards lado a lado podem ter naturezas temporais diferentes e devem deixar isso visível:

| Tipo | Exemplo |
|---|---|
| Snapshot atual | valor de estoque, materiais críticos |
| Estado atual | SC abertas |
| Intervalo | OTD, CPV, savings |
| Competência | indicadores/metas SI quando aplicável |

A UI deve exibir período/competência ou indicação de “agora/snapshot” para não sugerir uma janela temporal única.

---

## KPI-OTD — Pontualidade de compras

| Campo | Conteúdo |
|---|---|
| ID | `KPI-OTD` |
| Nome | OTD compras |
| Objetivo | Medir % de linhas recebidas no prazo |
| Descrição | Universo: tipo MP ou código iniciando em `3019`; on-time = recebimento ≤ data prometida |
| Fórmula | `on_time_lines / eligible_lines × 100` |
| Numerador | Linhas elegíveis recebidas no prazo |
| Denominador | Linhas elegíveis recebidas no período |
| Fonte | api-delpi `get_supplies_otd`; meta SI `supplies-otd` |
| Filtros | branch, start_date, end_date, competência |
| Escopo filial | somente unidades autorizadas; consolidado = união dessas units |
| Natureza temporal | intervalo |
| Granularidade | % + evolução mensal + ranking |
| Status | **PARCIAL** — confirmar se BI atraso usa mesma regra |

---

## KPI-STOCK-VALUE — Valor de estoque

| Campo | Conteúdo |
|---|---|
| ID | `KPI-STOCK-VALUE` |
| Nome | Valor total do estoque |
| Objetivo | Expor valor SB9 no recorte |
| Fórmula | `Σ valor SB9` no filtro |
| Fonte | `get_supplies_stock_value`; SI `supplies-stock-value` |
| Filtros | branch, location |
| Escopo filial | somente allowedUnits |
| Natureza temporal | snapshot/competência conforme contrato da rota |
| Status | **PARCIAL** — modo histórico precisa respeitar documentação canônica |

---

## KPI-TURNOVER — Giro de estoque

| Campo | Conteúdo |
|---|---|
| ID | `KPI-TURNOVER` |
| Nome | Giro de estoque (vezes) |
| Objetivo | Indicador oficial em vezes |
| Fórmula | `CPV_total / stock_value`; meses é auxiliar separado |
| Fonte | `get_supplies_inventory_turnover`; SI `supplies-stock-turnover` |
| Escopo filial | somente allowedUnits |
| Natureza temporal | intervalo |
| Status | **CONFIRMADO** no help atual para “vezes” |

Não rotular meses de cobertura e giro em vezes como o mesmo indicador.

---

## KPI-CPV — Custo dos produtos vendidos

| Campo | Conteúdo |
|---|---|
| ID | `KPI-CPV` |
| Nome | CPV |
| Objetivo | Custo dos produtos vendidos vs meta |
| Fórmula | soma de movimentos classificados como CPV; `% ROL = CPV/ROL` quando aplicável |
| Fonte | `get_supplies_cpv`; SI `supplies-cpv` |
| Escopo filial | somente allowedUnits |
| Natureza temporal | intervalo/competência |
| Status | **PARCIAL** — classificação SQL não deve ser reespecificada aqui |

---

## KPI-SAVINGS — Economia em negociações

| Campo | Conteúdo |
|---|---|
| ID | `KPI-SAVINGS` |
| Nome | Economia em negociações |
| Objetivo | Somar economia lançada no IDD |
| Fórmula | soma dos lançamentos no recorte |
| Fonte | `get_supplies_negotiation_savings_summary`; meta SI `supplies-negotiation-savings` |
| Escopo filial | por unidade conforme origem; consolidado apenas allowedUnits |
| Natureza temporal | intervalo |
| Status | **PARCIAL** — app Sheets do PO ainda não confirmado no Core |

Meta canônica continua no SI; planilha não vira segunda fonte de meta.

---

## KPI-SC-OPEN — Solicitações pendentes

| Campo | Conteúdo |
|---|---|
| ID | `KPI-SC-OPEN` |
| Nome | SC pendentes |
| Objetivo | Volume de itens SC com saldo no escopo autorizado |
| Descrição | grão item; saldo `C1_QUANT - C1_QUJE`; exclusão lógica fora |
| Fonte | purchase-requests-api / api-delpi SC1 |
| Escopo | unit + CC fail-closed; `view-all` só amplia CC dentro das units |
| Natureza temporal | estado atual |
| Status | **CONFIRMADO** no contrato; aging buckets ainda necessitam validação |

---

## KPI-PO-LATE — Pedidos / linhas atrasadas

| Campo | Conteúdo |
|---|---|
| ID | `KPI-PO-LATE` |
| Nome | Pedidos atrasados |
| Objetivo | Exceção operacional de entrega |
| Fonte | `get_supplies_purchase_order_otd` / panel |
| Fórmula | não congelada até leitura/homologação do DTO |
| Escopo filial | somente allowedUnits |
| Natureza temporal | depende do contrato do panel; não inferir |
| Status | **NECESSITA_VALIDACAO_FUNCIONAL** |

---

## KPI-CRITICAL-MP — Materiais críticos

| Campo | Conteúdo |
|---|---|
| ID | `KPI-CRITICAL-MP` |
| Nome | Materiais críticos |
| Objetivo | Itens com saldo abaixo do ESTSEG |
| Fonte | `/supplies/safety-stock/summary` |
| Fórmula | COUNT/SUM conforme contrato canônico do safety-stock |
| Escopo filial | somente allowedUnits |
| Natureza temporal | snapshot atual |
| Status | **CONFIRMADO** no README/plugin atual |

---

## KPI-COVERAGE — Cobertura

| Campo | Conteúdo |
|---|---|
| ID | `KPI-COVERAGE` |
| Nome | Cobertura |
| Objetivo | ainda não congelado |
| Problema | meses de giro e cobertura ESTSEG são conceitos distintos |
| Status | **BLOQUEADO** no Overview até decisão funcional |

---

## KPI-PRICE-VAR — Variação de preço

| Campo | Conteúdo |
|---|---|
| ID | `KPI-PRICE-VAR` |
| Nome | Variação de preço |
| Objetivo | anomalia/comparação vs última compra ou média homologada |
| Fonte | purchase-price-history |
| Natureza temporal | série histórica |
| Status | **NECESSITA_VALIDACAO_FUNCIONAL** — P1, não Overview P0 |
