# Portal Comercial — fichas de KPI (F0)

> **Status:** Onda A em validação (ago/2026) — C1 com baseline Minha DELPI + analogia de mercado  
> **Playbook:** [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 1.2 e § 10  
> **Homologação:** [KPI-HOMOLOGACAO-ONDA-A.md](./KPI-HOMOLOGACAO-ONDA-A.md) (após E2.S1) · [ATA-MAPA-NECESSIDADES.md](./ATA-MAPA-NECESSIDADES.md)  
> **Owner padrão (D1):** `Comercial — a confirmar (homologação)`

Legenda de status da ficha: `rascunho` · `em_validacao` · `aprovada` · `bloqueada`.

---

## Template (usar em cada ficha)

| Campo | Conteúdo |
|-------|----------|
| Código | KPI-xxx estável |
| Nome (pt-BR) | |
| Objetivo | |
| Fórmula (comportamento atual / proposta) | |
| Analogia de mercado | |
| Numerador / denominador | |
| Inclusões / exclusões | |
| Fonte | api-delpi `operationId` / SI / commercial-api |
| Checklist de homologação | perguntas ao Comercial |
| Owner | |
| Freshness | |
| Filtros válidos | filial, período, … |
| Escopo | own / team / branch / all |
| Versão da regra | v0 |
| Status | |

---

## KPI-ROL — Receita operacional líquida

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-ROL` |
| Nome | ROL |
| Objetivo | Medir o faturamento líquido do período para gestão comercial |
| **Fórmula — comportamento atual (código)** | `rol_with_ipi = VLR_VENDA − VLR_DEVOLUCAO` onde `VLR_VENDA = Σ(D2_TOTAL − D2_VALICM − D2_VALIMP5 − D2_VALIMP6)` em SD2 (competência `D2_EMISSAO`) e devoluções em SD1 (`D1_DTDIGIT`; CF `1201`/`2201` ou `D1_TIPO='D'`). `ipi_separated = 0` no SQL atual → `rol` ≡ `rol_with_ipi`. |
| **% meta** | `(rol / comparable_goal_SI) × 100` após enrich de metas (`commercial_rol` / goal SI) |
| **Meta no período (decisão ata alinhamento 2)** | **Soma** das metas **proporcionais por dia** no intervalo selecionado: para cada mês civil sobreposto, `(meta_mês / dias_do_mês) × dias_no_intervalo`; somar. **Não** usar média de metas mensais. Inclui mês parcial, YTD e intervalos custom. Implementação alvo: `strategic-indicators-api` (P0-META) — ver [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) §5 |
| Analogia de mercado | **Billings / receita faturada** no período (não é backlog; não é book-to-bill) |
| Numerador | Valor líquido de vendas (− impostos listados) menos devoluções no período |
| Denominador (meta) | Meta SI `comparable_goal` quando presente; **comportamento atual no código** ainda pode agregar por meses civis (a corrigir para proporcional diária); composer pode injetar placeholder `1.0` antes do enrich |
| Inclusões / exclusões (SQL) | Inclui TES com `F4_DUPLIC='S'` (padrão); exclui `D2_TIPO='D'`; CF `5911`/`6151` com exceções; remessa especial `5927` conforme regras SF4. Segmento WEG = cliente `000001`; novos negócios = não-WEG |
| Fonte | api-delpi `get_financial_rol`, `get_*_rol_target_pct`, `get_commercial_rol_series`; BFF commercial-api `/analytics/*`; SQL: `api-delpi/app/infrastructure/persistence/totvs/financial_repositories/financial_repository.py` |
| Freshness | Conforme cache/query TOTVS do período filtrado |
| Filtros válidos | `branch` / unidade, `start_date`, `end_date`, `customer_segment`, escopo carteira (via BFF) |
| Escopo | branch / all (+ membership no Portal) |
| Versão da regra | v0 — baseline código; **v1 (ata)** = proporcional diária (pendente P0-META) |
| Owner | Comercial — a confirmar (homologação) |
| Status | **em_validacao** |

### Checklist de homologação (KPI-ROL)

- [ ] Confirmar se impostos descontados (ICM / IMP5 / IMP6) são a definição oficial de «líquido»  
- [ ] Confirmar competência por `D2_EMISSAO` (vs outro campo)  
- [ ] Confirmar tratamento de devoluções e CFs especiais  
- [ ] Confirmar se IPI deve ser separado no futuro (`ipi_separated`)  
- [ ] Confirmar fonte e curva da meta SI  
- [ ] Homologar meta acumulada **proporcional diária** (ata alinhamento 2) vs média/meses inteiros  

---

## KPI-CARTEIRA — Carteira comercial

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-CARTEIRA` |
| Nome | Carteira |
| Objetivo | Expor o saldo de pedidos/compromissos comerciais em aberto (backlog), distinto da programação do PCP |
| **Fórmula — comportamento atual (código)** | `openValue = SUM(valor_aberto)` das linhas do escopo; também `openLineCount = COUNT(linhas)` via `FilterOpenOrdersByScopeService` → `summary.valor_total_aberto` / `total_linhas`. Fonte de linha: view/lista pedidos em aberto (SC5/SC6 / `VW_PEDIDOS_VENDA_ABERTOS_*`). |
| Semântica temporal | **Snapshot** («em aberto agora») — **não** filtra por MTD/YTD do Overview |
| Analogia de mercado | **Order backlog / order book** (comprometido, ainda não faturado como ROL) |
| Natureza financeira | Tipicamente **valor aberto de pedido** (pode ser base bruta) — **não** misturar com ROL líquido sem homologação |
| Inclusões / exclusões | Escopo membership / `seller_id` no BFF; linhas com saldo em aberto conforme view; cancelados/bloqueados conforme regra da view TOTVS (a confirmar na homologação) |
| Fonte | commercial-api open-orders BFF (`list_commercial_open_orders`) + summary; cockpit: `GET /analytics/open-portfolio-summary` (E4); **não** é programação PCP |
| Freshness | Cada consulta ao TOTVS/BFF |
| Filtros válidos | Escopo carteira / vendedor; unidade se o upstream aplicar; **período de faturamento não se aplica** |
| Escopo | own / team / membership |
| Versão da regra | v0 — baseline open-orders |
| Owner | Comercial — a confirmar (homologação) |
| Status | **em_validacao** |

### Checklist de homologação (KPI-CARTEIRA)

- [ ] Confirmar se `valor_aberto` é bruto ou líquido  
- [ ] Confirmar exclusão de bloqueados / cancelados / residuais  
- [ ] Confirmar se conta linhas, pedidos ou itens  
- [ ] Confirmar que **não** se apresenta programação PCP como carteira  

---

## KPI-ROL-CARTEIRA — ROL + carteira

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-ROL-CARTEIRA` |
| Nome | ROL e carteira (visão combinada) |
| Objetivo | Permitir leitura gerencial de **realizado (ROL)** e **backlog (carteira)** na mesma tela |
| **Fórmula — decisão engineering (até homologação)** | Exibir **lado a lado**. **Proibido** somar `ROL + openValue` automaticamente (naturezas diferentes: faturado líquido × aberto de pedido). |
| Analogia de mercado | Painel billings + backlog; **book-to-bill** é outro indicador (fora deste ciclo) |
| Fonte | `KPI-ROL` + `KPI-CARTEIRA` no Overview |
| Owner | Comercial — a confirmar (homologação) |
| Status | **em_validacao** · soma oficial **bloqueada** |

### Checklist de homologação (KPI-ROL-CARTEIRA)

- [ ] Manter lado a lado como padrão?  
- [ ] Se soma for desejada: definir base única (tudo líquido ou tudo bruto) e fórmula  
- [ ] Definir se book-to-bill entra em ciclo futuro  

---

## KPI-CARTEIRA-HORIZON — Carteira no tempo + gap vs meta

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-CARTEIRA-HORIZON` |
| Nome | Carteira no tempo (buckets por entrega) |
| Objetivo | Concentrar esforço: ver **onde** está o valor aberto (atraso / mês / futuro) e o **buraco vs meta ROL**, sem misturar naturezas |
| **Gap vs meta** | `gapValue = max(meta_SI − ROL_período, 0)` — mesma fonte do KPI ROL **principal** (matriz/filial). **Fora:** WEG e novos negócios neste card |
| **Buckets** | Agrupar `valor_aberto` por `data_entrega` (TZ `America/Sao_Paulo`): `overdue`, `current_month`, `next_1_3_months`, `later`, `undated` |
| Semântica temporal | Buckets = **snapshot** (como KPI-CARTEIRA); gap = **período** dos filtros Overview |
| Analogia de mercado | Time-phased order backlog (ERP) + gap-to-quota (CRM); **não** pipeline × win rate |
| **Proibido** | Somar `ROL + openValue`; win-rate em pedido aberto; rotular como PCP/OP; forecast F6 |
| Contexto UI | Mostrar `current_month.openValue` **ao lado** do gap (contexto), sem soma automática |
| Módulo canônico | `OpenOrdersHorizonBucketService` (commercial-api); MFE **não** reimplementa regra de data |
| Fonte | `GET /analytics/open-portfolio-horizon` (+ `deliveryHorizon` no envelope `GET /open-orders/`) |
| Escopo | Mesmo membership / `seller_id` do open-portfolio-summary |
| Status | **implementado_mvp** (homologação de limites de bucket ainda aberta) |

### Checklist de homologação (KPI-CARTEIRA-HORIZON)

- [ ] Confirmar limites dos buckets (mês+1…+3) com Comercial  
- [ ] Confirmar tratamento de `data_entrega` vazia (`undated`)  
- [ ] Confirmar disclaimer bruto/líquido alinhado a KPI-CARTEIRA  

---

## KPI-PORTFOLIO-SHARE — Share faturamento carteira ÷ empresa

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-PORTFOLIO-SHARE` |
| Nome | Share da carteira no faturamento da empresa |
| Objetivo | Mostrar quanto do ROL (faturado) do período a carteira/escopo atual representa vs. o consolidado da empresa |
| **Fórmula** | `sharePct = (portfolioRol / companyRol) × 100` no **mesmo** `start_date`/`end_date` do filtro |
| Numerador (`portfolioRol`) | ROL do escopo atual (membership / `seller_id`) — mesma regra `KPI-ROL` |
| Denominador (`companyRol`) | ROL consolidado **sem** filtro de carteira (empresa / filiais do filtro de unidade, se houver) |
| Analogia de mercado | Portfolio share of company billings (CRM/ERP cockpit) |
| Inclusões / exclusões | Mesmas do `KPI-ROL`; **não** usar `openValue` (carteira aberta) no numerador nem no denominador |
| **Proibido** | Misturar backlog (`KPI-CARTEIRA`) com share; somar ROL+carteira; expor denominador empresa a quem só tem `accounts.view` |
| RBAC (UI) | Card só com `analytics.view` **ou** `accounts.team.view` **ou** `seller-portfolios.manage`; demais usuários veem só faturamento do escopo (sem %) |
| Fonte | commercial-api `GET /analytics/portfolio-billing-share` → api-delpi ROL (série/agregado) |
| Freshness | Conforme cache/query TOTVS do período |
| Filtros válidos | `start_date`, `end_date`, `branch`/unidade, `seller_id`/carteira (só no numerador) |
| Escopo | Numerador: own / team / membership; denominador: all (empresa) |
| Versão da regra | v0 |
| Owner | Comercial — a confirmar (homologação) |
| Status | **rascunho** (implementação Portal — plano carteira comparativos) |

### Checklist de homologação (KPI-PORTFOLIO-SHARE)

- [ ] Confirmar que denominador = empresa toda (não «todas as carteiras ativas do Portal»)  
- [ ] Confirmar política: vendedor operacional **não** vê % empresa  
- [ ] Confirmar arredondamento (1 casa vs 0) e tratamento `companyRol = 0`  
- [ ] Confirmar se segmento WEG/NB entra no share ou só no Overview separado  

---

## KPI-HIT-RATE — Taxa de conversão / hit rate

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-HIT-RATE` |
| Nome | Hit rate / taxa de conversão |
| Objetivo | Medir conversão de ofertas (OV) no período, **preservando** a metodologia já usada no Portal |
| **Fórmula — comportamento atual (código)** | `sales_conversion_rate_pct = qtd_won / qtd_proposals × 100` (0 se denom=0). **Denominador:** COUNT de revisões em `AD1010` com `AD1_DATA` ∈ `[start,end]` (cada revisão conta). **Numerador:** OVs cuja **última** revisão tem `AD1_STATUS='9'` (Ganha) e data de aceite `COALESCE(AD1_DTASSI, AD1_DTFIM)` ∈ período — **cohort de aceite**, independente da data de abertura. |
| Analogia de mercado | **Win rate** CRM; atenção: Delpi usa ganhas÷abertas no período (cohorts distintos), não necessariamente ganhas÷(ganhas+perdidas) do mesmo cohort |
| Inclusões / exclusões | Ganha = só status `9` no cabeçalho AD1; **não** usa estágio `000013` nem `AIJ_STATUS`. Filtros: branch, segment, customer_codes |
| Fonte | api-delpi `get_sales_conversion_rate` (`GET /commercial/closing-rate`) + série `get_sales_conversion_rate_series` (`GET /commercial/closing-rate/series`); BFF `/analytics/closing-rate` e `/analytics/closing-rate/series`; doc: [comercial-taxa-conversao-estagios.md](../../../api-delpi/docs/api/comercial-taxa-conversao-estagios.md); repo: `SalesConversionRateRepository` |
| Freshness | Query no período filtrado |
| Filtros válidos | período, unidade, segmento, escopo clientes |
| Escopo | branch / all (+ membership) |
| Versão da regra | v0 — **não alterar** até homologação explícita |
| Owner | Comercial — a confirmar (homologação) |
| Status | **em_validacao** |

### Checklist de homologação (KPI-HIT-RATE)

- [ ] Confirmar que numerador (aceite) e denominador (abertura) em períodos cruzados é intencional  
- [ ] Confirmar tratamento de revisões (cada revisão no denom)  
- [ ] Confirmar exclusão de canceladas / perdidas do numerador (só status 9)  
- [ ] Documentar se no futuro migrará para ganhas÷fechadas do mesmo cohort  
- [ ] **Proibido** mudar SQL/regra neste ciclo de cockpit sem ata de mudança  

---

## KPI-OTD — On-time delivery

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-OTD` |
| Nome | Pontualidade (OTD) de pedido de venda |
| Objetivo | % de linhas elegíveis no prazo (`C6_ENTREG`) + insights operacionais no painel |
| Fórmula KPI | `sales_order_otd_pct = on_time_lines / total_lines × 100` — regras em `comercial-sales-order-otd.md` |
| Stats painel | `late_percentage`; `avg_late_days` / `p50_late_days` / `p90_late_days` (só linhas `late`, `days_diff` > 0) |
| Recorrência | Clientes com **≥2** linhas `late` no período — top 10 por `late_count` (desempate: soma `days_diff` DESC) |
| Top 10 | (1) piores atrasos = linhas `late` por `days_diff` DESC; (2) próximas promessas = abertas (`not is_invoiced`) por `promised_date` ASC |
| Tabela linhas | Server-side: `search`, `status`, `sort_by`/`sort_dir`, `page`/`page_size` via BFF commercial-api |
| Fonte | api-delpi `get_sales_order_otd` / `…/panel` / `…/series`; BFF `/analytics/sales-order-otd*` |
| Owner | Comercial + engenharia Portal |
| Status | **implementado_mvp** (painel enriquecido) |

---

## KPI-CLIENTE-ATIVO / NOVO / RECUPERADO

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-CLIENTE-ATIVO`, `KPI-CLIENTE-NOVO`, `KPI-CLIENTE-RECUPERADO` |
| Nome | Cliente ativo / novo / recuperado |
| Objetivo | Classificar base de clientes |
| Fórmula | Janelas de evento (faturamento vs pedido) — **a formalizar** |
| Fonte | parcial `get_new_clients_*` / `get_new_business_rol_pct` |
| Owner | a confirmar |
| Status | rascunho · **bloqueia** dor #7 completa |

---

## KPI-TICKET — Ticket médio

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-TICKET` |
| Nome | Ticket médio |
| Objetivo | Valor ÷ unidade de contagem |
| Fórmula | Unidade (NF, pedido, embarque, cliente) — **a confirmar** |
| Fonte | a criar |
| Owner | a confirmar |
| Status | rascunho · **bloqueada** até unidade definida |

---

## Dores P0 bloqueadas até ficha aprovada

| Dor (§ 1.2) | Motivo |
|-------------|--------|
| #2 (ticket / amostras no cockpit) | KPI-TICKET e amostras sem ficha |
| #4 (carteira consolidada × PCP) | Soma ROL+carteira e distinção PCP — baseline lado a lado em `em_validacao`; soma ainda bloqueada |
| #7 (ativo/novo/recuperado) | Janelas não formalizadas |

Engineering do cockpit Overview (MTD/YTD, card carteira **lado a lado**) usa o **baseline de código** acima enquanto as fichas permanecem `em_validacao`.
