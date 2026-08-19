# Gestão à vista — Portal Comercial (consolidação nativa)

> **Status:** IA hub 2026 — top nav + Visão geral BI + Início launcher · zero hosteamento · RBAC condensado `commercial.access` (BI/produto) — ver [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)  
> **Produto:** `plugins/commercial` · `/apps/commercial`  
> **Plano:** refino visual + IA de informação (Equipe→Admin; Opp Conta+Início; OTD Início; filtro carteira analytics)

## Norte

| Camada | Papel |
|--------|--------|
| MFE `commercial` | Única UX de produto a evoluir — páginas **nativas** |
| `commercial-api` | Estado Delpi (carteiras, Minhas tarefas, avatars, realtime); resolve clientes da carteira para filtro analytics |
| `api-delpi` | TOTVS HTTP (`/commercial/*`, …); filtro opcional **`customer_codes`** (sem `portfolio_id` / membership) |
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

**Fora da top bar** (launcher Início):

| Página | Path |
|--------|------|
| Propostas ADY | `/proposals` |
| OTD | `/analytics/otd` |
| Oportunidades OV | `/analytics/opportunities` |

**Nav futuro (ata alinhamento 2):**

| Página | Path (proposto) | Nota |
|--------|-----------------|------|
| Reunião Diretoria | a definir após modelo Junior/Laércio | Stub WF-DIR — [ATA-ALINHAMENTO-AGO2026-2.md](./ATA-ALINHAMENTO-AGO2026-2.md) §34 |
| GR de Vendas | **não** no Portal | Implementação no [tv-dashboard](../../../plugins/tv-dashboard/README.md); Comercial alimenta KPIs — **sem** atalho para o TV |

**Depreciado:** Equipe (`/analytics/team`) → **redirect** `/administration`.

**Redirects:** `/analytics` e `/gestao` → `/overview`. `/seller-portfolios` → `/administration/seller-portfolios`. `/analytics/team` → `/administration`.

**Administração subnav:** Painel · Carteiras · Membros.

## Catálogo de informação por página

| Página | Pergunta | Obrigatório | Não trazer |
|--------|----------|-------------|------------|
| Início | O que fazer agora / para onde ir? | Saudação; KPIs carteira; eventos; launcher | BI ROL/funil |
| Visão geral | Como está o comercial no período? | Filtros (+**carteira** + **Unidade** SC/ES + atalhos período); KPIs (ROL, **carteira aberta agora**, **gap vs meta**, hit rate, OTD…); painel **carteira no tempo**; ROL Dia–Ano + **YoY**; funil; série hit rate + **YoY**; **export** ROL/funil/série conversão | Aprofundar; prévia OV; export OTD/Opp; soma ROL+carteira |
| Minhas tarefas | Qual minha fila? | Buckets; CRUD tarefa | Pedidos / ROL |
| Meus pedidos | Quais linhas operar? | Escopo carteira; chip **Atraso**; **Concentrar** (horizonte); tabela | Série OTD histórica |
| Minha Carteira | Quem são os clientes? | Lista; clique→Conta; atalho **Ver atrasos** → pedidos | BI período |
| Conta · Opp | Quais OVs deste cliente? | Lista filtrada por código/loja | Placeholder CTA |
| OTD | Pontualidade no período? | %; série SC/ES; stats atraso; reincidência; top 10 atrasos/promessas; linhas com busca/sort/filtro | Chip do dia (Pedidos); export |
| Oportunidades | Quais OVs no período (global)? | Lista + busca | ADY |
| Propostas | Documentos ADY / PDF? | Lista + detalhe | OV AD1010 |
| Administração | Como gerir carteiras? | Painel / Carteiras / Membros | Ranking Equipe separado |

## Início vs Visão geral

| | Início `/` | Visão geral `/overview` |
|--|------------|-------------------------|
| Papel | Launcher (main) + eventos (side) | BI: filtros Unidade SC/ES, KPIs (carteira aberta, gap vs meta, horizonte), ROL + YoY, funil, série hit rate + YoY, export |
| Não fazer | Duplicar faixa BI completa | Faixa Aprofundar; hospedar CRUD carteiras |

## Duas “propostas”

| Nome no Portal | TOTVS | API | Uso |
|----------------|-------|-----|-----|
| **Oportunidades (OV)** | AD1010 | `/commercial/proposals` | Lista global (Início) + aba Conta. Censo: 3767 OVs; funil `000001` é 82% e **não** é o recorte LMP das rotas `/lmp`. Chave `filial+nropor`. Ver [crm-sigatec.md](../../../../api-delpi/docs/api/padroes-totvs/crm-sigatec.md). |
| **Propostas (documento)** | ADY010 | `/propostas-comerciais` | Documento + PDF — launcher. `ADY_FILIAL` vazio nesta base; não join por filial com AD1. |

Escopo ADY: **sem** filtro membership nesta wave. Chip Escopo chrome = identidade (`PROPOSALS_CONTENT.list.scopeNote`).

## Catálogo de métricas (Visão geral)

Fonte MFE: `plugins/commercial/src/content/overviewMetricsCatalog.ts`.

| id | Label |
|----|-------|
| `rol` | ROL vs meta |
| `rol_weg` | ROL WEG |
| `rol_new_business` | ROL novos negócios |
| `closing_rate` | Conversão |
| `open_portfolio` | Carteira aberta (agora) |
| `gap_to_target` | Gap vs meta ROL |
| `open_portfolio_horizon` | Carteira no tempo (buckets) |
| `otd` | OTD |
| `new_business_pct` | % novos negócios |
| `rol_series` | Evolução de ROL (+ YoY opcional) |
| `closing_rate_series` | Evolução hit rate (+ YoY opcional) |
| `funnel` | Funil |

(`ov_table` removido do hub — lista OV não na Overview.)

## Permissões (capacidades — sem cargo)

| Code | Função |
|------|--------|
| `commercial.accounts.view` | Portal, pedidos, carteira, conta |
| `commercial.worklist.view` / `followups.manage` | Minhas tarefas |
| `commercial.seller-portfolios.manage` | Administração |
| `commercial.audit.view` | Auditoria |
| `commercial.analytics.view` | Visão geral + OTD + Oportunidades |
| `commercial.proposals.view` / `.export` | Propostas ADY |
| `commercial.accounts.team.view` | Filtro multi-vendedor / admin team scope |
| `commercial.worklist.team.view` | Minhas tarefas `scope=team` |

## Filtros Visão geral / OTD / Opp

| | |
|--|--|
| URL | `competence`, `start_date`, `end_date`, `branch` (Unidade SC/ES), `customer_segment`, **`seller_id`** (carteira) |
| sessionStorage | `delpi.commercial.analytics.filters` |
| Hook | `useAnalyticsFilters` + sync `PortfolioScopeContext.sellerIdFilter` |
| Carteira → dados | commercial-api clientes → api-delpi `customer_codes` (TOTVS puro) |
| Datas v1 | **2× DateField** (+ competence) — sem DateRangeField |

Ver [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md): membership no Portal; api-delpi sem `portfolio_id`.

## Backend P0 (realtime)

`portfolio.changed` → sala WS **`team`** + `user:{member}`.  
**Status:** entregue em `commercial_realtime_notify.notify_portfolio_changed`.

## Export (D13 + exceção Visão geral)

| Superfície | Export tabular CSV/Excel/PDF |
|------------|------------------------------|
| **Visão geral** — Evolução ROL + Funil + série conversão (colunas prior se YoY) | **Sim** (exceção D13 — paridade dashboard) |
| OTD / Oportunidades | **Não** nesta wave (D13 permanece) |

Rótulos de unidade: canônico `@delpi/plugin-ui` (`formatOperationalUnitCode` / SC = Santa Catarina, ES = Espírito Santo) — UI nunca mostra `"01"`/`"02"` como rótulo quando o código é conhecido. Campo de filtro analytics: **Unidade (indicadores)**.

## Backlog (outros)

- `GET /me/worklist` preview leve
- Membership automático ADY (lista)
- Ranking Equipe **dentro** de Administração (se produto pedir)
- Paridade KPI WEG / NB absoluto
- P3 CRM; remoção de plugins irmãos

## Conteúdo PT

`plugins/commercial/src/content/` + `helpTooltips.ts` (`CM_HELP`).

## Bloqueios explícitos

- **P3 CRM** só com pedido explícito
- **DateRangeField** fora da v1
- **Remoção** de plugins irmãos só no futuro
- Endpoints `new-clients-*` / `rol/by-customer` fora
- PVA membership / regras novas no PVA
- `portfolio_id` em rotas api-delpi

## Referências

- [WIREFRAMES.md](./WIREFRAMES.md) · [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md) · [DESIGN-IA-COMERCIAL.md](./DESIGN-IA-COMERCIAL.md)
- [SCOPE-OWNERSHIP.md](./SCOPE-OWNERSHIP.md) · [PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)

## Homologação (refino visual)

Rebuild sequencial (dev, ago/2026): `plugin-ui` → `commercial` → `api-delpi` (core) — imagens recriadas; sem regressão de build.

| # | Papel / cap | Conferir | Status build |
|---|-------------|----------|--------------|
| 1 | Vendedor | Início 2 colunas; sem Equipe no launcher; Minhas tarefas | Pronto p/ smoke UI |
| 2 | Analytics | Visão geral sem Aprofundar; filtro carteira†; OTD/Opp via Início | Pronto p/ smoke UI |
| 3 | Team | Filtro carteira; `/analytics/team` → Admin | Redirect + testes |
| 4 | Manage | Administração; empty pedidos → Admin | Pronto p/ smoke UI |
| 5 | Carteira tabela | Clique linha **e** coluna Cliente → Conta (C17) | Testes estruturais |
| 6 | Conta Opp | Lista OV real (não placeholder) | Entregue |
| 7 | Helps | `CM_HELP` matriz + PageHero/filtros | Teste C16 |

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build commercial
# C8.7 customer_codes (api-delpi vive na fase core em dev):
./infra/scripts/up-dev-sequential.sh --fase core --build api-delpi
```
