# KPI-FICHAS — Portal Suprimentos

Legenda de status: `CONFIRMADO` · `PARCIAL` · `NECESSITA_VALIDACAO_FUNCIONAL` · `BLOQUEADO`

Fórmulas abaixo vêm do **help e código atuais** (`helpTooltips.ts`, SI catalog). Não inventar. Owner padrão: Suprimentos — homologação pendente.

---

## KPI-OTD — Pontualidade de compras

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-OTD` |
| Nome | OTD compras |
| Objetivo | Medir % de linhas recebidas no prazo |
| Descrição | Universo: tipo MP **ou** código iniciando em `3019`. On-time = recebimento ≤ data prometida |
| Fórmula | `on_time_lines / eligible_lines × 100` |
| Numerador | Linhas elegíveis recebidas no prazo |
| Denominador | Linhas elegíveis recebidas no período |
| Fonte | api-delpi `get_supplies_otd`; meta SI `supplies-otd` |
| Tabela/endpoint | `/supplies/otd` · também `purchase-order-otd*` |
| Filtros | branch, start_date, end_date, competência |
| Exclusões | Fora de MP e fora de 3019* (help atual) |
| Filial | Consolidado SI quando branch vazio |
| Período | Intervalo filtrado |
| Granularidade | % + evolução mensal + ranking atrasos |
| Owner | api-delpi (regra) · SI (meta) |
| Consumidores | dashboard-supplies/otd · SI · futuro Overview |
| Disponibilidade | Produção |
| Status | **PARCIAL** — confirmar se BI atraso usa a mesma regra |

---

## KPI-STOCK-VALUE — Valor de estoque

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-STOCK-VALUE` |
| Nome | Valor total do estoque |
| Objetivo | Expor valor (SB9) no recorte |
| Descrição | Help: valor total no recorte de unidade e localização |
| Fórmula | `Σ valor SB9` no filtro |
| Numerador | Valor |
| Denominador | n/a (nível) |
| Fonte | `get_supplies_stock_value` · SI `supplies-stock-value` |
| Tabela/endpoint | `/supplies/stock-value` · TV `supplies_stock_value` |
| Filtros | branch, location |
| Exclusões | Não documentadas no help — **não inventar** |
| Filial | Recorte ou consolidado SI |
| Período | Snapshot / competência conforme rota |
| Granularidade | Total + por localização + por unidade |
| Owner | api-delpi |
| Consumidores | dashboard `/stock` · SI · TV |
| Disponibilidade | Produção |
| Status | **PARCIAL** — modo híbrido histórico documentado em `supplies-estoque-historico.md` |

---

## KPI-TURNOVER — Giro de estoque

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-TURNOVER` |
| Nome | Giro de estoque (vezes) |
| Objetivo | Indicador oficial IDD/SI em **vezes** |
| Descrição | Auxiliar em meses = estoque ÷ CPV médio mensal |
| Fórmula | `CPV_total / stock_value` (vezes); meses = `stock / CPV_mensal_médio` |
| Numerador | CPV do período |
| Denominador | Valor de estoque |
| Fonte | `get_supplies_inventory_turnover` · SI `supplies-stock-turnover` |
| Tabela/endpoint | `/supplies/inventory-turnover` |
| Filtros | branch, período |
| Exclusões | — |
| Filial | Consolidado SI possível |
| Período | Intervalo |
| Granularidade | Vezes (oficial) + meses (auxiliar) |
| Owner | api-delpi |
| Consumidores | dashboard `/inventory-turnover` · SI |
| Disponibilidade | Produção |
| Status | **CONFIRMADO** no help do MFE (oficial = vezes) |

---

## KPI-CPV — Custo dos produtos vendidos

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-CPV` |
| Nome | CPV |
| Objetivo | Custo dos produtos vendidos vs meta |
| Descrição | Movimentos SD3 classificados como CPV; % ROL no mesmo período |
| Fórmula | Soma movimentos CPV; `CPV/ROL` |
| Numerador | CPV; CPV (para %) |
| Denominador | n/a; ROL mesmo período |
| Fonte | `get_supplies_cpv` · SI `supplies-cpv` |
| Tabela/endpoint | `/supplies/cpv` |
| Filtros | branch, período, competência |
| Exclusões | Só movimentos classificados CPV |
| Filial | Consolidado SI |
| Período | Intervalo |
| Granularidade | Total, % ROL, por CFOP, por TM |
| Owner | api-delpi |
| Consumidores | dashboard `/cpv` · SI |
| Disponibilidade | Produção |
| Status | **PARCIAL** — classificação CPV no SQL: não reespecificar aqui; homologar com Suprimentos |

---

## KPI-SAVINGS — Economia em negociações

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-SAVINGS` |
| Nome | Economia em negociações |
| Objetivo | Somar economia lançada no IDD |
| Descrição | **Não** é tabela TOTVS. Planilha IDD via composer |
| Fórmula | Soma lançamentos no recorte |
| Numerador | Economia R$ |
| Denominador | n/a |
| Fonte | `get_supplies_negotiation_savings_summary` · SI `supplies-negotiation-savings` |
| Tabela/endpoint | `/supplies/negotiation-savings/summary` |
| Filtros | unidade, período |
| Exclusões | Lançamentos fora da planilha |
| Filial | Por unidade na planilha |
| Período | Intervalo |
| Granularidade | Total + qtd lançamentos + por unidade |
| Owner | Planilha (lançamento) · api-delpi (leitura) · SI (meta) |
| Consumidores | dashboard `/negotiation-savings` |
| Disponibilidade | Produção (depende `SUPPLIES_IDD_SHEET_ID`) |
| Status | **PARCIAL** — app Sheets do PO sem perm no git |

---

## KPI-SC-OPEN — Solicitações pendentes

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-SC-OPEN` |
| Nome | SC pendentes |
| Objetivo | Worklist: volume de itens SC com saldo |
| Descrição | Grão item; saldo `C1_QUANT - C1_QUJE`; exclusão lógica fora |
| Fórmula | `COUNT` linhas no escopo com saldo > 0 (e filtros de estágio) |
| Numerador | Linhas |
| Denominador | n/a |
| Fonte | purchase-requests-api lista / `list_supplies_purchase_request_lines` |
| Tabela/endpoint | SC1 via api-delpi |
| Filtros | branch obrigatório, CC, datas, estágio |
| Exclusões | `D_E_L_E_T_`; resíduo ≠ cancelado |
| Filial | Unit perm |
| Período | Datas da SC |
| Granularidade | Contagem / aging P0 |
| Owner | contrato Fase 0.2 |
| Consumidores | MFE purchase-requests · futuro Home |
| Disponibilidade | Produção |
| Status | **CONFIRMADO** no contrato; aging buckets = **NECESSITA_VALIDACAO_FUNCIONAL** |

---

## KPI-PO-LATE — Pedidos / linhas atrasadas

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-PO-LATE` |
| Nome | Pedidos atrasados |
| Objetivo | Exceção operacional de entrega |
| Descrição | Preferir `get_supplies_purchase_order_otd` / panel (existe, sem MFE) |
| Fórmula | Contagem/valor linhas late do panel — **não inventar** até ler payload |
| Numerador | A confirmar no DTO |
| Denominador | A confirmar |
| Fonte | `/supplies/purchase-order-otd/panel` |
| Tabela/endpoint | SC7/SD1 conforme SQL da rota |
| Filtros | branch, período |
| Exclusões | A ler no use case E9.S1 |
| Filial | Unit |
| Período | — |
| Granularidade | Panel |
| Owner | api-delpi |
| Consumidores | futuro WF-07 |
| Disponibilidade | API sim / UI não |
| Status | **NECESSITA_VALIDACAO_FUNCIONAL** (ler DTO antes do Overview) |

---

## KPI-CRITICAL-MP — Materiais críticos (déficit ESTSEG)

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-CRITICAL-MP` |
| Nome | Materiais críticos |
| Objetivo | Itens com saldo abaixo do ESTSEG |
| Descrição | Déficit físico: saldo 01+98+99 × ESTSEG (README ESTSEG) |
| Fórmula | COUNT/SUM déficit conforme `get_supplies_safety_stock_summary` |
| Numerador | Itens ou qty em déficit |
| Denominador | n/a |
| Fonte | `/supplies/safety-stock/summary` · TV `supplies_stock_alert` |
| Tabela/endpoint | SB2/SBZ |
| Filtros | filial, grupo, situação |
| Exclusões | SC1 abertas **não** entram na projeção (README) |
| Filial | filial-01/02 |
| Período | Snapshot |
| Granularidade | KPIs + tabela |
| Owner | api-delpi ESTSEG |
| Consumidores | estoque-seguranca · TV · futuro Home |
| Disponibilidade | Produção |
| Status | **CONFIRMADO** no README do plugin |

---

## KPI-COVERAGE — Cobertura (hipótese de Overview)

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-COVERAGE` |
| Nome | Cobertura |
| Objetivo | Meses ou dias de cobertura |
| Fórmula | Já existe auxiliar de giro em **meses**. Cobertura ESTSEG (SC7/SD4) é outra coisa |
| Status | **BLOQUEADO** no Overview até o PO escolher **uma** definição. Não mostrar os dois como o mesmo KPI |
| Fonte | — |

---

## KPI-PRICE-VAR — Variação de preço

| Campo | Conteúdo |
|-------|----------|
| ID | `KPI-PRICE-VAR` |
| Nome | Variação de preço |
| Objetivo | Anomalia vs última compra / média |
| Fonte | `get_product_purchase_price_history` / safety-stock price-history |
| Status | **NECESSITA_VALIDACAO_FUNCIONAL** — P1, não Overview P0 |
