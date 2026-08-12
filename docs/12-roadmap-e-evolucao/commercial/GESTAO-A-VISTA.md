# Gestão à vista — Portal Comercial (consolidação nativa)

> **Status:** IA hub 2026 — top nav Início · Visão geral · Minhas tarefas · … · Administração · zero hosteamento · `commercial.analytics.view` para BI  
> **Produto:** `plugins/commercial` · `/apps/commercial`  
> **Plano:** Início launcher + Visão geral top-level + Administração hub + deep pages (OTD/Opp/Equipe/Propostas)

## Norte

| Camada | Papel |
|--------|--------|
| MFE `commercial` | Única UX de produto a evoluir — páginas **nativas** |
| `commercial-api` | Estado Delpi (carteiras, Minhas tarefas, avatars, realtime) |
| `api-delpi` | TOTVS HTTP (`/commercial/*`, `/propostas-comerciais`, `/pedidos-venda-abertos`) |
| MFEs irmãos | Permanecem no menu; **não** hostear/deep-link como entrega |

**Proibido:** iframe / Module Federation / deep link obrigatório para `dashboard-commercial`, `propostas-comerciais` ou PVA.

## Nav alvo (top bar)

```text
Início | Visão geral | Minhas tarefas | Meus pedidos | Minha Carteira | Administração†
```

† `seller-portfolios.manage`. Visão geral exige `analytics.view`. Minhas tarefas exige `worklist.view`.

| Item top | Path | Capacidade |
|----------|------|------------|
| Início | `/` | `accounts.view` |
| Visão geral | `/overview` | `analytics.view` |
| Minhas tarefas | `/my-tasks` (alias `/my-day`) | `worklist.view` |
| Meus pedidos | `/open-orders` | `accounts.view` |
| Minha Carteira | `/customers` | membership ou team/manage |
| Administração | `/administration` | `seller-portfolios.manage` |

**Fora da top bar** (launcher Início e/ou drill da Visão geral):

| Página | Path |
|--------|------|
| Propostas ADY | `/proposals` |
| OTD | `/analytics/otd` |
| Oportunidades OV | `/analytics/opportunities` |
| Equipe (analítica) | `/analytics/team` |

**Redirects:** `/analytics` e `/gestao` → `/overview`. `/seller-portfolios` → `/administration/seller-portfolios`.

**Administração subnav:** Painel · Carteiras · Membros.

## Início vs Visão geral

| | Início `/` | Visão geral `/overview` |
|--|------------|-------------------------|
| Papel | Launcher + eventos/interações (worklist preview) | BI: KPIs, filtros, charts ROL/funil |
| Não fazer | Duplicar faixa BI completa | Hospedar CRUD de carteiras |

## Duas “propostas”

| Nome no Portal | TOTVS | API | Uso |
|----------------|-------|-----|-----|
| **Oportunidades (OV)** | AD1010 | `/commercial/proposals` | Funil / ciclo — drill Gestão/Visão geral |
| **Propostas (documento)** | ADY010 | `/propostas-comerciais` | Documento + PDF — launcher (não top nav) |

Escopo ADY: **sem** filtro membership nesta wave (lista global com `proposals.view`).
O chip Escopo no chrome = **identidade da sessão**, não filtro desta lista
(`PROPOSALS_CONTENT.list.scopeNote` / `CM_HELP.proposals.scopeNote`).

## Catálogo de métricas (Visão geral)

Fonte MFE: `plugins/commercial/src/content/overviewMetricsCatalog.ts`.

| id | Label |
|----|-------|
| `rol_head_office` | ROL vs meta |
| `rol_branch` | ROL filial |
| `closing_rate` | Conversão |
| `otd` | OTD |
| `new_business` | Novos negócios |
| `rol_series` | Evolução de ROL |
| `funnel` | Funil |
| `ov_table` | Oportunidades |

## Permissões (capacidades — sem cargo)

| Code | Função |
|------|--------|
| `commercial.accounts.view` | Portal, pedidos, carteira, conta |
| `commercial.worklist.view` / `followups.manage` | Minhas tarefas |
| `commercial.seller-portfolios.manage` | Administração (Painel/Carteiras/Membros) |
| `commercial.audit.view` | Auditoria |
| `commercial.analytics.view` | Visão geral + OTD + Oportunidades |
| `commercial.proposals.view` / `.export` | Propostas ADY (launcher) |
| `commercial.accounts.team.view` | Filtro multi-vendedor / Equipe analítica |
| `commercial.worklist.team.view` | Minhas tarefas `scope=team` |

### Equipe (analítica)

Universo = carteiras **ativas**. Filtro MFE: `accounts.team.view || manage`. CTA admin manage-gated → Administração.

## Filtros Visão geral / OTD / Opp

| | |
|--|--|
| URL | `competence`, `start_date`, `end_date`, `branch`, `customer_segment` |
| sessionStorage | `delpi.commercial.analytics.filters` |
| Hook | `useAnalyticsFilters` |
| Datas v1 | **2× DateField** (+ competence) — sem DateRangeField |

## Backend P0 (realtime)

`portfolio.changed` deve fan-out para sala WS **`team`** (gestores manage), além de `user:{member}`.
**Status:** entregue em `commercial_realtime_notify.notify_portfolio_changed`.

## Backlog — export (não nesta wave)

Decisão D13: **não** implementar export OTD/Opp / Visão geral nesta wave.

| Superfície | Formato desejado (futuro) | Notas |
|------------|---------------------------|--------|
| Visão geral (KPIs / série ROL) | CSV ou Excel | Respeitar filtros `useAnalyticsFilters` |
| OTD (painel + linhas) | Excel | Incluir status/promessa; detalhe linha fora |
| Oportunidades OV | Excel | Colunas da lista + filtros do período |
| WEG / novos negócios | CSV | Só se houver pedido de produto |

Já existe export na Administração: **Exportar matriz** (org / load-summary) — não confundir com este backlog.

## Backlog (outros — não nesta wave)

- `GET /me/worklist` preview leve; list portfolios sem `customers[]`
- Membership em ADY/OTD/OV
- P3 CRM; remoção de plugins irmãos

## Conteúdo PT

Textos de UI em `plugins/commercial/src/content/` (não hardcode em JSX).

## Bloqueios explícitos

- **P3 CRM** só com pedido explícito
- **DateRangeField** fora da v1
- **Remoção** de plugins irmãos só no futuro (`cleanup-later`)
- Endpoints `new-clients-*` / `rol/by-customer` fora
- PVA membership / regras novas no PVA

## Referências

- [WIREFRAMES.md](./WIREFRAMES.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md)
- [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) · [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)
