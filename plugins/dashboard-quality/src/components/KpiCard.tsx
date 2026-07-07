import type { ReactNode } from "react";

import type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";
import { HelpTooltip } from "./HelpTooltip";

type KpiCardProps = {
  title: string;
  titleHint?: string;
  value: string;
  valueVariant?: "default" | "per-unit";
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeBadge?: GoalScopeBadge | null;
  goalScopeHint?: string | null;
  goalPerformanceBadge?: GoalPerformanceBadge | null;
  goalPerformanceBadges?: GoalPerformanceBadge[];
  iddScoreLabel?: string | null;
  goalVariant?: "default" | "per-unit";
  subtitle?: string;
  icon: ReactNode;
  footer?: ReactNode;
  loading?: boolean;
};

export function KpiCard({
  title,
  titleHint,
  value,
  valueVariant = "default",
  contextLabel,
  goalLabel = null,
  goalScopeBadge = null,
  goalScopeHint = null,
  goalPerformanceBadge = null,
  goalPerformanceBadges = [],
  iddScoreLabel = null,
  goalVariant = "default",
  subtitle,
  icon,
  footer = null,
  loading = false,
}: KpiCardProps) {
  const showMeta = !loading;
  const resolvedGoal = showMeta ? goalLabel ?? null : null;
  const resolvedContext = subtitle ?? contextLabel ?? "";
  const resolvedScopeHint = showMeta ? goalScopeHint?.trim() || null : null;
  const resolvedScopeBadge = showMeta ? goalScopeBadge : null;
  const resolvedIddScore = showMeta ? iddScoreLabel ?? null : null;
  const performanceBadges = showMeta
    ? goalPerformanceBadges.length > 0
      ? goalPerformanceBadges
      : goalPerformanceBadge
        ? [goalPerformanceBadge]
        : []
    : [];
  const hasBadges = Boolean(
    resolvedScopeBadge || resolvedScopeHint || performanceBadges.length > 0,
  );
  const valueClassName =
    valueVariant === "per-unit"
      ? "dq-kpi-value dq-kpi-value--per-unit"
      : "dq-kpi-value";
  const goalClassName =
    goalVariant === "per-unit"
      ? "dq-kpi-goal dq-kpi-goal--per-unit"
      : "dq-kpi-goal";

  return (
    <article className="dq-card dq-kpi-card">
      <div className="dq-kpi-header">
        <div>
          <p className="dq-kpi-title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="dq-kpi-title__help"
              />
            ) : null}
          </p>
          <h3 className={valueClassName}>{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className={goalClassName}>
              <span className="dq-kpi-goal-prefix">Meta</span> {resolvedGoal}
            </p>
          ) : null}
          {resolvedIddScore ? (
            <p className={`${goalClassName} dq-kpi-goal--idd`}>
              <span className="dq-kpi-goal-prefix">Nota IDD</span> {resolvedIddScore}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dq-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {resolvedScopeBadge ? (
                <span className="dq-kpi-badge dq-kpi-badge--scope">{resolvedScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dq-kpi-badge dq-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {performanceBadges.map((badge, index) => (
                <span key={`${badge.statusLabel}-${index}`} className="dq-kpi-badge-group">
                  <span
                    className={`dq-kpi-badge dq-kpi-badge--${badge.tone}`}
                  >
                    {badge.statusLabel}
                  </span>
                  <span className="dq-kpi-badge dq-kpi-badge--direction">
                    {badge.directionLabel}
                  </span>
                </span>
              ))}
            </div>
          ) : null}
          <span className="dq-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dq-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
      {footer}
    </article>
  );
}
