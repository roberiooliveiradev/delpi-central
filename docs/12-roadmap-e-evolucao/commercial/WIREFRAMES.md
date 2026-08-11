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
│            │ │ [Propostas]           │  │ Atrasados     5               │ │
│            │ │   (página nativa)     │  │ Próxima entrega  08/08        │ │
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
**Kit:** `cm-*` — PageHero (`actions`/`children`), ScopeChipBar, FilterBar, DataTable / Cards, InlineMeter.
**Evoluções:** WF-02R-H (Hero), WF-02R-T (tabela visual), WF-02R-C (cards), WF-02R-D (página de detalhe). MultiSelect do kit usa o mesmo checkbox moderno das Colunas.

```
┌─ PageHero (card único) ───────────────────────────────────────────────────┐
│ PEDIDOS · highlights Linhas / Valor / Após filtros         [↻ Atualizar] │
│ Carteira · Atenção chips · FilterBar (busca/filial/cliente/datas)         │
└───────────────────────────────────────────────────────────────────────────┘
┌─ SectionCard ─ [Tabela|Cards] ─ Excel · Fonte · Colunas ──────────────────┐
│ Tabela: Cobertura (InlineMeter) · Prev. OP + badge · Status · Atraso badge│
│ Cards: mesmos campos visíveis · Ordenar por + direção · Detalhe → página  │
└───────────────────────────────────────────────────────────────────────────┘
┌─ Página nativa (Detalhe da linha) — ver WF-02R-D ─────────────────────────┐
│ Status fabril · KPIs · charts · bloco OP+timeline · tabela OP · Ver OP/OV │
└───────────────────────────────────────────────────────────────────────────┘
```

**Colunas default:** Cliente, Pedido, Produto, Cobertura, Entrega, Prev. OP, Status, Valor, Atraso.  
**Clique:** linha / Prev. OP / card → página nativa da linha; ação
da OP → página SPA nativa `/open-orders/:filial/:pedido/:linha/op/:op`.
**URLs internas compartilháveis:** busca, filial, clientes, datas, estoque/atenção,
`seller_id`, sort/direção e página formam o estado canônico da lista. Valores são
allowlisted, defaults são omitidos, `popstate` restaura a bancada e filtros/escopo/
sort resetam a página. `seller_id` só é aceito com `team_scope` e portfolio id
válido. O `replaceState` roda apenas na rota exata `/open-orders`; linha e OP
preservam o estado completo no retorno. O legado `?pedido=&linha=&filial=` é
migrado após localizar a linha. Home pode emitir `?focus=late` / `?stock=…`.

**Mobile (≤768px):** default Cards na 1ª visita; hero e página de detalhe empilham.

**Histórico:** WF-02 (KPI cards + tabela densa + modal OP) → WF-02R → H/T/C/D.

### WF-02R-D — Páginas nativas da linha e da OP

**Domínio:** SC5/SC6 + OP SC2 (não misturar com OV AD*).  
**APIs extras ao abrir:** `/products/{code}/factory-status?branch=`, `/production/orders/by-op/{op}`, `/production/appointments/by-op` (agregado), opcional `/products/{code}/structure`.  
**OV (AD1_NROPOR):** se a lista PVA trouxer `proposal_number`, usa direto; senão `GET /commercial/proposals?search={pedido}&branch=` e match por filial+cliente (limiar). **Não** chamar `GET /proposals/{pedido}` — path é OV, não `C5_NUM`. Sem vínculo SC5↔AD1 estável documentado no PVA, enriquecimento na lista é opcional.

```
┌─ Página linha · PagePath Pedidos / Pedido-linha ─────────────────────────┐
│ Pedido · Linha · Produto · Cliente                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Status fabril (+ chips MP: PA produzível, MP limitante, MPs sem estoque) │
│ KPIs locais da linha (não bloqueados pelo loading dos extras)            │
│ Charts compactos: cobertura · prazo                                      │
│ Produção/OPs: SegmentToggle · meter · Prazo OTD + tabela PI densa        │
│   Timeline · apontamentos agregados · prefetch até 12 OPs (+ on-demand)  │
│   «Ver no OTD produção» → /apps/dashboard-production/otd/op/{op}         │
│ Tabela OP rica — clique sincroniza OP selecionada                        │
│ Estrutura do produto (BOM: empty/erro/loading visíveis)                  │
│ [Abrir página OP] [Copiar pedido] [Ver OV n] [Abrir conta]               │
└──────────────────────────────────────────────────────────────────────────┘
┌─ Página OP nativa · PagePath Pedidos / Pedido-linha / Produto / OP ──────┐
│ PageHero · mesmo OpenOrdersProductionDetailContent integral da linha      │
│ loading / erro / 404 / retry · troca OP na URL · sem CTA para a própria OP│
└───────────────────────────────────────────────────────────────────────────┘
```

**Entrada por contexto de pedido:** `?pedido=&linha=&filial=` localiza a linha e
substitui o endereço pela rota nativa `/open-orders/:filial/:pedido/:linha`.

**Página OP:** busca a linha exata por filial+pedido+linha no escopo `seller_id`
validado contra `PortfolioScope.canUseTeamScope` e ids carregados, e
confirma a OP em `opsUtilizadas`; não usa iframe, import ou URL de outro MFE.
As páginas compartilham hook, cálculos, componentes e conteúdo operacional.
Ao trocar entre múltiplas OPs, a própria rota SPA é atualizada; ao voltar, todo o
estado canônico da bancada é herdado, e a OP retorna à rota da linha.

**Fora do detalhe de pedido:** KPI/processo AD1, tabela ADJ multi-item, timeline AIJ, export OV → **WF-OV-D**.

### WF-OV-D — Página Detalhe da OV (Gestão)

**Rota:** analytics opportunity detail (`AnalyticsOpportunityDetailPage`)  
**Paridade:** dashboard-commercial `CommercialDetailPage`  
**APIs:** `GET /commercial/proposals/{n}` + `/history/events` + `/products/{code}/structure` por item.

```
┌─ Página · OV n ──────────────────────────────────────────────────────────┐
│ PagePath Oportunidades / OV n                              [Atualizar]    │
│ KPI: Status · Abertura · Fechamento                                      │
│ Cards: Proposta | Cliente e vendedor                                     │
│ Produtos ADJ (grupo, tipo, qtd PI)                                       │
│ BOM por produto                                                          │
│ Histórico: [Linha do tempo | Tabela] via /history/events                 │
└──────────────────────────────────────────────────────────────────────────┘
```

**Mapa:** OV exclusivamente nesta página, aberta por
`navigateAnalyticsOpportunityDetail`; não existe modal de OV. O PagePath retorna
a `/analytics/opportunities` preservando apenas filtros allowlisted presentes.
Produtos, histórico em modo tabela e detalhe de OP usam `DataTable` no desktop e
`DataRecordCard` no mobile.
Pedido+OP permanece nas páginas nativas WF-02R-D.


---

## WF-03R — Minha carteira (desktop)

**Rota:** `/apps/commercial/customers`  
**Papel:** priorizar clientes da carteira com pedidos de venda em aberto; não representa a SA1 completa.
**Estado URL:** somente `q`, `focus`, `trend`, `seller_id`, `sort`, `dir` e
`page` allowlisted; presets fixos agora, saved views customizadas depois.
Valores inválidos são normalizados e defaults são omitidos. `focus=growth`
legado vira `trend=up`; `focus=inactive` vira `all`.

```text
┌─ PageHero · Minha carteira ─────────────────────────── [Atualizar] ──────┐
│ Clientes no recorte 24 │ Valor aberto R$ 1,9 mi │ Após filtros 7        │
│ Atualizado 09:04                                                       │
│ Carteira [Todos os vendedores ▾]                                      │
│ Foco [Todos] [Atenção] [Em dia] [Sem venda 60d]                       │
│ Tendência [Todas] [Crescimento] [Estável] [Queda]                     │
│ Buscar cliente, código, loja ou pedido [___________________________]    │
└─────────────────────────────────────────────────────────────────────────┘
┌─ Faturamento — últimos 12 meses ────────────────────────────────────────┐
│ [Hoje][Semana][Mês][Trimestre][Ano][12 meses][Personalizado]           │
│ ChartToolbar [Dia] [Semana] [Mês] [Ano] · cliente ▾                    │
│ Área do faturamento (Recharts)                                         │
└─────────────────────────────────────────────────────────────────────────┘
┌─ SectionCard · Clientes (1–20 de 24) ─────────────── [Colunas] ────────┐
│ Cliente       Vendedor  Última venda  Fat.12m  Em aberto  Atrasos      │
│ ACME 01001/01 Ana       01/08/26      R$ 800k  R$ 90k     2            │
│ … clique/Enter na linha → Conta; resize/reorder e paginação abaixo     │
└─────────────────────────────────────────────────────────────────────────┘
```

**Componentes importados de `@delpi/plugin-ui`:** `PageHero`,
`ScopeChipBar`, `FilterBarShell`, `TextField`, `SelectField`, `DateField`,
`SectionCard`, `ChartToolbar`, `DataTable`, `TableColumnVisibilityMenu`,
`DataRecordCard`, `CompactPagination`, `StatusBadge`, `KpiCard`, `StateBanner`,
`EmptyState` e `LoadingActivityCard`.

**Composições de domínio no `commercial`:** `CustomersPage`,
`SellerScopeFilter`, `CustomersTable`, `CustomerSummaryCards`,
`CustomerBillingSeriesChart` e o mapper `CustomerSummary → DataRecordCard`.
O MFE mantém apenas layout/responsividade e regra comercial; não replica CSS do kit.

**Colunas default:** Cliente, Última venda, Fat. 12 meses, Tendência, Status,
Em aberto, Atrasos e Próxima entrega. Vendedor é default apenas para escopo de
equipe; Cidade / UF começa oculta. O usuário pode persistir visibilidade, ordem
e largura localmente.

**Cobertura:** a lista base de pedidos em aberto não é paginada na origem e
permanece utilizável se enrichment ou faturamento falhar parcialmente. O MFE
divide enrichment e billing em lotes determinísticos de até 200 clientes e
agrega a cobertura. Campo derivado sem lote coberto mostra
`Dado indisponível`; export deixa a célula vazia, sem converter ausência em zero.

### WF-03R-M — Minha carteira (mobile)

```text
┌ Minha carteira                         [↻] ┐
│ 24 clientes · R$ 1,9 mi                    │
│ Atualizado 09:04                            │
│ Carteira [Todos ▾]                         │
│ Foco [Todos][Atenção][Em dia][Sem venda] → │
│ Tendência [Todas][Alta][Estável][Queda] →  │
│ [Buscar_______________________________]    │
└─────────────────────────────────────────────┘
┌ [avatar] ACME                    [Atenção] ┐
│ 01001 · Loja 01                            │
│ Última venda 01/08 · Em aberto R$ 90k     │
│ Atrasos 2 · Próxima entrega 15/08         │
│ Próxima ação: tratar atraso                │
└─────────────────────────────────────────────┘
                1 2 3 ›
[Análise da carteira]
```

No mobile, `DataRecordCard` usa o mesmo conjunto filtrado, ordenado e paginado
da `DataTable`; não existe segundo pipeline nem segundo fetch.

---

## WF-04R — Conta 360 (desktop)

**Rota:** `/apps/commercial/customers/:code/:store`  
**PagePath:** `← Minha carteira / {cliente}`, com retorno determinístico para a
lista e preservação de `q`, `focus`, `trend` e `seller_id`.
**Estado URL:** `?secao=resumo|pedidos|historico|oportunidades|atividades`;
`faturamento` e `contatos` permanecem aliases legados.

```text
← Minha carteira   /   ACME
┌─ PageHero · Conta ────────────── [Follow-up] [Propostas] [Atualizar] ─┐
│ ACME  [Atenção]                                                      │
│ 000006 · Loja 01 · cidade/UF · vendedor · atualizado                 │
│ Fat. 12m  │  Em aberto  │  Pedidos  │  Próx. entrega                 │
│ Próxima ação: Tratar atraso                                          │
└──────────────────────────────────────────────────────────────────────┘
 [Visão geral] [Pedidos 3] [Histórico] [Oportunidades] [Atividades]
┌─ tabpanel full-width ────────────────────────────────────────────────┐
│ Pontos para conversa · Evolução · preview pedidos/atividades         │
└──────────────────────────────────────────────────────────────────────┘
```

**Abas:** Pedidos mostra linhas do cliente; Histórico carrega faturamento e NFs
somente quando ativo; Oportunidades oferece CTA interno apenas com
`analytics.view`; Atividades carrega timeline real e permite follow-up somente
com `worklist.view + followups.manage`. Cada fonte mantém loading, erro, vazio,
retry e atualização independentes.

**Componentes importados de `@delpi/plugin-ui`:** `PagePath`, `PageHero`,
`InitialsAvatar`, `StatusBadge`, `UnderlineNav` em modo tabs, `DetailCard`,
`DetailFieldGrid`, `SectionCard`, `KpiCard`, `ChartCard`, `Timeline`,
`DataTable`, `DataRecordCard`, `ActionButton`, `StateBanner`, `EmptyState` e
`LoadingActivityCard`.

**Composições de domínio no `commercial`:** `CustomerDetailHeader`,
`CustomerDetailSections`, `CustomerOverviewSection`,
`CustomerOrdersTable`, `CustomerBillingPanel`,
`CustomerPurchaseEvolutionChart` e `CustomerActivityTimelinePanel`.

### WF-04R-M — Conta 360 (mobile)

```text
← Minha carteira / ACME
┌─ PageHero · Conta ─────────────────────────┐
│ ACME [Atenção]                             │
│ código · loja · vendedor · atualizado      │
│ Fat. 12m · Em aberto · Pedidos · Entrega   │
│ Próxima ação: Tratar atraso                │
│ [Follow-up] [Atualizar]                    │
└────────────────────────────────────────────┘
Tabs com scroll horizontal →
┌ tabpanel em uma coluna ┐
│ pontos / evolução      │
│ tabelas → cards        │
└────────────────────────┘
```

O kit empilha os highlights do `PageHero`; não há accordion nem coluna sticky.
Nenhum conteúdo crítico depende de hover.

### Fronteira de integração

Minha carteira, Conta, OP e OV são páginas SPA nativas do `commercial`. Nenhuma
delas hospeda plugin externo, usa iframe, monta remote irmão ou oferece URL de
fallback para outro MFE. Dados de produção, pedidos, faturamento e oportunidades
são projeções próprias consumidas por HTTP da `api-delpi`/`commercial-api`.

---

## WF-05R — Administração de carteiras

**Rota:** `/apps/commercial/seller-portfolios`  
**URL:** `q`, `filter=all|active|inactive`, `id` (uuid). Defaults omitidos.  
**Dados:** commercial-api `seller-portfolios`  
**Permissão:** `commercial.seller-portfolios.manage`  
**Kit:** `PagePath`, `PageHero`, `ScopeChipBar`, `FilterBarShell`, `DataTable`, `DataRecordCard` / `InteractiveDataCard`, `HostContainedDialog` / `CommercialConfirmModal`.

```
← Portal Comercial / Administração / Carteiras

┌─ PageHero · Carteiras ──────────────── [+ Nova carteira] [Atualizar] ─┐
│ 1 carteira │ 0 ativas │ 1 inativa │ 0 clientes                       │
│ Situação [Todas 1] [Ativas 0] [Inativas 1]                           │
│ Buscar vendedor, usuário ou e-mail [________________]                │
└──────────────────────────────────────────────────────────────────────┘

┌─ Carteiras (1) ── [Tabela|Cards] ──┐  ┌─ Conta ─────────────────────────┐
│ Carteira   Usuário       Cli Status│  │ Robério Oliveira     [Inativa]  │
│ Robério ●  r***@delpi      0 Inativa│  │ Nome [Robério Oliveira] [Salvar]│
│                                    │  │ Buscar cadastro [________]      │
│                                    │  │ hits · [Vincular]               │
│                                    │  │ Na carteira: empty / DataTable  │
│                                    │  │ [Reativar][Transferir][Excluir] │
└────────────────────────────────────┘  └─────────────────────────────────┘
```

Linha selecionada = `?id=`. Sem coluna Ações. Sem `id`: empty «Selecione uma carteira».

**Card da lista (mobile / modo Cards):** nome, usuário, contagem, `StatusBadge`. O card inteiro seleciona.

**Dialog Nova carteira** — `UserDirectoryPicker` + nome + Cancelar / Criar.  
**Dialog Transferir** — origem travada, destino ativo, clientes pré-marcados, motivo obrigatório.  
**Inativar** — sai do escopo; vínculos ficam (`DELETE /{id}`).  
**Excluir** — apaga de vez (`DELETE /{id}/permanent`); «N clientes serão desvinculados» se `customer_count > 0`.

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
| Detalhe linha (OP + fabril) | WF-02R-D | `/open-orders/:filial/:pedido/:linha` + `/open-orders/:filial/:pedido/:linha/op/:op` |
| Detalhe OV (paridade dashboard) | WF-OV-D | `/analytics/opportunities/:n` |
| Minha carteira | WF-03R / WF-03R-M | `/customers` |
| Conta 360 | WF-04R / WF-04R-M | `/customers/:code/:store` |
| Config vendedores | WF-05 | `/seller-portfolios` |
| Avatar | WF-04R + WF-05 | commercial-api |
| URL interna código+loja | WF-04R | idem |
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
| Caminho de detalhe | `PagePath` |
| Equivalência mobile | `DataRecordCard` |
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
