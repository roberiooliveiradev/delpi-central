import type { ReactNode } from "react";

import type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";

type SummaryMetric = {
  label: string;
  value: string;
};

type SummaryCardProps = {
  title: string;
  description: string;
  goalLabel?: string | null;
  goalScopeBadge?: GoalScopeBadge | null;
  goalScopeHint?: string | null;
  goalPerformanceBadge?: GoalPerformanceBadge | null;
  iddScoreLabel?: string | null;
  icon: ReactNode;
  metrics: SummaryMetric[];
  loading?: boolean;
};

export function SummaryCard({
  title,
  description,
  goalLabel = null,
  goalScopeBadge = null,
  goalScopeHint = null,
  goalPerformanceBadge = null,
  iddScoreLabel = null,
  icon,
  metrics,
  loading = false,
}: SummaryCardProps) {
  const resolvedScopeHint = goalScopeHint?.trim() || null;
  const hasBadges = Boolean(goalScopeBadge || resolvedScopeHint || goalPerformanceBadge);

  return (
    <article className="dq-card dq-summary-card">
      <div className="dq-summary-card__header">
        <div className="dq-summary-card__icon" aria-hidden="true">
          {icon}
        </div>
        <div>
          <h2 className="dq-summary-card__title">{title}</h2>
          <p className="dq-summary-card__description">{description}</p>
          {goalLabel ? (
            <p className="dq-kpi-goal">
              <span className="dq-kpi-goal-prefix">Meta</span> {goalLabel}
            </p>
          ) : null}
          {iddScoreLabel ? (
            <p className="dq-kpi-goal dq-kpi-goal--idd">
              <span className="dq-kpi-goal-prefix">Nota IDD</span> {iddScoreLabel}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dq-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {goalScopeBadge ? (
                <span className="dq-kpi-badge dq-kpi-badge--scope">{goalScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dq-kpi-badge dq-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {goalPerformanceBadge ? (
                <>
                  <span className={`dq-kpi-badge dq-kpi-badge--${goalPerformanceBadge.tone}`}>
                    {goalPerformanceBadge.statusLabel}
                  </span>
                  <span className="dq-kpi-badge dq-kpi-badge--direction">
                    {goalPerformanceBadge.directionLabel}
                  </span>
                </>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <dl className="dq-summary-metrics">
        {metrics.map((metric) => (
          <div key={metric.label} className="dq-summary-metric">
            <dt>{metric.label}</dt>
            <dd>{loading ? "…" : metric.value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
