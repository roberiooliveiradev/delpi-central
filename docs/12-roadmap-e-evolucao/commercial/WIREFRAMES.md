# Wireframes — Portal Comercial

> **Produto ao usuário:** Portal Comercial  
> **Id técnico:** `commercial` · `basePath` `/apps/commercial`  
> **Playbook:** [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)  
> **Paridade:** § 2.1.1 (Portal do Vendedor → Portal Comercial)  
> **UI kit:** `@delpi/plugin-ui` · modais contidos no host  
> **Status:** wireframes de produto (ago/2026) — não são mockups de marca finais  
> **Wave G / G+:** revisão de IA em [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md). UX polish + backlog de tarefas: [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md). IDs canônicos WF-01…10; **Wave G+** adiciona WF-00 (shell UnderlineNav), WF-01R (Home hero), WF-06R (Meu dia CRM). Rota `/my-day` implementada.

## Convenções

| Símbolo | Significado |
|---------|-------------|
| `[Botão]` | Ação primária/secundária |
| `( )` / `(•)` | Radio |
| `[x]` | Checkbox |
| `·····` | Campo de busca / input |
| `│ ░░░ │` | Skeleton / loading |
| `⚠` | Estado de atenção (atraso, SLA) — no wireframe textual |

**Layout portal:** sidebar do Minha DELPI à esquerda (fora do MFE). Conteúdo abaixo = área do plugin (`dashboard-commercial` pattern: `dashboard-commercial` → aqui `dashboard-commercial-portal` / root `.dashboard-commercial`).

**Rotas propostas (EN paths, labels pt-BR):**

| Rota | Label (menu) | Fase | Persona |
|------|--------------|------|---------|
| `/apps/commercial` | Início | F2b | Todos |
| `/apps/commercial/open-orders` | Pedidos em aberto | F2b | Vendedor+ |
| `/apps/commercial/customers` | Minha carteira | F2b | Vendedor+ |
| `/apps/commercial/customers/:code/:store` | Conta (detalhe) | F2b | Vendedor+ |
| `/apps/commercial/seller-portfolios` | Carteiras | F2b | Admin |
| `/apps/commercial/my-day` | Meu dia | Wave G+ | worklist.view |
| `/apps/commercial/proposals` | Propostas (ADY) | Consolidação | proposals.view |
| `/apps/commercial/proposals/:id` | Detalhe + PDF | Consolidação | proposals.view |
| `/apps/commercial/analytics` | Gestão visão geral | Consolidação | analytics.view |
| `/apps/commercial/analytics/otd` | OTD | Consolidação | analytics.view |
| `/apps/commercial/analytics/team` | Equipe | Consolidação | analytics + team |
| `/apps/commercial/analytics/opportunities` | Oportunidades OV | Consolidação | analytics.view |
| `/apps/commercial/prospects` | Prospects | pós-consolidação / P3 | — |
| `/apps/commercial/forecast` | Forecast | pós-consolidação | — |

### WF-G — Gestão visão geral (`/gestao`) — ASCII

```text
[UnderlineNav] Início | Meu dia | Pedidos | Carteira | Propostas | Gestão | Carteiras†
[Subnav Gestão] Visão geral · OTD · Equipe · Oportunidades
[FilterBar] Competence | Start DateField | End DateField | Branch | Segment | [Atualizar]
[KPI row ×6] ROL | Meta | Conversão | OTD | Ticket | Funil
[Série ROL]  chart
[Funil OV]   stages
[Tabela OV]  resumo período → drill /gestao/oportunidades/:n
[Export]
```

Datas v1: **2× DateField** (sem DateRangeField). Filtros: URL + `sessionStorage` `delpi.commercial.gestao.filters`.

Wireframes ASCII detalhados + matriz `@delpi/plugin-ui`: [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md).

---

## Mapa de navegação (F2b)

```text
Portal Comercial
├── Início                         /apps/commercial
├── Pedidos e entregas
│   └── Pedidos em aberto          /apps/commercial/open-orders
├── Contas
│   ├── Minha carteira             /apps/commercial/customers
│   └── Conta (detalhe)            /apps/commercial/customers/:code/:store   ← fora do menu
└── Administração
    └── Carteiras                  /apps/commercial/seller-portfolios        ← admin
```

---

## Wave G+ — shell e Home (ago/2026)

Nav secundária do plugin = **UnderlineNav** (padrão GitHub Primer / SAP), **não** pills de `ActionButton`. Host Minha DELPI já tem sidebar — sem sidebar interna no plugin. Meu dia alinhado a HubSpot/Pipedrive/Gong: prazo + prioridade + cliente.

### WF-00 — Shell (UnderlineNav)

```text
┌─ plugin ────────────────────────────────────────────────────────────────────┐
│ [icon] Portal Comercial [?]                    Escopo: Carteira própria     │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Início   Meu dia (3)   Pedidos em aberto   Minha carteira   Carteiras†      │
│ ═══════                                                                     │
│   ↑ underline accent #089bdb; badge Meu dia = overdue+today                 │
│ … página …                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### WF-01R — Início (hero + permissões)

```text
┌─ HERO ──────────────────────────────────────────────────────────────────────┐
│ Bom dia · {escopo/carteira}                                   [Atualizar]   │
│ “Aqui está o que precisa da sua atenção hoje.”                              │
│ Chips: Pedidos abertos · Follow-ups · Atrasos                               │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ PRECISA DE ATENÇÃO (AlertQueue) ──────────────────────────────────────────┐
│ ⚠ N atrasos [Ver pedidos]  │  ⚠ M follow-ups [Meu dia]                     │
│ empty → EmptyState + CTA · loading/erro por card (allSettled)               │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ SEUS NÚMEROS (accounts.view) ──────────────────────────────────────────────┐
│ Linhas │ Valor │ Pode faturar │ Atrasos │ Tarefas* (worklist.view)          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ GESTÃO (seller-portfolios.manage) ─────────────────────────────────────────┐
│ ROL · Conversão · OTD + tabela equipe                                       │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ ATALHOS ───────────────────────────────────────────────────────────────────┐
│ Meu dia* · Pedidos · Carteira · Carteiras†                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### WF-06R — Meu dia (CRM mínimo)

```text
┌─ Filtros in-page ─ [Atrasadas] [Hoje] [Depois] ─ [Atualizar] ───────────────┐
│ item: título · prioridade · prazo · cliente                                 │
│        [Concluir] [Adiar] [Abrir conta]                                     │
├─ Nova tarefa ───────────────────────────────────────────────────────────────┤
│ Título* | Prazo* (default hoje EOD) | Prioridade | Cliente | Tipo           │
│                                                    [Criar tarefa]           │
└─────────────────────────────────────────────────────────────────────────────┘
```

Conta 360: CTA **Agendar follow-up** → Meu dia com `customer_code`/`store` pré-preenchidos.

---

## WF-01 — Shell + Início (home por papel)

**Rota:** `/apps/commercial`  
**Objetivo:** entrada única; atalhos e pendências; sem regra de negócio pesada na home.

### Vendedor

```
┌─ Portal (shell Minha DELPI) ────────────────────────────────────────────────┐
│ [sidebar]  │ Portal Comercial                              [Período ▾] [↻] │
│            ├──────────────────────────────────────────────────────────────┤
│ Comercial  │ Início                                                         │
│  · Início  │                                                                │
│  · Pedidos │ Olá, {nome} · Carteira própria · Atualizado há 4 min           │
│  · Carteira│                                                                │
│  · …       │ ┌─ Precisa de atenção ─────────────────────────────────────┐ │
│            │ │  ⚠ 3 pedidos atrasados     [Ver pedidos]                   │ │
│            │ │  ⚠ 2 clientes sem contato   [Ver carteira]                 │ │
│            │ │  · 1 follow-up hoje         [Meu dia]  ← F5 (oculto se N/A)│ │
│            │ └────────────────────────────────────────────────────────────┘ │
│            │                                                                │
│            │ ┌─ Atalhos ─────────────┐  ┌─ Resumo da carteira ──────────┐ │
│            │ │ [Pedidos em aberto]   │  │ Clientes     42               │ │
│            │ │ [Minha carteira]      │  │ Valor em aberto  R$ 1,2 mi    │ │
│            │ │ [Propostas →]         │  │ Atrasados     5               │ │
│            │ │   (deep link externo) │  │ Próxima entrega  08/08        │ │
│            │ └───────────────────────┘  └───────────────────────────────┘ │
│            │                                                                │
│            │ ┌─ Recentes ───────────────────────────────────────────────┐ │
│            │ │ Cliente 01001-01  ACME Ltda          há 12 min   [Abrir] │ │
│            │ │ Pedido 000123 / 01                   há 1 h     [Abrir] │ │
│            │ └──────────────────────────────────────────────────────────┘ │
└────────────┴────────────────────────────────────────────────────────────────┘
```

### Gestão (supervisor / gerente)

```
┌─ Portal Comercial · Início (gestão) ────────────────────────────────────────┐
│ Filtros: [Filial ▾] [Equipe/Vendedor ▾] [Período ▾]              [Atualizar]│
│                                                                             │
│ ┌ KPI ROL MTD ┐ ┌ Carteira ┐ ┌ Gap meta ┐ ┌ Pedidos atrasados ┐            │
│ │ R$ …        │ │ R$ …     │ │ R$ …     │ │ 18                 │            │
│ │ vs meta …%  │ │          │ │          │ │ [Abrir OTD/pedidos]│            │
│ └─────────────┘ └──────────┘ └──────────┘ └────────────────────┘            │
│                                                                             │
│ ┌─ Equipe — atenção ──────────────────────────────────────────────────────┐│
│ │ Vendedor     Atrasados  Valor aberto  Follow-ups vencidos   [Drill]     ││
│ │ Ana Silva         4      R$ 210 mil              2                      ││
│ │ …                                                                       ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ Atalhos: [Dashboard Comercial →] [Propostas →] [Carteiras admin]            │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Estados:** loading por card (`Promise.allSettled`); erro parcial não derruba a home; sem permissão de KPI → card omitido (não 403 na página inteira).

---

## WF-02R — Pedidos em aberto (bancada operacional)

**Rota:** `/apps/commercial/open-orders`  
**Paridade:** `OpenOrdersPage` / `OpenOrdersPageImpl`  
**Dados:** api-delpi `GET /pedidos-venda-abertos/` (+ ops abertas)  
**Papel:** bancada de linhas (achar → entender entrega → agir). Home = atenção; Gestão = KPIs de período.  
**Kit:** `cm-*` — PageHero (`actions`/`children`), ScopeChipBar, FilterBar, DataTable / Cards, InlineMeter, WorkbenchModal host-fill.  
**Evoluções:** WF-02R-H (Hero), WF-02R-T (tabela visual), WF-02R-C (cards), WF-02R-D (modal detalhe). MultiSelect do kit usa o mesmo checkbox moderno das Colunas.

```
┌─ PageHero (card único) ───────────────────────────────────────────────────┐
│ PEDIDOS · highlights Linhas / Valor / Após filtros         [↻ Atualizar] │
│ Carteira · Atenção chips · FilterBar (busca/filial/cliente/datas)         │
└───────────────────────────────────────────────────────────────────────────┘
┌─ SectionCard ─ [Tabela|Cards] ─ Excel · Fonte · Colunas ──────────────────┐
│ Tabela: Cobertura (InlineMeter) · Prev. OP + badge · Status · Atraso badge│
│ Cards: mesmos campos visíveis · Ordenar por + direção · Detalhe → modal   │
└───────────────────────────────────────────────────────────────────────────┘
┌─ Modal host-fill (Detalhe da linha) — ver WF-02R-D ───────────────────────┐
│ Status fabril · KPIs · charts · bloco OP+timeline · tabela OP · Ver OV?   │
└───────────────────────────────────────────────────────────────────────────┘
```

**Colunas default:** Cliente, Pedido, Produto, Cobertura, Entrega, Prev. OP, Status, Valor, Atraso.  
**Clique:** linha / Prev. OP / card → modal expandido (drawer lateral deprecado).  
**Deep links:** `?stock=` / `?focus=late` → chip; `seller_id` = portfolio id.

**Mobile (≤768px):** default Cards na 1ª visita; hero empilha; modal fill.

**Histórico:** WF-02 (KPI cards + tabela densa + modal OP) → WF-02R → H/T/C/D.

### WF-02R-D — Modal Detalhe da linha

**Domínio:** SC5/SC6 + OP SC2 (não misturar com OV AD*).  
**APIs extras ao abrir:** `/products/{code}/factory-status`, `/production/orders/by-op/{op}`, `/production/appointments/by-op`, opcional `/products/{code}/structure`; probe OV via `GET /commercial/proposals/{pedido}` se não houver `proposal_number`.

```
┌─ Modal host-fill · Detalhe da linha ─────────────────────────────────────┐
│ Pedido · Linha · Produto · Cliente                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Status fabril do produto (factory-status; some se 403)                   │
│ KPIs: saldo · estoque · produzir · valor · atraso · status · kind · datas│
│ Charts compactos: cobertura · prazo                                      │
│ Produção/OPs: SegmentToggle · meter · Prazo OTD + PIs · Timeline · CTA   │
│   «Ver no OTD produção» → /apps/dashboard-production/otd/op/{op}         │
│ Tabela OP rica (produzido/planejado/saldo/status/OTD) — clique sincroniza│
│ Estrutura do produto (BOM colapsável, só código da linha)                │
│ [Copiar pedido] [Ver OV n] [Abrir conta]                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

**Fora do modal:** KPI/processo AD1, tabela ADJ multi-item, timeline AIJ, export OV → **WF-OV-D**.

### WF-OV-D — Página Detalhe da OV (Gestão)

**Rota:** analytics opportunity detail (`AnalyticsOpportunityDetailPage`)  
**Paridade:** dashboard-commercial `CommercialDetailPage`  
**APIs:** `GET /commercial/proposals/{n}` + `/history/events` + `/products/{code}/structure` por item.

```
┌─ Página · OV n ──────────────────────────────────────────────────────────┐
│ [Voltar] [Atualizar]                                                     │
│ KPI: Status · Abertura · Fechamento                                      │
│ Cards: Proposta | Cliente e vendedor                                     │
│ Produtos ADJ (grupo, tipo, qtd PI)                                       │
│ BOM por produto                                                          │
│ Histórico: [Linha do tempo | Tabela] via /history/events                 │
└──────────────────────────────────────────────────────────────────────────┘
```

**Mapa:** comercial (OV) na página; operacional (pedido+OP) no modal WF-02R-D. Deep link opcional modal → esta página.


---

## WF-03 — Minha carteira (lista de clientes)

**Rota:** `/apps/commercial/customers`  
**Paridade:** `CustomersPage`  
**Dados:** commercial-api portfolio + enrichment api-delpi

```
┌─ Portal Comercial · Minha carteira ─────────────────────────────────────────┐
│ Breadcrumb: Portal Comercial › Minha carteira                               │
│                                                                             │
│ Escopo: (•) Minha carteira  ( ) Equipe     ← equipe só se permissão         │
│ Busca ················  [Atenção ▾]  [Ordenar: valor aberto ▾]              │
│                                                                             │
│ ┌─ Fila de atenção ───────────────────────────────────────────────────────┐│
│ │ Chips: Atrasados (5) · Sem pedido recente (3) · Parcial (2)             ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ Avatar │ Cliente              │ Cidade   │ Aberto    │ Atraso │ Próx.  ││
│ │ [img]  │ 01001-01 ACME Ltda   │ Joinville│ R$ 180 mil│ 2      │ 08/08  ││
│ │ [img]  │ 01002-01 Beta SA     │ Blumenau │ R$  42 mil│ 0      │ 12/08  ││
│ │ …                                                                       ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ Linha inteira clicável → detalhe da conta                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Vazio:** «Nenhum cliente na carteira. Peça ao administrador para vincular clientes.» + CTA admin se `seller-portfolios.manage`.

---

## WF-04 — Conta / Check-up do cliente

**Rota:** `/apps/commercial/customers/:code/:store`  
**Paridade:** `CustomerDetailPage`  
**Chave:** `customer_key = code|store`

```
┌─ Portal Comercial · Conta ──────────────────────────────────────────────────┐
│ ← Minha carteira    01001-01 · ACME Ltda                    [Avatar] [⋯]   │
│ Joinville/SC · Carteira: Ana Silva · Atualizado há 3 min                    │
│                                                                             │
│ Abas: [Check-up] [Pedidos] [Faturamento] [Notas]   ← Faturamento/NF se API │
│                                                                             │
│ === Aba Check-up ========================================================== │
│ ┌ Valor aberto ┐ ┌ Pedidos ┐ ┌ Atrasados ┐ ┌ Próx. entrega ┐ ┌ Ticket* ┐ │
│ │ R$ 180 mil   │ │ 6       │ │ 2         │ │ 08/08         │ │ —      │ │
│ └──────────────┘ └─────────┘ └───────────┘ └───────────────┘ └────────┘ │
│ * ticket só após ficha KPI F0                                               │
│                                                                             │
│ ┌─ Pontos para a conversa ────────────────────────────────────────────────┐│
│ │ · 2 itens atrasados (saldo 80 un.)                                      ││
│ │ · Próxima entrega em 3 dias                                             ││
│ │ · Pedido 000123 parcial                                                 ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ ┌─ Pedidos em aberto (resumo) ────────────────────────── [Ver todos] ────┐│
│ │ Pedido │ Item │ Produto │ Saldo │ Entrega │ Status                      ││
│ │ 000123 │ 01   │ …       │ 50    │ 02/08   │ ⚠ Atrasado                 ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ === Aba Pedidos =========================================================== │
│ Tabela completa filtrada ao cliente (mesmo contrato open-orders)            │
│                                                                             │
│ === Aba Faturamento (se disponível) ======================================= │
│ Série / período · gráfico ou tabela billing-series                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Menu ⋯ (admin):** alterar avatar · transferir cliente (se permissão).

---

## WF-05 — Administração de carteiras

**Rota:** `/apps/commercial/seller-portfolios`  
**Paridade:** `SellerConfigPage`  
**Dados:** commercial-api `seller-portfolios`  
**Permissão:** `commercial.seller-portfolios.manage` (espelha admin legado)

```
┌─ Portal Comercial · Carteiras ──────────────────────────────────────────────┐
│ Breadcrumb: Portal Comercial › Administração › Carteiras                    │
│                                                                             │
│ [+ Nova carteira]   Busca vendedor ·········                                │
│                                                                             │
│ ┌ Lista de carteiras ───────────────┐  ┌ Detalhe / edição ────────────────┐│
│ │ Ana Silva      42 clientes  Ativa │  │ Vendedor: Ana Silva              ││
│ │ Bruno Costa    28 clientes  Ativa │  │ Keycloak: ana.silva@…            ││
│ │ …                                 │  │ Status: (•) Ativa  ( ) Inativa   ││
│ │                                   │  │                                  ││
│ │                                   │  │ Clientes vinculados              ││
│ │                                   │  │ Busca TOTVS ······· [Adicionar]  ││
│ │                                   │  │ ┌──────────────────────────────┐ ││
│ │                                   │  │ │ 01001-01 ACME    [Remover]   │ ││
│ │                                   │  │ │ 01002-01 Beta    [Remover]   │ ││
│ │                                   │  │ └──────────────────────────────┘ ││
│ │                                   │  │                                  ││
│ │                                   │  │ [Substituir lista] [Transferir…] ││
│ │                                   │  │ [Salvar]                         ││
│ └───────────────────────────────────┘  └──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Modal Transferir (host-contained):**

```
┌─ Transferir clientes ─────────────────────────────┐
│ De: Ana Silva                                     │
│ Para: [Bruno Costa ▾]                             │
│ Clientes: [x] 01001-01  [x] 01002-01  [Todos]     │
│ Motivo (obrigatório) ···························  │
│                    [Cancelar]  [Transferir]       │
└───────────────────────────────────────────────────┘
```

---

## WF-06 — Meu dia (F5)

**Rota:** `/apps/commercial/my-day`  
**Dados:** commercial-api worklist  
**Wave G+:** ver **WF-06R** acima (form com prazo/prioridade/cliente; Adiar/Abrir).

```
┌─ Portal Comercial · Meu dia ────────────────────────────────────────────────┐
│ Filtros: [Hoje ▾] [Tipo ▾] [Criticidade ▾]                                  │
│                                                                             │
│ Segmentos: (•) Vencidos (4)  ( ) Hoje (6)  ( ) Semana (11)                  │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐│
│ │ ⚠ Follow-up  ACME 01001-01   Venceu ontem   [Concluir] [Adiar] [Abrir] ││
│ │ · Pedido atrasado 000123     há 3 dias      [Abrir pedido]             ││
│ │ · Proposta parada OV-992     12 dias        [Abrir propostas →]        ││
│ │ · Oportunidade sem ação      …              [Abrir]                    ││
│ └─────────────────────────────────────────────────────────────────────────┘│
│ Ordenação explicável: criticidade = atraso SLA > valor > data               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## WF-07 — Prospects (pós-paridade / P0 CRM)

**Rota:** `/apps/commercial/prospects`

```
┌─ Portal Comercial · Prospects ──────────────────────────────────────────────┐
│ [+ Novo prospect]  Busca ·····  Status [▾]  Origem [▾]  Responsável [▾]    │
│                                                                             │
│ ┌─ Funil (contagens) ─ Novo (8) · Em contato (12) · Qualificado (5) · … ─┐│
│ └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│ Tabela: Nome · Origem · Status · Responsável · Próx. ação · Follow-up       │
│ Linha → /prospects/:id                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Detalhe prospect (esboço):** dados cadastrais · contatos · timeline · [Converter em cliente] (fluxo controlado).

---

## WF-08 — Oportunidades / pipeline (F6)

**Rota:** `/apps/commercial/opportunities`

```
┌─ Portal Comercial · Oportunidades ──────────────────────────────────────────┐
│ Visão: (•) Kanban  ( ) Lista     Pipeline [Padrão ▾]   [+ Oportunidade]    │
│                                                                             │
│ ┌ Qualificação ┐ ┌ Proposta ┐ ┌ Negociação ┐ ┌ Fechamento ┐                │
│ │ ┌──────────┐ │ │ ┌──────┐ │ │            │ │            │                │
│ │ │ ACME     │ │ │ │ Beta │ │ │            │ │            │                │
│ │ │ R$ 90 mil│ │ │ │ …    │ │ │            │ │            │                │
│ │ │ 12d stage│ │ │ └──────┘ │ │            │ │            │                │
│ │ └──────────┘ │ │          │ │            │ │            │                │
│ └──────────────┘ └──────────┘ └────────────┘ └────────────┘                │
│ Arrastar card = stage-transition (API) + motivo se ganho/perda              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## WF-09 — Forecast (F6)

**Rota:** `/apps/commercial/forecast`

```
┌─ Portal Comercial · Forecast ───────────────────────────────────────────────┐
│ Ciclo: Ago/2026 · Status: Em edição                                         │
│ Visão: (•) Meu  ( ) Equipe                                                  │
│                                                                             │
│ ┌ Pipeline ┐ ┌ Melhor caso ┐ ┌ Commit ┐ ┌ Realizado ┐ ┌ Meta ┐             │
│ │ R$ …     │ │ R$ …        │ │ R$ …   │ │ R$ …      │ │ R$ …│             │
│ └──────────┘ └─────────────┘ └────────┘ └───────────┘ └──────┘             │
│                                                                             │
│ Itens do forecast (oportunidades / pedidos) · categoria · valor             │
│ [Adicionar item]                                                            │
│                                                                             │
│ [Salvar rascunho]  [Submeter]     Supervisor: [Aprovar] [Rejeitar]          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## WF-10 — Estados transversais

### Loading

```
┌─ Seção ─────────────────┐
│ ░░░░░░░░░░░░░░░░░░░░░░░ │
│ ░░░░░░░░░  ░░░░░░░░░░░░ │
└─────────────────────────┘
```

### Erro parcial

```
┌─ Pedidos em aberto ─────────────────────────────⚠─┐
│ Não foi possível carregar a lista.                 │
│ [Tentar novamente]                                 │
│ (KPIs da home / outras seções seguem visíveis)     │
└────────────────────────────────────────────────────┘
```

### Sem permissão

```
┌─ Carteiras ────────────────────────────────────────┐
│ Você não tem permissão para administrar carteiras. │
│ Solicite commercial.seller-portfolios.manage       │
└────────────────────────────────────────────────────┘
```

### Plugin / API parcial

Home e menu permanecem; card da capacidade indisponível mostra estado de erro isolado (MOD-012).

---

## Matriz wireframe × paridade § 2.1.1

| Capacidade Portal do Vendedor | Wireframe | Rota Portal Comercial |
|-------------------------------|-----------|------------------------|
| Lista pedidos em aberto | WF-02R | `/open-orders` |
| Detalhe linha (OP + fabril) | WF-02R-D | modal em `/open-orders` |
| Detalhe OV (paridade dashboard) | WF-OV-D | `/analytics/opportunities/:n` |
| Minha carteira | WF-03 | `/customers` |
| Check-up cliente | WF-04 | `/customers/:code/:store` |
| Config vendedores | WF-05 | `/seller-portfolios` |
| Avatar | WF-04 (⋯) + WF-05 | commercial-api |
| Deep link codigo+loja | WF-04 | idem |
| Home / entrada | WF-01 | `/` |

---

## Componentes `@delpi/plugin-ui` sugeridos

| Área | Preferir do kit |
|------|-----------------|
| KPIs | `KpiCard` / dual-class `delpi-ui` |
| Filtros | `FilterBarShell` |
| Tabelas | `DataTable` + paginação |
| Loading | `LoadingActivityCard` |
| Seções | `SectionCard` |
| Ajuda | `HelpTooltip` / `FieldLabel` |
| Modal transferir | shell host-contained (`HostContainedDialog`) |

CSS de kit: **zero** no MFE — só tokens `--delpi-ui-*` + layout de página.

---

## Próximos artefatos

| Artefato | Quando |
|----------|--------|
| `HOMOLOGACAO-PARIDADE-PEDIDOS.md` | Checklist QA F2b |
| Wireframes mobile detalhados | Antes do build F2b se UX mobile for critério de aceite |
| Fluxos convert prospect / forecast approve | Ao iniciar F5–F6 |
| High-fi no design system | Opcional; wireframe ASCII basta para implementação |

---

## Referências

- [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 2.1, § 6, § 11  
- [PORTAL-VENDEDOR-ESPECIFICACAO.md](../pedidos-venda-abertos/PORTAL-VENDEDOR-ESPECIFICACAO.md)  
- [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)  
- Padrão ASCII: `plugins/transformometro/docs/wireframes/`  
