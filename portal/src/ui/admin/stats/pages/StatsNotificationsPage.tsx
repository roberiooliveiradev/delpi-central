// src/ui/admin/stats/pages/StatsNotificationsPage.tsx

import { BarChart, DonutChart } from "../StatsCharts";
import { PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { STATS_CHART_COLORS } from "../statsTheme";

import type { StatsChartsData } from "../useAdminStats";

type StatsNotificationsPageProps = StatsPageProps & {
  charts: StatsChartsData;
};

export function StatsNotificationsPage({
  stats,
  charts,
  onNavigateTab,
}: StatsNotificationsPageProps) {
  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Notificações"
          description="Volume e status dos envios de campanhas agendadas pelo Admin."
        />
        <PanelNav tab="notifications" label="Gerenciar" onNavigateTab={onNavigateTab} />
      </div>

      <div className="admin-stats__panel">
        <div className="admin-stats__split">
          <DonutChart
            segments={charts.notificationSegments}
            centerValue={String(stats.notifications?.dispatchesTotal ?? 0)}
            centerLabel="Envios"
            size={140}
          />
          <BarChart
            items={[
              {
                id: "total",
                label: "Total registrados",
                value: stats.notifications?.dispatchesTotal ?? 0,
              },
              {
                id: "pending",
                label: "Pendentes / agendados",
                value: stats.notifications?.dispatchesPending ?? 0,
              },
              {
                id: "done",
                label: "Concluídos",
                value: stats.notifications?.dispatchesCompleted ?? 0,
              },
              {
                id: "fail",
                label: "Com falha",
                value: stats.notifications?.dispatchesFailed ?? 0,
              },
            ]}
            accent={STATS_CHART_COLORS.primary}
          />
        </div>
      </div>
    </div>
  );
}
