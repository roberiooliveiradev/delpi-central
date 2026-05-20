// src/ui/admin/stats/pages/StatsAccessPage.tsx

import { BarChart } from "../StatsCharts";
import {
  StatsInsight,
  StatsInsightRow,
  StatsMiniKpi,
  StatsMiniKpiRow,
  formatPercent,
  statPercent,
} from "../StatsEnrichment";
import { PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

export function StatsAccessPage({ stats, onNavigateTab }: StatsPageProps) {
  const assignmentTotal =
    stats.assignments.userRoles +
    stats.assignments.userGroups +
    stats.assignments.groupRoles +
    stats.assignments.rolePermissions;

  return (
    <div className="admin-stats-page">
      <StatsPageIntro
        title="Acesso RBAC"
        description="Papéis, grupos e vínculos que estruturam permissões na plataforma."
      />

      <StatsMiniKpiRow>
        <StatsMiniKpi label="Papéis" value={stats.roles.total} hint={`${stats.roles.system} sistema`} />
        <StatsMiniKpi label="Grupos" value={stats.groups.total} hint={`${stats.groups.active} ativos`} />
        <StatsMiniKpi
          label="Permissões"
          value={stats.permissions.total}
          hint="Catálogo global"
        />
        <StatsMiniKpi
          tone="primary"
          label="Vínculos"
          value={assignmentTotal}
          hint="Soma de todas as arestas RBAC"
        />
      </StatsMiniKpiRow>

      <StatsInsightRow>
        <StatsInsight
          label="Papéis órfãos"
          value={String(stats.roles.withoutUsers)}
          detail={formatPercent(statPercent(stats.roles.withoutUsers, stats.roles.total))}
        />
        <StatsInsight
          label="Grupos sem usuários"
          value={String(stats.groups.withoutUsers)}
          detail={formatPercent(statPercent(stats.groups.withoutUsers, stats.groups.total))}
        />
        <StatsInsight
          label="Papéis customizados"
          value={String(stats.roles.custom)}
          detail={`${stats.roles.system} de sistema`}
        />
        <StatsInsight
          label="Grupos inativos"
          value={String(stats.groups.inactive)}
          detail={`${stats.groups.active} ativos`}
        />
      </StatsInsightRow>

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
            accent={STATS_CHART_COLORS.c2}
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
          <p className="admin-stats__chart-foot">
            {stats.groups.withoutUsers} grupos sem membros
          </p>
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
            accent={STATS_CHART_COLORS.c3}
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
            accent={STATS_CHART_COLORS.c6}
          />
          <p className="admin-stats__chart-foot">
            Densidade do grafo de acesso — picos em usuário→grupo indicam governança por equipes
          </p>
        </article>
      </div>
    </div>
  );
}
