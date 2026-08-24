// src/ui/admin/stats/pages/StatsUsagePage.tsx

import { Activity } from "lucide-react";

import type { AdminEngagementStatistics } from "../../../../data/adminApi";
import { Button, AreaChart } from "../../../../ui-kit";
import { BarChart } from "../StatsCharts";
import {
  StatsChartCard,
  StatsMiniKpi,
  StatsMiniKpiRow,
  formatPercent,
} from "../StatsEnrichment";
import { PanelNav, StatsPageIntro, type StatsPageProps } from "../StatsShared";
import { formatDuration } from "../engagementFormatting";
import {
  ENGAGEMENT_LABELS,
  ENGAGEMENT_PERIOD_OPTIONS,
  formatEngagementUserRow,
  formatSeriesDateLabel,
} from "../engagementLabels";
import { STATS_CHART_COLORS } from "../statsTheme";
import type { EngagementPeriodDays } from "../useAdminEngagementStats";

type StatsUsagePageProps = StatsPageProps & {
  engagement: AdminEngagementStatistics | null;
  loading: boolean;
  error: string | null;
  periodDays: EngagementPeriodDays;
  onPeriodChange: (period: EngagementPeriodDays) => void;
  onRefresh: () => void;
};

export function StatsUsagePage({
  engagement,
  loading,
  error,
  periodDays,
  onPeriodChange,
  onRefresh,
  onNavigateTab,
}: StatsUsagePageProps) {
  if (loading && !engagement) {
    return <p className="admin-stats__state">Carregando engajamento…</p>;
  }

  if (error && !engagement) {
    return (
      <div className="admin-stats__state admin-stats__state--error">
        <p>{error}</p>
        <Button variant="primary" onClick={onRefresh}>
          Tentar novamente
        </Button>
      </div>
    );
  }

  if (!engagement) {
    return <p className="admin-stats__empty">{ENGAGEMENT_LABELS.emptyRankings}</p>;
  }

  const { activity, duration, rankings, coverage } = engagement;

  return (
    <div className="admin-stats-page">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title={ENGAGEMENT_LABELS.pageTitle}
          description={ENGAGEMENT_LABELS.pageDescription}
        />
        <PanelNav tab="users" label="Gerenciar usuários" onNavigateTab={onNavigateTab} />
      </div>

      <div className="admin-entity-filters__group admin-stats__period-filter">
        <span className="admin-entity-filters__label">Período:</span>
        {ENGAGEMENT_PERIOD_OPTIONS.map(({ value, label }) => (
          <Button
            key={value}
            size="sm"
            pressed={periodDays === value}
            onClick={() => onPeriodChange(value)}
          >
            {label}
          </Button>
        ))}
      </div>

      {!coverage.trackingEnabled ? (
        <p className="admin-stats__coverage-notice">{ENGAGEMENT_LABELS.trackingDisabled}</p>
      ) : null}

      <div className="admin-stats__charts-row admin-stats__charts-row--duo admin-stats__charts-row--trends">
        <StatsChartCard title={ENGAGEMENT_LABELS.activeUsersSeries}>
          <AreaChart
            data={(activity.activeUsersSeries ?? []).map((point) => ({
              name: formatSeriesDateLabel(point.date),
              value: point.activeUsers ?? 0,
            }))}
            color={STATS_CHART_COLORS.c1}
            valueSuffix="usuários"
            hintText={ENGAGEMENT_LABELS.chartHoverHint}
          />
        </StatsChartCard>
        <StatsChartCard title={ENGAGEMENT_LABELS.durationSeries}>
          <AreaChart
            data={(activity.durationSeries ?? []).map((point) => ({
              name: formatSeriesDateLabel(point.date),
              value: point.totalSeconds ?? 0,
            }))}
            color={STATS_CHART_COLORS.c3}
            valueFormatter={formatDuration}
            hintText={ENGAGEMENT_LABELS.chartHoverHint}
          />
        </StatsChartCard>
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi tone="primary" label={ENGAGEMENT_LABELS.dau} value={activity.dau} />
        <StatsMiniKpi label={ENGAGEMENT_LABELS.wau} value={activity.wau} />
        <StatsMiniKpi label={ENGAGEMENT_LABELS.mau} value={activity.mau} />
        <StatsMiniKpi
          label={ENGAGEMENT_LABELS.stickiness}
          value={`${activity.stickiness}%`}
          hint="DAU / MAU"
        />
        <StatsMiniKpi
          label={ENGAGEMENT_LABELS.avgPortalTime}
          value={formatDuration(duration.avgPortalSeconds)}
          hint={`Mediana ${formatDuration(duration.medianPortalSeconds)}`}
        />
        <StatsMiniKpi
          label={ENGAGEMENT_LABELS.avgAppTime}
          value={formatDuration(duration.avgAppSeconds)}
          hint={`P90 ${formatDuration(duration.p90AppSeconds)}`}
        />
      </StatsMiniKpiRow>

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <StatsChartCard title={ENGAGEMENT_LABELS.topAppsOpens}>
          <BarChart
            items={(rankings.topAppsByOpens ?? []).map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="aberturas"
            accent={`linear-gradient(90deg, ${STATS_CHART_COLORS.c2}, ${STATS_CHART_COLORS.c1})`}
          />
        </StatsChartCard>
        <StatsChartCard title={ENGAGEMENT_LABELS.topAppsDuration}>
          <BarChart
            items={(rankings.topAppsByDuration ?? []).map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
              sublabel: formatDuration(item.count),
            }))}
            valueLabel=""
            accent={`linear-gradient(90deg, ${STATS_CHART_COLORS.c4}, ${STATS_CHART_COLORS.c3})`}
          />
        </StatsChartCard>
      </div>

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <StatsChartCard title={ENGAGEMENT_LABELS.topUsers}>
          {(rankings.topUsers ?? []).length === 0 ? (
            <p className="admin-stats__empty">{ENGAGEMENT_LABELS.emptyRankings}</p>
          ) : (
            <ul className="admin-stats-top-users-list">
              {(rankings.topUsers ?? []).map((user, index) => {
                const row = formatEngagementUserRow(user);
                return (
                  <li key={user.id} className="admin-stats-top-users-item">
                    <span className="admin-stats-top-users-item__rank">{index + 1}</span>
                    <div>
                      <strong>{row.primary}</strong>
                      <span className="admin-stats-top-users-item__email">{row.secondary}</span>
                      <span className="admin-stats-top-users-item__metrics">
                        {row.metrics.join(" · ")}
                      </span>
                      <span className="admin-stats-top-users-item__last">
                        Último uso: {row.lastUsage}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </StatsChartCard>
        <StatsChartCard title={ENGAGEMENT_LABELS.topRoutes}>
          <BarChart
            items={(rankings.topRoutes ?? []).map((item) => ({
              id: item.id,
              label: item.name,
              value: item.count,
            }))}
            valueLabel="aberturas"
            maxItems={8}
          />
        </StatsChartCard>
      </div>

      <section className="admin-stats__panel admin-stats__panel--wide">
        <div className="admin-stats-panel__title-row">
          <h5>
            <Activity size={14} aria-hidden="true" />
            {ENGAGEMENT_LABELS.coverage}
          </h5>
        </div>
        <p className="admin-stats-panel__lede">
          {formatPercent(coverage.consentRate)} dos usuários ativos ({coverage.consentedUsers} de{" "}
          {coverage.activeUsers}) com consentimento · {coverage.sessionsRecorded} sessões
          registradas · {coverage.eventsInPeriod.toLocaleString("pt-BR")} aberturas no período
        </p>
      </section>
    </div>
  );
}
