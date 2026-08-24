// portal/src/ui/usage/UserUsagePanel.tsx

import { Activity } from "lucide-react";
import { Link } from "react-router-dom";

import type { UserUsagePeriodDays, UserUsageStatistics } from "../../data/userUsageTypes";
import { Button, AreaChart } from "../../ui-kit";
import { BarChart } from "../admin/stats/StatsCharts";
import { formatSeriesDateLabel } from "../admin/stats/engagementLabels";
import { formatDuration } from "../admin/stats/engagementFormatting";
import {
  StatsChartCard,
  StatsMiniKpi,
  StatsMiniKpiRow,
} from "../admin/stats/StatsEnrichment";
import { formatGeneratedAt } from "../admin/stats/StatsShared";
import { STATS_CHART_COLORS } from "../admin/stats/statsTheme";
import {
  USER_USAGE_LABELS,
  USER_USAGE_PERIOD_OPTIONS,
} from "./userUsageLabels";

import "../admin/tabs/StatsTab.css";
import "./UserUsagePanel.css";

export type UserUsagePanelVariant = "admin" | "profile";

export type UserUsagePanelProps = {
  data: UserUsageStatistics | null;
  loading: boolean;
  error: string | null;
  periodDays: UserUsagePeriodDays;
  onPeriodChange: (period: UserUsagePeriodDays) => void;
  onRefresh?: () => void;
  variant: UserUsagePanelVariant;
  consentCtaHref?: string;
};

export function UserUsagePanel({
  data,
  loading,
  error,
  periodDays,
  onPeriodChange,
  onRefresh,
  variant,
  consentCtaHref = "/privacy",
}: UserUsagePanelProps) {
  if (loading && !data) {
    return <p className="admin-stats__state">{USER_USAGE_LABELS.loading}</p>;
  }

  if (error && !data) {
    return (
      <div className="admin-stats__state admin-stats__state--error">
        <p>{error}</p>
        {onRefresh ? (
          <Button variant="primary" onClick={onRefresh}>
            {USER_USAGE_LABELS.retry}
          </Button>
        ) : null}
      </div>
    );
  }

  if (!data) {
    return <p className="admin-stats__empty">{USER_USAGE_LABELS.emptyRankings}</p>;
  }

  const { summary, activity, rankings, coverage, consent } = data;

  return (
    <div
      className={[
        "user-usage-panel",
        `user-usage-panel--${variant}`,
      ].join(" ")}
      data-tour={variant === "profile" ? "profile-usage-panel" : undefined}
    >
      <div className="user-usage-panel__toolbar">
        <div className="admin-entity-filters__group admin-stats__period-filter">
          <span className="admin-entity-filters__label">{USER_USAGE_LABELS.periodLabel}</span>
          {USER_USAGE_PERIOD_OPTIONS.map(({ value, label }) => (
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
        <span className="user-usage-panel__updated">
          {USER_USAGE_LABELS.updatedAt} {formatGeneratedAt(data.generatedAt)}
        </span>
      </div>

      {!consent.granted ? (
        <div className="user-usage-panel__consent-notice admin-stats__coverage-notice">
          <p>{USER_USAGE_LABELS.consentDisabled}</p>
          {variant === "profile" ? (
            <Link to={consentCtaHref} className="home-panel-action">
              {USER_USAGE_LABELS.consentCta}
            </Link>
          ) : (
            <p className="user-usage-panel__consent-note">
              {USER_USAGE_LABELS.consentDisabledAdminNote}
            </p>
          )}
        </div>
      ) : null}

      {!coverage.trackingEnabled ? (
        <p className="admin-stats__coverage-notice">{USER_USAGE_LABELS.trackingDisabledServer}</p>
      ) : null}

      <StatsMiniKpiRow>
        <StatsMiniKpi
          tone="primary"
          label={USER_USAGE_LABELS.totalOpens}
          value={summary.totalOpens}
        />
        <StatsMiniKpi label={USER_USAGE_LABELS.appsUsed} value={summary.appsUsed} />
        <StatsMiniKpi
          label={USER_USAGE_LABELS.totalDuration}
          value={formatDuration(summary.totalDurationSeconds)}
        />
        <StatsMiniKpi
          label={USER_USAGE_LABELS.portalDuration}
          value={formatDuration(summary.portalDurationSeconds)}
        />
        <StatsMiniKpi
          label={USER_USAGE_LABELS.avgSession}
          value={formatDuration(summary.avgSessionSeconds)}
        />
        <StatsMiniKpi
          label={USER_USAGE_LABELS.lastUsage}
          value={
            summary.lastAppUsageAt
              ? formatGeneratedAt(summary.lastAppUsageAt)
              : "—"
          }
        />
      </StatsMiniKpiRow>

      <div className="admin-stats__charts-row admin-stats__charts-row--duo admin-stats__charts-row--trends">
        <StatsChartCard title={USER_USAGE_LABELS.opensSeries}>
          {(activity.opensSeries ?? []).length === 0 ? (
            <p className="admin-stats__empty">{USER_USAGE_LABELS.emptyRankings}</p>
          ) : (
            <AreaChart
              data={(activity.opensSeries ?? []).map((point) => ({
                name: formatSeriesDateLabel(point.date),
                value: point.opens ?? 0,
              }))}
              color={STATS_CHART_COLORS.c1}
              valueSuffix={USER_USAGE_LABELS.opensSuffix}
              hintText={USER_USAGE_LABELS.chartHoverHint}
            />
          )}
        </StatsChartCard>
        <StatsChartCard title={USER_USAGE_LABELS.durationSeries}>
          {(activity.durationSeries ?? []).length === 0 ? (
            <p className="admin-stats__empty">{USER_USAGE_LABELS.emptyRankings}</p>
          ) : (
            <AreaChart
              data={(activity.durationSeries ?? []).map((point) => ({
                name: formatSeriesDateLabel(point.date),
                value: point.totalSeconds ?? 0,
              }))}
              color={STATS_CHART_COLORS.c3}
              valueFormatter={formatDuration}
              hintText={USER_USAGE_LABELS.chartHoverHint}
            />
          )}
        </StatsChartCard>
      </div>

      <div className="admin-stats__charts-row admin-stats__charts-row--duo">
        <StatsChartCard title={USER_USAGE_LABELS.topAppsOpens}>
          {(rankings.topAppsByOpens ?? []).length === 0 ? (
            <p className="admin-stats__empty">{USER_USAGE_LABELS.emptyRankings}</p>
          ) : (
            <BarChart
              items={(rankings.topAppsByOpens ?? []).map((item) => ({
                id: item.id,
                label: item.name,
                value: item.count,
              }))}
              valueLabel={USER_USAGE_LABELS.opensSuffix}
              accent={`linear-gradient(90deg, ${STATS_CHART_COLORS.c2}, ${STATS_CHART_COLORS.c1})`}
            />
          )}
        </StatsChartCard>
        <StatsChartCard title={USER_USAGE_LABELS.topAppsDuration}>
          {(rankings.topAppsByDuration ?? []).length === 0 ? (
            <p className="admin-stats__empty">{USER_USAGE_LABELS.emptyRankings}</p>
          ) : (
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
          )}
        </StatsChartCard>
      </div>

      <div className="admin-stats__charts-row">
        <StatsChartCard title={USER_USAGE_LABELS.topRoutes}>
          {(rankings.topRoutes ?? []).length === 0 ? (
            <p className="admin-stats__empty">{USER_USAGE_LABELS.emptyRoutes}</p>
          ) : (
            <BarChart
              items={(rankings.topRoutes ?? []).map((item) => ({
                id: item.id,
                label: item.name,
                value: item.count,
              }))}
              valueLabel={USER_USAGE_LABELS.opensSuffix}
              maxItems={8}
            />
          )}
        </StatsChartCard>
      </div>

      <section className="admin-stats__panel admin-stats__panel--wide">
        <div className="admin-stats-panel__title-row">
          <h5>
            <Activity size={14} aria-hidden="true" />
            {USER_USAGE_LABELS.coverage}
          </h5>
        </div>
        <p className="admin-stats-panel__lede">
          {coverage.sessionsRecorded.toLocaleString("pt-BR")} sessões registradas ·{" "}
          {coverage.eventsInPeriod.toLocaleString("pt-BR")} aberturas no período
        </p>
      </section>
    </div>
  );
}
