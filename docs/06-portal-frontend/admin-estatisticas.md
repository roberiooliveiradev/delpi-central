# Portal — Admin: Estatísticas

> **Código:** `portal/src/ui/admin/tabs/StatsTab.tsx`  
> **API:** `GET /core-api/admin/statistics` (`adminApi.getAdminStatistics`)

---

## 1. Aba Estatísticas

Primeira aba do `/admin`, com **subpáginas** internas e tema de analytics via tokens globais do portal (`--stats-*`, `--chart-*` em `portal/src/index.css`), no mesmo espírito do plugin Strategic Indicators: paleta saturada e legível tanto no modo claro quanto no escuro.

| Subpágina | Conteúdo |
|-----------|----------|
| **Visão geral** | KPIs + donuts resumidos (usuários, apps, notificações) |
| **Usuários** | Online, logins, ativos/inativos, **tour do portal (exploradores)** |
| **Aplicações** | Quem usa cada app agora, top 30d, fantasmas (sem backend-only), trackable vs backend-only, tipos |
| **Acesso RBAC** | Rankings de papéis/grupos e vínculos |
| **Notificações** | Status dos envios de campanha |
| **Acompanhamento** | Tour gamificado — exploradores, conclusões, ranking semanal (`GET /core-api/admin/portal-tour/*`) |

Código em `portal/src/ui/admin/stats/` (páginas em `stats/pages/`, acompanhamento do tour em `StatsTourPage.tsx` + `usePortalTourAdminMonitoring.ts`). Paleta em `statsTheme.ts` (`STATS_CHART_COLORS` → `var(--chart-1)` … `var(--chart-6)`).

**Acompanhamento — tour:** KPIs (explorando, concluíram, total), ranking top exploradores (7/30 dias), lista paginada com filtro por status e **progresso % / nível por usuário** (escopado ao RBAC de cada explorador). Ver [portal-tour.md](./portal-tour.md).

**Usuários:** atalho «Abrir acompanhamento» leva à subpágina dedicada do tour.

**Aplicações:** layout em duas colunas — uso ao vivo ocupa a área principal; ranking 30d e lista compacta de apps fantasmas (rolável, expansível) ficam na coluna lateral, sem tags que estouram a tela. Apps **`backend-only`** não aparecem como fantasmas; KPI **Apps rastreáveis** exclui serviços só-backend.

Cada painel pode ter atalho **Gerenciar** que navega para a aba correspondente.

Rastreamento via api-delpi (rotas consumidas pelos dashboards) exige consentimento **`usage_tracking`** e header **`X-Delpi-Caller-App`** nos plugins — ver [rastreamento-uso-apps.md](../04-core-api/rastreamento-uso-apps.md).

---

## 2. Atualização

Botão **Atualizar** recarrega o snapshot. Timestamp exibido em `generatedAt` (horário de Brasília na UI).

---

## 3. Relacionados

- [Controllers e rotas — estatísticas](../04-core-api/controllers-e-rotas.md#7-admin--estatísticas-e-presença)
- [Rastreamento de uso de apps](../04-core-api/rastreamento-uso-apps.md)
- [Presença online e uso de apps (Socket.IO)](../01-arquitetura/event-driven-e-socket.md)
