import type { ReactNode } from "react";

import type { GoalPerformanceBadge } from "../utils/goalDisplay";

type KpiCardProps = {
  title: string;
  value: string;
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeLabel?: string | null;
  goalPerformanceBadge?: GoalPerformanceBadge | null;
  subtitle?: string;
  icon: ReactNode;
  loading?: boolean;
};

export function KpiCard({
  title,
  value,
  contextLabel,
  goalLabel = null,
  goalScopeLabel = null,
  goalPerformanceBadge = null,
  subtitle,
  icon,
  loading = false,
}: KpiCardProps) {
  const resolvedGoal = goalLabel ?? null;
  const resolvedScope = goalScopeLabel?.trim() || null;
  const resolvedContext = subtitle ?? contextLabel ?? "";

  return (
    <article className="ds-card ds-kpi-card">
      <div className="ds-kpi-header">
        <div>
          <p className="ds-kpi-title">{title}</p>
          <h3 className="ds-kpi-value">{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className="ds-kpi-goal">
              <span className="ds-kpi-goal-prefix">Meta</span> {resolvedGoal}
              {resolvedScope ? (
                <span className="ds-kpi-goal-scope"> · {resolvedScope}</span>
              ) : null}
            </p>
          ) : null}
          {goalPerformanceBadge ? (
            <div className="ds-kpi-badges" role="status" aria-label="Desempenho em relação à meta">
              <span
                className={`ds-kpi-badge ds-kpi-badge--${goalPerformanceBadge.tone}`}
              >
                {goalPerformanceBadge.statusLabel}
              </span>
              <span className="ds-kpi-badge ds-kpi-badge--direction">
                {goalPerformanceBadge.directionLabel}
              </span>
            </div>
          ) : null}
          <span className="ds-kpi-context">{resolvedContext}</span>
        </div>
        <div className="ds-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
