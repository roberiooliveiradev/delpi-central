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
      ? "dl-kpi-value dl-kpi-value--per-unit"
      : "dl-kpi-value";
  const goalClassName =
    goalVariant === "per-unit"
      ? "dl-kpi-goal dl-kpi-goal--per-unit"
      : "dl-kpi-goal";

  return (
    <article className="dl-card dl-kpi-card">
      <div className="dl-kpi-header">
        <div>
          <p className="dl-kpi-title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="dl-kpi-title__help"
              />
            ) : null}
          </p>
          <h3 className={valueClassName}>{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className={goalClassName}>
              <span className="dl-kpi-goal-prefix">Meta</span> {resolvedGoal}
            </p>
          ) : null}
          {resolvedIddScore ? (
            <p className={`${goalClassName} dl-kpi-goal--idd`}>
              <span className="dl-kpi-goal-prefix">Nota IDD</span> {resolvedIddScore}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dl-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {resolvedScopeBadge ? (
                <span className="dl-kpi-badge dl-kpi-badge--scope">{resolvedScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dl-kpi-badge dl-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {performanceBadges.map((badge, index) => (
                <span key={`${badge.statusLabel}-${index}`} className="dl-kpi-badge-group">
                  <span
                    className={`dl-kpi-badge dl-kpi-badge--${badge.tone}`}
                  >
                    {badge.statusLabel}
                  </span>
                  <span className="dl-kpi-badge dl-kpi-badge--direction">
                    {badge.directionLabel}
                  </span>
                </span>
              ))}
            </div>
          ) : null}
          <span className="dl-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dl-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
      {footer}
    </article>
  );
}
