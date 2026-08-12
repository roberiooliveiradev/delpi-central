# Design / IA — Portal Comercial

> **Status:** IA hub 2026 — refino visual + IA de informação  
> **Produto:** Portal Comercial · `id` `commercial` · `/apps/commercial`  
> **UI kit:** `@delpi/plugin-ui` · prefixo MFE `cm-` · root `.dashboard-commercial`  
> **Wireframes:** [WIREFRAMES.md](./WIREFRAMES.md) · **Gestão:** [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) · **Perfis:** [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

O Portal Comercial é o hub operacional e de diagnóstico: **Início** (launcher), **Visão geral** (dashboard BI), **Minhas tarefas**, pedidos, Conta 360, deep pages via Início (Propostas ADY, OTD, Oportunidades) e **Administração** — páginas **nativas**.

## Princípios de informação

| Camada | Superfície | Objetivo |
|--------|------------|----------|
| **Hub Início** | Início (`/`) | Eventos **ou** chip «Fila em dia» → busca → favoritos → recentes → seções (`SectionRouteCard`) |
| **Diagnosis** | Visão geral (`/overview`) | Filtros + KPIs ≤8 + evolução ROL + funil — **sem** faixa Aprofundar |
| **Focus / Action** | Minhas tarefas, Meus pedidos, OTD, Oportunidades, Propostas ADY | Filas e listas (entrada: top, Início ou Ctrl+K) |
| **Detail** | Conta, detalhe OV/ADY/linha/OP | Investigation |
| **Admin** | Administração (`/administration/*`) | Painel · Carteiras · Membros (`seller-portfolios.manage`) |

## Catálogo rápido (o que cada página traz)

| Página | Traz | Não traz |
|--------|------|----------|
| Início | Saudação, KPIs carteira, eventos/chip, busca, favoritos, recentes, seções | BI ROL/funil |
| Visão geral | Filtros (+carteira), KPIs, ROL, funil | Drills Aprofundar, prévia OV, Equipe |
| Minhas tarefas | Fila follow-ups | Pedidos / ROL |
| Meus pedidos | Linhas abertas, chip Atraso | Série OTD histórica |
| Minha Carteira / Conta | Clientes; Conta com aba **Oportunidades** real | BI consolidado do período |
| OTD (Início) | OTD% período, série SC/ES, linhas | Chip operacional do dia |
| Oportunidades (Início) | Lista OV global | Documentos ADY |
| Propostas | ADY + PDF | OV AD1010 |
| Administração | Carteiras / membros | Ranking «Equipe» separado |
| `/analytics/team` | **Redirect → Administração** | — |

Detalhe: [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md) § Catálogo de informação.

## Navegação (alvo)

```text
Shell: TopBar flush + UnderlineNav
Início | Visão geral | Minhas tarefas | Meus pedidos | Minha Carteira | Administração†
```

- **Início:** PageHero (shell + CTA contextual) + stack Eventos/chip → busca → favoritos → recentes → grid de seções — **sem** BI da Visão geral.
- **Visão geral:** PageHero + filtros (datas, competência, filial, segmento, **carteira**) + KPIs + charts; **sem** Aprofundar.
- **Minhas tarefas:** `/my-tasks` (alias `/my-day`); atalho hub `?createTask=1`.
- Escopo no chrome = **identidade**; filtro de carteira nas listas/analytics = `SellerScopeFilter`.
- Propostas / OTD / Oportunidades: **não** na top — **catálogo Início** / CommandPalette (não drill Overview).
- Equipe analítica: **depreciada** → Administração.
- Atalho global: **Ctrl/Cmd+K** → `CommandPalette` host-contained.

### Administração

Subnav: **Painel · Carteiras · Membros**. Alias `/seller-portfolios` → aba Carteiras.

## Chrome de página (contrato)

```text
[PagePath?] → [UnderlineNav?] → PageHero (actions)
  → filtros (FiltersKit | FilterBarShell | SellerScopeFilter | chips)
→ SectionCard · MetricCard · charts · DataTable · Empty/Loading · StatusBadge
```

- Deprecar `cm-page-header-row` como chrome raiz.
- Clique tabela→detalhe: `onRowClick` + coluna identidade link; `interactive: true` só com ação própria distinta.

## Helps

Fonte única: `plugins/commercial/src/content/helpTooltips.ts` (`CM_HELP`). PageHero, SectionCard.hint, Field.hint, titleHint KPI, shell nav — sem literais PT de help no JSX.

## Alinhamento mercado

| Tema | Referência | Decisão Delpi |
|------|------------|---------------|
| Top nav + home launcher | Portal RH (IA) | Sim — visual Comercial (**não** clonar CSS RH) |
| Apps main + eventos side | Portal RH | **Supersedido** — stack vertical Eventos → busca → seções |
| Home = ação | HubSpot / Linear | Eventos + catálogo + Ctrl+K; BI em `/overview` |
| Tiles hierárquicos | SAP Fiori / hub SaaS | `SectionRouteCard` (seção → rotas) |
| Busca de apps | Notion / Linear | `CatalogSearchBar` + `?q=` + CommandPalette |
| Filtros + KPIs + funil | dashboard-comercial (legado) | Visão geral nativa (**não** hostear) |
| Worklist | Pipedrive Activities | «Minhas tarefas» / Eventos Início |
| Row → detalhe | Grids admin + link identidade | C17 DataTable |

## Alinhamento `.cursor`

| Regra | Aplicação |
|-------|-----------|
| `plugins-reusable-components` | Kit-first; zero CSS `.delpi-ui-*` no MFE |
| `plugins-visual-design-system` | Tokens `--cm-*` → `--delpi-ui-*` |
| `english-code-identifiers` | Paths EN; labels PT |
| `application-bounded-context-decoupling` | Membership só commercial-api; analytics com `customer_codes` TOTVS (sem `portfolio_id` na api-delpi) |
| `mfe-modal-host-contained` | Dialogs admin |
| `infra-sequential-container-startup` | Rebuild remote → mfe |
| `test-and-commit` | Cada subetapa: test → commit → push |

## Componentes kit (reconciliado — wave refino)

Bindings via `plugins/commercial/src/app/commercialUi.ts` (`Commercial*` / `createDashboard*`). **Zero** CSS `.delpi-ui-*` no MFE.

| Área | Kit | Binding | Estado |
|------|-----|---------|--------|
| Hero / Path / Subnav | PageHero, PagePath, UnderlineNav | CommercialPageHero/Path/UnderlineNav | Usar |
| Top / Escopo | TopBar, ScopeChipBar, StatusBadge | Commercial* | Usar |
| Filtros | FiltersKit, Date/Select/MultiSelect | cmFiltersKit, Commercial*Field | Usar |
| Carteira (filtro) | SelectField | SellerScopeFilter | Usar |
| Launcher card (legado) | NavigationCard `density=featured` | CommercialNavigationCard | Só fora do Início |
| Hub seção→rotas | SectionRouteCard | CommercialSectionRouteCard | Usar (Início) |
| Busca catálogo | CatalogSearchBar | CommercialCatalogSearchBar | Usar (Início) |
| Command palette | CommandPalette (host-contained) | CommercialCommandPalette | Usar (shell) |
| Ações | ActionButton | CommercialActionButton | Usar |
| KPI | MetricKpiCard | CommercialMetricCard (`onClick` opcional) | Usar |
| Seção / Empty / Loading | SectionCard, EmptyState, LoadingActivityCard | Commercial* | Usar |
| Tabela / Badge | DataTable (`onRowClick`, `rowClick` stop/propagate), StatusBadge | CommercialDataTable, CommercialStatusBadge | Usar |
| Alertas / Worklist | AlertQueue, WorklistItem | Commercial* | Usar |
| Help | HelpTooltip + `CM_HELP` | — | Usar |
| Charts | Recharts + EmptyState | SectionCard | MFE-only |
| Layout Início stack | — | CSS `cm-home-stack` / `cm-home-sections-grid` | MFE-only |
| Faixas Favoritos / Recentes | — | CSS `cm-home-chip-row*` (só spacing) | MFE-only |

Catálogo de rotas: `plugins/commercial/src/content/pluginRouteCatalog.ts` (caps + keywords + kind create/navigate).

### Backlog kit — hub Início (polish ago/2026)

Entrega atual: pin Lucide centralizado, foco único no `CatalogSearchBar`, polish visual dos cards/busca, alinhamento das faixas no MFE. **Não** redesenhar a stack do HomePage.

| Sugestão | Papel | Por quê |
|----------|-------|---------|
| `HubChipRow` (kit) | Favoritos / Recentes como primitivo | Hoje ActionButton ghost solto; chip com pin/remove e densidade |
| `PinnedRouteChip` | Chip favorito com estrela + label | Substitui botão genérico na faixa |
| Ícone Lucide por rota no `SectionRouteCard` (prop opcional) | Hierarquia visual 2º nível | Mercado (SAP Fiori / hub SaaS) |
| Empty quiet da busca inline no field | Zero empty SectionCard | Já parcialmente; reforçar |
| CommandPalette | Manter atalho; polish igual ao search | Paridade visual |

## UX

- Uma ação primária por seção; ≤ 2 cliques do Início até a ação.
- Loading/erro por seção (`allSettled`); cards launcher omitidos sem capability.
- Mobile ≤768: UnderlineNav com scroll; botões ≥44px.
- CTA Administração só com `manage`.

## Fora / backlog

| Item | Doc |
|------|-----|
| Export OTD/Opp; worklist summary leve | GESTAO-A-VISTA backlog |
| Paridade KPI WEG / NB absoluto | GESTAO-A-VISTA |
| Ranking Equipe (só se dentro de Admin) | futuro |
| Observação, anexos, reminder | UX-E-TASKS-EVOLUTION |
| F2c PVA, Wave H | IMPLEMENTATION-PLAN |
