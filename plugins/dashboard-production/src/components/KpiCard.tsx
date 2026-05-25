import type { ReactNode } from "react";

import type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";

type KpiCardProps = {
  title: string;
  value: string;
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeBadge?: GoalScopeBadge | null;
  goalScopeHint?: string | null;
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
  goalScopeBadge = null,
  goalScopeHint = null,
  goalPerformanceBadge = null,
  subtitle,
  icon,
  loading = false,
}: KpiCardProps) {
  const resolvedGoal = goalLabel ?? null;
  const resolvedContext = subtitle ?? contextLabel ?? "";
  const resolvedScopeHint = goalScopeHint?.trim() || null;
  const hasBadges = Boolean(goalScopeBadge || resolvedScopeHint || goalPerformanceBadge);

  return (
    <article className="dp-card dp-kpi-card">
      <div className="dp-kpi-header">
        <div>
          <p className="dp-kpi-title">{title}</p>
          <h3 className="dp-kpi-value">{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className="dp-kpi-goal">
              <span className="dp-kpi-goal-prefix">Meta</span> {resolvedGoal}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dp-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {goalScopeBadge ? (
                <span className="dp-kpi-badge dp-kpi-badge--scope">{goalScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dp-kpi-badge dp-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {goalPerformanceBadge ? (
                <>
                  <span
                    className={`dp-kpi-badge dp-kpi-badge--${goalPerformanceBadge.tone}`}
                  >
                    {goalPerformanceBadge.statusLabel}
                  </span>
                  <span className="dp-kpi-badge dp-kpi-badge--direction">
                    {goalPerformanceBadge.directionLabel}
                  </span>
                </>
              ) : null}
            </div>
          ) : null}
          <span className="dp-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dp-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
