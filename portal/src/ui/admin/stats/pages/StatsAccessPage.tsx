// src/ui/admin/stats/pages/StatsAccessPage.tsx

import { BarChart } from "../StatsCharts";
import { PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

export function StatsAccessPage({ stats, onNavigateTab }: StatsPageProps) {
  return (
    <div className="admin-stats-page">
      <StatsPageIntro
        title="Acesso RBAC"
        description="Papéis, grupos e vínculos que estruturam permissões na plataforma."
      />

      <div className="admin-stats__grid admin-stats__grid--access">
        <article className="admin-stats__panel">
          <div className="admin-stats-page__head-row">
            <h5>Papéis mais atribuídos</h5>
            <PanelNav tab="roles" label="Papéis" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={stats.roles.topByUsers.map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="usuários"
            accent={STATS_CHART_COLORS.secondary}
          />
          <p className="admin-stats__chart-foot">
            {stats.roles.withoutUsers} papéis sem usuários · {stats.roles.system} de sistema
          </p>
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats-page__head-row">
            <h5>Grupos com mais usuários</h5>
            <PanelNav tab="groups" label="Grupos" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={stats.groups.topByUsers.map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="usuários"
            accent={STATS_CHART_COLORS.primary}
          />
        </article>

        <article className="admin-stats__panel">
          <div className="admin-stats-page__head-row">
            <h5>Grupos com mais papéis</h5>
            <PanelNav tab="groups" label="Grupos" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={stats.groups.topByRoles.map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="papéis"
            accent={STATS_CHART_COLORS.primaryLight}
          />
        </article>

        <article className="admin-stats__panel admin-stats__panel--wide">
          <div className="admin-stats-page__head-row">
            <h5>Vínculos na base</h5>
            <PanelNav tab="permissions" label="Permissões" onNavigateTab={onNavigateTab} />
          </div>
          <BarChart
            items={[
              {
                id: "ur",
                label: "Usuário → papel",
                value: stats.assignments.userRoles,
              },
              {
                id: "ug",
                label: "Usuário → grupo",
                value: stats.assignments.userGroups,
              },
              {
                id: "gr",
                label: "Grupo → papel",
                value: stats.assignments.groupRoles,
              },
              {
                id: "rp",
                label: "Papel → permissão",
                value: stats.assignments.rolePermissions,
              },
            ]}
            accent={STATS_CHART_COLORS.secondaryMuted}
          />
          <p className="admin-stats__chart-foot">
            {stats.permissions.total} permissões cadastradas no catálogo
          </p>
        </article>
      </div>
    </div>
  );
}
