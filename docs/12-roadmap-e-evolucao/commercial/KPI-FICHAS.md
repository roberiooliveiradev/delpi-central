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
| Analogia de mercado | **Billings / receita faturada** no período (não é backlog; não é book-to-bill) |
| Numerador | Valor líquido de vendas (− impostos listados) menos devoluções no período |
| Denominador (meta) | Meta SI `comparable_goal` quando presente; composer pode injetar placeholder `1.0` antes do enrich |
| Inclusões / exclusões (SQL) | Inclui TES com `F4_DUPLIC='S'` (padrão); exclui `D2_TIPO='D'`; CF `5911`/`6151` com exceções; remessa especial `5927` conforme regras SF4. Segmento WEG = cliente `000001`; novos negócios = não-WEG |
| Fonte | api-delpi `get_financial_rol`, `get_*_rol_target_pct`, `get_commercial_rol_series`; BFF commercial-api `/analytics/*`; SQL: `api-delpi/app/infrastructure/persistence/totvs/financial_repositories/financial_repository.py` |
| Freshness | Conforme cache/query TOTVS do período filtrado |
| Filtros válidos | `branch` / unidade, `start_date`, `end_date`, `customer_segment`, escopo carteira (via BFF) |
| Escopo | branch / all (+ membership no Portal) |
| Versão da regra | v0 — baseline código |
| Owner | Comercial — a confirmar (homologação) |
| Status | **em_validacao** |

### Checklist de homologação (KPI-ROL)

- [ ] Confirmar se impostos descontados (ICM / IMP5 / IMP6) são a definição oficial de «líquido»  
- [ ] Confirmar competência por `D2_EMISSAO` (vs outro campo)  
- [ ] Confirmar tratamento de devoluções e CFs especiais  
- [ ] Confirmar se IPI deve ser separado no futuro (`ipi_separated`)  
- [ ] Confirmar fonte e curva da meta SI  

---

## KPI-CARTEIRA — Carteira comercial

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-CARTEIRA` |
| Nome | Carteira |
| Objetivo | Saldo de pedidos assumidos pelo Comercial |
| Fórmula | **A confirmar** — fonte SC5/SC6, cancelados, bloqueados, bruto/líquido |
| Fonte | a criar / parcial via open-orders |
| Owner | a confirmar |
| Status | rascunho · **bloqueia** dor #4 consolidada |

---

## KPI-ROL-CARTEIRA — ROL + carteira

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-ROL-CARTEIRA` |
| Nome | ROL + carteira |
| Objetivo | Visão combinada realizado + carteira |
| Fórmula | Soma de bases **compatíveis** (mesma unidade/natureza) — a confirmar |
| Fonte | depende KPI-ROL + KPI-CARTEIRA |
| Owner | a confirmar |
| Status | rascunho · **bloqueada** até ROL e Carteira |

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
| Fonte | api-delpi `get_sales_conversion_rate` (`GET /commercial/closing-rate`); BFF `/analytics/closing-rate`; doc: [comercial-taxa-conversao-estagios.md](../../../api-delpi/docs/api/comercial-taxa-conversao-estagios.md); repo: `SalesConversionRateRepository` |
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
| Nome | OTD |
| Objetivo | Entregas no prazo ÷ elegíveis |
| Fórmula | Definir solicitado vs confirmado; parciais; tolerância |
| Fonte | api-delpi `get_sales_order_otd`, panel, series |
| Owner | a confirmar |
| Status | rascunho |

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
| #4 (carteira consolidada × PCP) | KPI-CARTEIRA incompleta (E1.S2 preenche baseline) |
| #7 (ativo/novo/recuperado) | Janelas não formalizadas |

Engineering do cockpit Overview (MTD/YTD, card carteira **lado a lado**) usa o **baseline de código** acima enquanto as fichas permanecem `em_validacao`.
