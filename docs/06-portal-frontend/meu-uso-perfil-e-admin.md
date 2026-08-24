# Portal — Meu uso (perfil) e Uso por usuário (Admin)

> **Código:** `portal/src/ui/usage/`  
> **API:** [estatisticas-uso-usuario.md](../04-core-api/estatisticas-uso-usuario.md)  
> **Wireframes:** [user-usage-wireframes.md](./user-usage-wireframes.md)

Painel compartilhado de analytics individuais: apps mais acessados, tempo de uso, rotas e séries temporais. **Render-only** — agregação na Core API.

---

## Superfícies

| Onde | Rota UI | API | Lazy load |
|------|---------|-----|-----------|
| **Admin** | `/admin/users/:id` → aba **Uso** | `GET /core-api/admin/rbac/users/{id}/usage` | Sim — só ao abrir a aba |
| **Titular** | `/profile` → `#profile-usage` | `GET /core-api/me/usage` | Não — carrega com a página |

Permissão admin: herda `rbac.manage` da área Admin / edição de usuário.

---

## Módulos

```text
portal/src/
├── data/
│   ├── userUsageTypes.ts          UserUsageStatistics (tipo compartilhado)
│   ├── adminApi.ts                getAdminUserUsageStatistics
│   └── coreApi.ts                 getMyUsageStatistics
└── ui/usage/
    ├── UserUsagePanel.tsx         Painel compartilhado (variant admin | profile)
    ├── UserUsagePanel.css         Toolbar, banner consent, responsivo
    ├── userUsageLabels.ts         Textos PT-BR
    ├── useAdminUserUsageStats.ts  Hook admin (userId + periodDays)
    └── useMyUsageStats.ts         Hook titular (/me)
```

**Admin:** `portal/src/ui/admin/rbac/UserUsageTab.tsx` — wrapper fino (hook + mini-header + panel).

**Perfil:** seção em `MyProfile.tsx` com `HomePanelHeader` + `UserUsagePanel variant="profile"`.

---

## UX e estados

| Estado | Comportamento |
|--------|---------------|
| Loading | Texto «Carregando uso…» (`admin-stats__state`) |
| Erro | Mensagem + botão «Tentar novamente» |
| Sem consentimento | Banner no topo; KPIs/gráficos zerados; perfil link → `/privacy` |
| Período 7/30/90d | `Button pressed`; refetch automático no hook |

Componentes visuais reutilizados de **Estatísticas → Engajamento**: `StatsMiniKpi`, `StatsChartCard`, `AreaChart`, `BarChart`, classes `admin-stats__*` (`StatsTab.css`).

---

## Período e refresh

- Default: **30 dias**
- Opções: 7, 30, 90 (`USER_USAGE_PERIOD_OPTIONS`)
- Admin: sem auto-refresh periódico (carrega ao trocar aba/período)
- Perfil: mesmo comportamento do hook admin (sem polling 45s do engajamento global)

---

## LGPD na UI

- `consent.granted === false` → banner + zeros; **não** tratar como erro de API
- Admin: texto informativo (titular ativa em Privacidade)
- Perfil: CTA «Ativar nas preferências de privacidade» → `/privacy`

---

## Tour do portal

`data-tour="profile-usage"` na seção do perfil (opcional para gamificação futura).

---

## Build e testes

```bash
cd portal && npm run build
```

Validação manual (checklist):

1. Admin → usuário com consentimento → aba Uso coerente com ranking global
2. `/profile` → mesmos totais do admin para o mesmo usuário/período
3. Revogar consentimento → banner + zeros
4. Trocar 7/90 dias altera séries e KPIs

Deploy: rebuild `core-api` + `portal` após alterações de contrato.

---

## Relacionados

- [admin-estatisticas.md](./admin-estatisticas.md) — engajamento **global** (DAU/WAU/MAU)
- [rastreamento-uso-apps.md](../04-core-api/rastreamento-uso-apps.md) — coleta Socket/HTTP
- [visao-geral-portal.md](./visao-geral-portal.md) — estrutura `src/ui/`
