# Portal Comercial — fichas de KPI (F0)

> **Status:** rascunho (ago/2026) — owners e fórmulas a homologar com o Comercial  
> **Playbook:** [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 1.2 e § 10  
> **Gate F0 mínimo:** este template publicado (fórmulas podem permanecer “a confirmar”)

Legenda de status da ficha: `rascunho` · `em_validacao` · `aprovada` · `bloqueada`.

---

## Template (usar em cada ficha)

| Campo | Conteúdo |
|-------|----------|
| Código | KPI-xxx estável |
| Nome (pt-BR) | |
| Objetivo | |
| Fórmula | |
| Numerador / denominador | |
| Inclusões / exclusões | |
| Fonte | api-delpi `operationId` / SI / commercial-api |
| Owner | a confirmar |
| Freshness | |
| Filtros válidos | filial, período, … |
| Escopo | own / team / branch / all |
| Versão da regra | v0 |
| Status | rascunho |

---

## KPI-ROL — Receita operacional líquida

| Campo | Conteúdo |
|-------|----------|
| Código | `KPI-ROL` |
| Nome | ROL |
| Objetivo | Medir faturamento líquido do período |
| Fórmula | **A confirmar** — documentos, impostos, devoluções, competência |
| Fonte | api-delpi `get_*_rol_target_pct`, `get_commercial_rol_series`, `get_financial_rol` |
| Owner | a confirmar |
| Status | rascunho |

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
| Nome | Hit rate |
| Objetivo | Taxa de conversão de ofertas |
| Fórmula | Ganhos ÷ universo elegível — **preservar metodologia atual** até documentar |
| Fonte | api-delpi `get_sales_conversion_rate` (`/commercial/closing-rate`) |
| Owner | a confirmar |
| Status | rascunho |

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
| #4 (carteira consolidada × PCP) | KPI-CARTEIRA incompleta |
| #7 (ativo/novo/recuperado) | Janelas não formalizadas |

Implementação F1–F2b (API + paridade Portal do Vendedor) **segue** sem aguardar aprovação total destas fichas.
