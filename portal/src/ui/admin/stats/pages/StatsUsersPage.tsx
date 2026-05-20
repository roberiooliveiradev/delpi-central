// src/ui/admin/stats/pages/StatsUsersPage.tsx

import { BarChart, DonutChart } from "../StatsCharts";
import { PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

import type { StatsChartsData } from "../useAdminStats";

type StatsUsersPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

export function StatsUsersPage({ stats, charts, onNavigateTab }: StatsUsersPageProps) {
  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Usuários"
          description="Presença no portal, status da base e histórico de login."
        />
        <PanelNav tab="users" label="Gerenciar usuários" onNavigateTab={onNavigateTab} />
      </div>

      <div className="admin-stats__panel">
        <div className="admin-stats__split">
          <DonutChart
            segments={charts.userSegments}
            centerValue={String(stats.users.online)}
            centerLabel="Online agora"
            size={128}
          />
          <BarChart
            items={[
              { id: "active", label: "Ativos", value: stats.users.active },
              { id: "inactive", label: "Inativos", value: stats.users.inactive },
              {
                id: "login7",
                label: "Login últimos 7 dias",
                value: stats.users.loggedInLast7Days,
              },
              {
                id: "login30",
                label: "Login últimos 30 dias",
                value: stats.users.loggedInLast30Days,
              },
              {
                id: "super",
                label: "Superadmins",
                value: stats.users.superadmins,
              },
              {
                id: "birth",
                label: "Com data de nascimento",
                value: stats.users.withBirthDate,
              },
              {
                id: "norole",
                label: "Sem papel direto",
                value: stats.users.withoutDirectRoles,
              },
              {
                id: "nogroup",
                label: "Sem grupo",
                value: stats.users.withoutGroups,
              },
            ]}
            accent={STATS_CHART_COLORS.primary}
          />
        </div>
      </div>
    </div>
  );
}
