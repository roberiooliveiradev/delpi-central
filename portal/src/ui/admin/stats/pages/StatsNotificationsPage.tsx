// src/ui/admin/stats/pages/StatsNotificationsPage.tsx

import { BarChart, DonutChart } from "../StatsCharts";
import {
  StatsChartCard,
  StatsInsight,
  StatsInsightRow,
  StatsMiniKpi,
  StatsMiniKpiRow,
  formatPercent,
  statPercent,
} from "../StatsEnrichment";
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
  const n = stats.notifications;
  const total = n?.dispatchesTotal ?? 0;
  const pending = n?.dispatchesPending ?? 0;
  const completed = n?.dispatchesCompleted ?? 0;
  const failed = n?.dispatchesFailed ?? 0;
  const successPct = statPercent(completed, total);
  const failPct = statPercent(failed, total);

  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Notificações"
          description="Volume e status dos envios de campanhas agendadas pelo Admin."
        />
        <PanelNav tab="notifications" label="Gerenciar" onNavigateTab={onNavigateTab} />
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi label="Total de envios" value={total} hint="Histórico registrado" />
        <StatsMiniKpi
          tone="primary"
          label="Pendentes"
          value={pending}
          hint={formatPercent(statPercent(pending, total))}
        />
        <StatsMiniKpi
          tone="success"
          label="Concluídos"
          value={completed}
          hint={formatPercent(successPct)}
        />
        <StatsMiniKpi
          tone="danger"
          label="Com falha"
          value={failed}
          hint={formatPercent(failPct)}
        />
      </StatsMiniKpiRow>

      <StatsInsightRow>
        <StatsInsight
          label="Taxa de sucesso"
          value={formatPercent(successPct)}
          detail={total > 0 ? `${completed} envios ok` : "Sem envios"}
        />
        <StatsInsight
          label="Em fila"
          value={String(pending)}
          detail="Aguardando processamento"
        />
        <StatsInsight
          label="Falhas"
          value={String(failed)}
          detail={failed > 0 ? "Revisar logs de campanha" : "Nenhuma falha"}
        />
        <StatsInsight
          label="Outros status"
          value={String(Math.max(0, total - pending - completed - failed))}
          detail="Cancelados ou estados intermediários"
        />
      </StatsInsightRow>

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <StatsChartCard
          title="Distribuição"
          foot={
            total > 0
              ? `${formatPercent(successPct)} concluídos · ${formatPercent(failPct)} falhas`
              : "Nenhum envio para analisar"
          }
        >
          <DonutChart
            segments={charts.notificationSegments}
            centerValue={String(total)}
            centerLabel="Envios"
            size={140}
          />
        </StatsChartCard>
        <StatsChartCard title="Detalhamento">
          <BarChart
            items={[
              { id: "total", label: "Total registrados", value: total },
              { id: "pending", label: "Pendentes / agendados", value: pending },
              { id: "done", label: "Concluídos", value: completed },
              { id: "fail", label: "Com falha", value: failed },
            ]}
            accent={STATS_CHART_COLORS.primary}
          />
        </StatsChartCard>
      </div>
    </div>
  );
}
