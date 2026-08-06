# Portal Comercial — plano de implementação (status)

> Playbook: [PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md) § 11.

| Fase | Objetivo | Status |
|------|----------|--------|
| **F0** | Fichas KPI | `concluído` |
| **F1** | Scaffold `commercial-api` | `concluído` |
| **F2** | Portfolios + avatars | `concluído` |
| **F2b** | MFE paridade (scaffold) | `concluído` |
| **F2b harden** | UX real + clients + scope | `concluído` (ago/2026 — port PVA completo) |
| Wave G | Shell/IA, Home, Meu dia, worklist, timeline Conta 360 | **concluído Wave G+** (P0+P1; sem F2c) |
| **UX polish** | PageHero/TopBar; Home + Meu dia + Carteiras anti-redundância | **concluído** (ago/2026) — [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 1 |
| **Tasks P0** | Observação UI + nota na fila + filtro tipo | **concluído** (ago/2026) |
| **Tasks P1** | Responsável / reassign / fila equipe | **concluído** (ago/2026) |
| **Tasks P2** | Anexos | **backlog** — [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 3 |
| **Cutover dados** | backfill + `COMMERCIAL_PORTFOLIO_SOURCE=commercial` | `pronto` (ops) |
| **F2c** | Depreciar PVA | **pendente** — após homologação Comercial/QA |

## Paridade UX (F2b harden)

Portal Comercial absorveu a UX do PVA:

- Pedidos: KPIs, filtros, tabela ~16 cols, Excel, previsão OP, column picker, fonte, sort/paginação
- Carteira: agregação por pedidos, KPIs, gráfico 12m, tendência, detalhe com abas
- Admin: `SellerPortfoliosPage` via **commercial-api** (carteiras/avatars/enrichment)

Reads TOTVS continuam na api-delpi; estado Delpi na commercial-api.

## Cutover de dados (ops)

```bash
docker exec -it delpi-commercial-api \
  python scripts/backfill_from_pedidos_venda_abertos.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

## Wave G (CRM leve — sem F2c)

Plano: [.cursor/plans/wave_ui_crm_comercial_2e278317.plan.md](../../../.cursor/plans/wave_ui_crm_comercial_2e278317.plan.md)  
Homologação: [HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md) · Perfis: [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

### Matriz plano × código (ago/2026)

| Item do plano | Status | Evidência / nota |
|---------------|--------|------------------|
| **G0** kit `AlertQueue`, `ScopeChipBar`, `WorklistItem` | **Feito** | `plugins/plugin-ui` + `worklist-surface.css` + teste |
| **G0** `ActivityTimeline` | **Feito** | Alias de `Timeline` em `data/index.ts` |
| **G0** EmptyState onboarding (WF-11) / SavedViewChips | **Parcial / fora** | Empty states básicos em Home/Meu dia; SavedViewChips **não** |
| **G1** Shell + nav por objeto + ScopeChipBar | **Feito** | `PluginShell.tsx` |
| **G1** Remover CSS espelho kit no MFE | **Dívida** | Overrides `.delpi-ui-*` legados PVA em `customers.css` / `responsive.css` (pré-Wave G) |
| **G2** Home vendedor (AlertQueue + ≤2 cliques) | **Feito** | `HomePage.tsx` — sem atalhos redundantes (UX polish) |
| **G2** Home gestão (ROL/OTD/equipe api-delpi) | **Feito** | `commercialKpisApi.ts` + painel Gestão; KPIs clicáveis |
| **G2+** Hero SI + highlights vivos | **Feito** | `PageHero` + `HomeHeroMetricsContext` |
| **G3** Timeline conta + deep links propostas/dashboard | **Feito** | `CustomerActivityTimelinePanel.tsx` |
| **G4** Migration M2 parcial `tasks`/`activities` | **Feito** | `V003__tasks_activities.sql` (`description` no DB) |
| **G4** API worklist/tasks/activities | **Feito** | list/create/complete/**defer** + worklist; **sem** reassign multi-user |
| **G4** MFE `/my-day` + RBAC `worklist`/`followups` | **Feito** | Form prazo/prioridade/cliente/tipo; Adiar; Conta→follow-up; **sem** UI de `description` |
| **G4+** Meu dia PageHero / ScopeChipBar / empty CTA | **Feito** | `MyDayPage.tsx` (UX polish) |
| **Pós-G** Observação / responsável / anexos | **Backlog** | [UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) |
| **G5** Manifest capacidades (sem persona) | **Feito** | Sem `commercial.home.view` — Home usa `accounts.view` |
| **G5** `PERFIS-E-PERMISSOES.md` | **Feito** | Papéis sugeridos Minha Delpi |
| Docs DESIGN-IA / HOMOLOGAÇÃO / README | **Feito** | Wave G+ P0/P1 |
| Wireframes **WF-00 / 01R / 06R** | **Feito** | `WIREFRAMES.md` + DESIGN-IA |
| Playbook §9 → link perfis | **Pendente doc** | Catálogo longo ainda; Wave G ativa em PERFIS |
| Catálogo `plugin-ui` docs | **Parcial** | `UnderlineNav` no kit; entrada no catalog a completar |
| Testes unit worklist + smoke remotes | **Feito** | Ver HOMOLOGACAO-WAVE-G |
| Testes HTTP 403 RBAC worklist | **Feito** | `test_worklist_routes_rbac.py` (+ defer) |
| **Fora:** F2c, prospects, pipeline, forecast, F3–F4 | **Fora** | Intencional |

**Não inclui F2c** (ocultar PVA).

## F2c

Só após [HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md) 100% ✅ — ver [F2C-CUTOVER-RUNBOOK.md](./F2C-CUTOVER-RUNBOOK.md).

## Checklist gates

- [x] F0 KPI-FICHAS
- [x] F1 health + compose
- [x] F2 migrations + dual-read + transfer audit
- [x] F2b harden — paridade UX open-orders/carteira com PVA
- [x] Wave G / G+ — worklist / Meu dia / RBAC / Home gestão / Conta follow-up
- [x] UX polish Home + Meu dia ([UX-E-TASKS-EVOLUTION.md](./UX-E-TASKS-EVOLUTION.md) § 1)
- [x] Tasks P0 Observação na UI + filtro tipo
- [x] Tasks P1 Responsável / reassign / fila equipe
- [ ] Tasks P2 Anexos (volume persistente)
- [ ] Homologação Comercial ([HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md))
- [ ] Homologação assinada Wave G+ ([HOMOLOGACAO-WAVE-G.md](./HOMOLOGACAO-WAVE-G.md))
- [ ] F2c flip menu + redirects
