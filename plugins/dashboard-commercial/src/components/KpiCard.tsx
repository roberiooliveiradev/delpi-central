import type { ReactNode } from "react";

import type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";

type KpiCardProps = {
  title: string;
  value: string;
  valueVariant?: "default" | "per-unit";
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeBadge?: GoalScopeBadge | null;
  goalScopeHint?: string | null;
  goalPerformanceBadge?: GoalPerformanceBadge | null;
  goalPerformanceBadges?: GoalPerformanceBadge[];
  goalVariant?: "default" | "per-unit";
  subtitle?: string;
  icon: ReactNode;
  loading?: boolean;
};

export function KpiCard({
  title,
  value,
  valueVariant = "default",
  contextLabel,
  goalLabel = null,
  goalScopeBadge = null,
  goalScopeHint = null,
  goalPerformanceBadge = null,
  goalPerformanceBadges = [],
  goalVariant = "default",
  subtitle,
  icon,
  loading = false,
}: KpiCardProps) {
  const resolvedGoal = goalLabel ?? null;
  const resolvedContext = subtitle ?? contextLabel ?? "";
  const resolvedScopeHint = goalScopeHint?.trim() || null;
  const performanceBadges =
    goalPerformanceBadges.length > 0
      ? goalPerformanceBadges
      : goalPerformanceBadge
        ? [goalPerformanceBadge]
        : [];
  const hasBadges = Boolean(
    goalScopeBadge || resolvedScopeHint || performanceBadges.length > 0,
  );
  const valueClassName =
    valueVariant === "per-unit"
      ? "dc-kpi-value dc-kpi-value--per-unit"
      : "dc-kpi-value";
  const goalClassName =
    goalVariant === "per-unit"
      ? "dc-kpi-goal dc-kpi-goal--per-unit"
      : "dc-kpi-goal";

  return (
    <article className="dc-card dc-kpi-card">
      <div className="dc-kpi-header">
        <div>
          <p className="dc-kpi-title">{title}</p>
          <h3 className={valueClassName}>{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className={goalClassName}>
              <span className="dc-kpi-goal-prefix">Meta</span> {resolvedGoal}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dc-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {goalScopeBadge ? (
                <span className="dc-kpi-badge dc-kpi-badge--scope">{goalScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dc-kpi-badge dc-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {performanceBadges.map((badge, index) => (
                <span key={`${badge.statusLabel}-${index}`} className="dc-kpi-badge-group">
                  <span
                    className={`dc-kpi-badge dc-kpi-badge--${badge.tone}`}
                  >
                    {badge.statusLabel}
                  </span>
                  <span className="dc-kpi-badge dc-kpi-badge--direction">
                    {badge.directionLabel}
                  </span>
                </span>
              ))}
            </div>
          ) : null}
          <span className="dc-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dc-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
