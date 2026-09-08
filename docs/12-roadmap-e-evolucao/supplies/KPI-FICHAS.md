# KPI-FICHAS — Portal Suprimentos

Legenda: `CONFIRMADO` · `PARCIAL` · `NECESSITA_VALIDACAO_FUNCIONAL` · `BLOQUEADO`.

Fórmulas abaixo vêm do help/código atuais. Não inventar regra.

## E1.S3 — Freeze Overview P0 (2026-09-08)

| Campo | Valor |
|---|---|
| Owner de negócio | **Suprimentos** (assinatura nominal pendente; freeze técnico por código/help) |
| P-12 | FECHADO — owner = área Suprimentos; nome da pessoa fica na § Assinatura quando o PO assinar |
| P-08 Cobertura | **FECHADO** — permanece **fora** do Overview P0 (`BLOQUEADO`); não misturar meses de giro com cobertura ESTSEG |
| Conjunto Overview P0 | **7 KPIs:** OTD, STOCK-VALUE, TURNOVER, CPV, SAVINGS, SC-OPEN, CRITICAL-MP |
| Fora do Overview P0 | KPI-PO-LATE (aguarda DTO/E7.S1), KPI-COVERAGE (P-08), KPI-PRICE-VAR (P1) |

Nenhuma ficha do conjunto P0 acima fica em `NECESSITA_VALIDACAO_FUNCIONAL`. Residuais de paridade com BIs externos (P-03/P-07) **não** bloqueiam o Overview nativo.

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO** (help/código); comparação com BI Atraso SC = P-03 (não bloqueia Overview) |

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO** — modo histórico segue contrato da rota api-delpi |

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO** |

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO** — classificação SQL permanece ownership da api-delpi |

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO** (fórmula API); destino do app Sheets = P-07 (não bloqueia card Overview) |

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO**; aging buckets = P-09 (não Overview) |

---

## KPI-PO-LATE — Pedidos / linhas atrasadas

| Campo | Conteúdo |
|---|---|
| ID | `KPI-PO-LATE` |
| Nome | Pedidos atrasados |
| Objetivo | Exceção operacional de entrega |
| Fonte | `get_supplies_purchase_order_otd` / panel |
| Fórmula | não congelada até leitura/homologação do DTO (E7.S1) |
| Escopo filial | somente allowedUnits |
| Natureza temporal | depende do contrato do panel; não inferir |
| Owner | Suprimentos |
| Overview P0 | **não** até E7.S1 |
| Status | **BLOQUEADO** no Overview P0; permanece elegível para Home/worklist após E7 |

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
| Owner | Suprimentos |
| Overview P0 | sim |
| Status | **CONFIRMADO** |

---

## KPI-COVERAGE — Cobertura

| Campo | Conteúdo |
|---|---|
| ID | `KPI-COVERAGE` |
| Nome | Cobertura |
| Objetivo | ainda não congelado |
| Problema | meses de giro e cobertura ESTSEG são conceitos distintos |
| Decisão E1.S3 (P-08) | **fora do Overview P0**; não exibir card até decisão funcional explícita do owner |
| Owner | Suprimentos |
| Overview P0 | não |
| Status | **BLOQUEADO** |

---

## KPI-PRICE-VAR — Variação de preço

| Campo | Conteúdo |
|---|---|
| ID | `KPI-PRICE-VAR` |
| Nome | Variação de preço |
| Objetivo | anomalia/comparação vs última compra ou média homologada |
| Fonte | purchase-price-history |
| Natureza temporal | série histórica |
| Owner | Suprimentos |
| Overview P0 | não |
| Status | **NECESSITA_VALIDACAO_FUNCIONAL** — P1, não Overview P0 |

---

## Assinatura E1.S3

| Item | Data | Owner Suprimentos | Evidência |
|---|---|---|---|
| Freeze técnico Overview P0 (7 KPIs) | 2026-09-08 | área Suprimentos (nominal pendente) | help/código + esta ficha |
| Aceite nominal PO | | | |
