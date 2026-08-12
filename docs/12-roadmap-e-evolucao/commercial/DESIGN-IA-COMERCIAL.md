# Design / IA — Portal Comercial

> **Status:** IA hub 2026 — [GESTAO-A-VISTA.md](./GESTAO-A-VISTA.md)  
> **Produto:** Portal Comercial · `id` `commercial` · `/apps/commercial`  
> **UI kit:** `@delpi/plugin-ui` · prefixo MFE `cm-` · root `.dashboard-commercial`  
> **Wireframes:** [WIREFRAMES.md](./WIREFRAMES.md) · **Perfis:** [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

O Portal Comercial é o hub operacional e de diagnóstico: **Início** (launcher), **Visão geral** (BI), **Minhas tarefas**, pedidos, Conta 360, deep pages (Propostas ADY, OTD, OV, Equipe) e **Administração** — páginas **nativas**.

## Princípios de informação

| Camada | Superfície | Objetivo |
|--------|------------|----------|
| **Launcher** | Início (`/`) | Hero + eventos/interações + grid de funcionalidades (gated) |
| **Diagnosis** | Visão geral (`/overview`) | KPIs, filtros, charts; drills OTD/Opp/Equipe |
| **Focus / Action** | Minhas tarefas, Pedidos, Propostas ADY | Filas e documentos |
| **Detail** | Minha Carteira, Conta, detalhe OV/ADY/OTD | Investigation |
| **Admin** | Administração (`/administration/*`) | Painel · Carteiras · Membros (`seller-portfolios.manage`) |

## Navegação (alvo)

```text
Shell: TopBar flush + UnderlineNav
Início | Visão geral | Minhas tarefas | Meus pedidos | Minha Carteira | Administração†
```

- **Início:** `PageHero` + card Eventos (worklist preview) + launcher — **sem** duplicar BI da Visão geral.
- **Visão geral:** filtros analytics + KPIs ≤8 + charts; atalhos drill.
- **Minhas tarefas:** antigo «Meu dia»; path `/my-tasks` (alias `/my-day`); badge = overdue+today.
- Escopo via chip no chrome (identidade, não filtro de página).
- Propostas / OTD / Opp / Equipe: **não** na top — só launcher ou drill.

### Administração

Subnav: **Painel · Carteiras · Membros**. Alias `/seller-portfolios` → aba Carteiras.

## Alinhamento mercado

| Tema | Referência | Decisão Delpi |
|------|------------|---------------|
| Top nav curta + home launcher | Portal RH (IA) | Sim — visual Comercial (não clonar CSS RH) |
| Eventos no home | Feed de interações | Worklist/tarefas — não aniversários RH |
| BI em página própria | Manager dashboard | `/overview` |
| Worklist | Pipedrive Activities | Label «Minhas tarefas» |

## Alinhamento `.cursor`

| Regra | Aplicação |
|-------|-----------|
| `plugins-reusable-components` | Kit-first; zero CSS `.delpi-ui-*` no MFE |
| `plugins-visual-design-system` | Tokens `--cm-*` → `--delpi-ui-*` |
| `english-code-identifiers` | Paths EN; labels PT |
| `application-bounded-context-decoupling` | Membership só commercial-api; ADY/OTD/OV sem membership |
| `mfe-modal-host-contained` | Dialogs admin |
| `infra-sequential-container-startup` | Rebuild remote → mfe |
| `test-and-commit` | Cada subetapa: test → commit → push |

## Componentes kit

| Componente | Uso |
|------------|-----|
| `PageHero` | Início, Minhas tarefas, Visão geral, Admin |
| `TopBar` + `UnderlineNav` | Shell |
| `ViewTransition` | Troca de telas |
| `SectionCard` / `SimpleKpiCard` | Launcher cards / KPIs |
| `AlertQueue` / worklist items | Eventos Início + Minhas tarefas |
| `EmptyState` + `ActionButton` | Empties manage-gated |
| `OrgMembershipFlow` | Organização Carteiras |

## UX

- Uma ação primária por seção; ≤ 2 cliques do Início até a ação.
- Loading/erro por seção (`allSettled`); cards launcher omitidos sem capability.
- Mobile ≤768: UnderlineNav com scroll; botões ≥44px.
- CTA Administração só com `manage`.

## Fora / backlog

| Item | Doc |
|------|-----|
| Export OTD/Opp; worklist summary leve | GESTAO-A-VISTA backlog |
| Observação, anexos, reminder | UX-E-TASKS-EVOLUTION |
| F2c PVA, Wave H | IMPLEMENTATION-PLAN |
