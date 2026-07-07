import type { ReactNode } from "react";

import type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";
import { HelpTooltip } from "@delpi/plugin-ui";

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
      ? "dh-kpi-value dh-kpi-value--per-unit"
      : "dh-kpi-value";
  const goalClassName =
    goalVariant === "per-unit"
      ? "dh-kpi-goal dh-kpi-goal--per-unit"
      : "dh-kpi-goal";

  return (
    <article className="dh-card dh-kpi-card">
      <div className="dh-kpi-header">
        <div>
          <p className="dh-kpi-title">
            {title}
            {titleHint ? (
              <HelpTooltip
                content={titleHint}
                ariaLabel={`Ajuda: ${title}`}
                className="dh-kpi-title__help"
              />
            ) : null}
          </p>
          <h3 className={valueClassName}>{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className={goalClassName}>
              <span className="dh-kpi-goal-prefix">Meta</span> {resolvedGoal}
            </p>
          ) : null}
          {resolvedIddScore ? (
            <p className={`${goalClassName} dh-kpi-goal--idd`}>
              <span className="dh-kpi-goal-prefix">Nota IDD</span> {resolvedIddScore}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dh-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {resolvedScopeBadge ? (
                <span className="dh-kpi-badge dh-kpi-badge--scope">{resolvedScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dh-kpi-badge dh-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {performanceBadges.map((badge, index) => (
                <span key={`${badge.statusLabel}-${index}`} className="dh-kpi-badge-group">
                  <span
                    className={`dh-kpi-badge dh-kpi-badge--${badge.tone}`}
                  >
                    {badge.statusLabel}
                  </span>
                  <span className="dh-kpi-badge dh-kpi-badge--direction">
                    {badge.directionLabel}
                  </span>
                </span>
              ))}
            </div>
          ) : null}
          <span className="dh-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dh-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
      {footer}
    </article>
  );
}
