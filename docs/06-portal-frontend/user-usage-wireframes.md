# Portal — Uso por usuário (wireframes)

> **Doc funcional:** [meu-uso-perfil-e-admin.md](./meu-uso-perfil-e-admin.md)  
> **API:** [estatisticas-uso-usuario.md](../04-core-api/estatisticas-uso-usuario.md)  
> **Código:** `portal/src/ui/usage/UserUsagePanel.tsx`  
> **Admin:** `portal/src/ui/admin/rbac/UserUsageTab.tsx`  
> **Perfil:** `portal/src/ui/MyProfile.tsx` (`#profile-usage`)

---

## Componentes reutilizados

| Elemento | Origem |
|----------|--------|
| KPIs | `StatsMiniKpi` / `StatsMiniKpiRow` |
| Gráficos | `StatsChartCard`, `AreaChart`, `BarChart` |
| Período | `Button size="sm" pressed` + `USER_USAGE_PERIOD_OPTIONS` |
| CSS analytics | `StatsTab.css` (`admin-stats__*`) |
| Perfil | `home-panel`, `HomePanelHeader`, `homeFadeUp` |
| Admin RBAC | `user-rbac-panel`, `PageChrome` tabs |

Escopo local: `UserUsagePanel.css` (`user-usage-panel`, variantes `--admin` / `--profile`).

---

## Painel compartilhado (`UserUsagePanel`)

Layout vertical (variante só altera chrome externo):

1. Toolbar — período 7/30/90d + «Atualizado em…»
2. Banner LGPD se `consent.granted === false`
3. Linha de 6 KPIs (aberturas, apps, tempo total, portal, sessão média, último uso)
4. 2× `AreaChart` — aberturas/dia e tempo/dia
5. 2× `BarChart` — apps por aberturas e por tempo
6. `BarChart` — rotas mais visitadas
7. Rodapé cobertura (sessões + eventos no período)

---

## Admin — aba Uso

`UserEditPage` → tab **Uso** → `UserUsageTab` (lazy fetch) → `UserUsagePanel variant="admin"`.

Mini-header opcional: `user-rbac-panel` com título «Uso na plataforma».

---

## Meu perfil — seção Meu uso

`/profile` → `#profile-usage` (`home-panel-wide profile-grid-usage`) após achievements, antes do launcher de apps.

`HomePanelHeader` + `UserUsagePanel variant="profile"` + CTA `/privacy` quando sem consentimento.

`data-tour="profile-usage"`.

---

## Responsivo

Herda breakpoints de `StatsTab.css`: ≤1100px charts em 1 coluna; ≤720px toolbar wrap.

Perfil: `profile-grid-usage` full-width em ≤980px.

---

## API

| Superfície | Endpoint |
|------------|----------|
| Admin | `GET /core-api/admin/rbac/users/{userId}/usage?periodDays=30` |
| Titular | `GET /core-api/me/usage?periodDays=30` |

Tipo compartilhado: `UserUsageStatistics` em `portal/src/data/userUsageTypes.ts`.
