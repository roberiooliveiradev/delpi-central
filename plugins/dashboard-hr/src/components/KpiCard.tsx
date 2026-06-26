import type { ReactNode } from "react";

import type { GoalPerformanceBadge, GoalScopeBadge } from "../utils/goalDisplay";
import { HelpTooltip } from "./HelpTooltip";

type KpiCardProps = {
  title: string;
  titleHint?: string;
  value: string;
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeBadge?: GoalScopeBadge | null;
  goalScopeHint?: string | null;
  goalPerformanceBadge?: GoalPerformanceBadge | null;
  iddScoreLabel?: string | null;
  subtitle?: string;
  icon: ReactNode;
  loading?: boolean;
};

export function KpiCard({
  title,
  titleHint,
  value,
  contextLabel,
  goalLabel = null,
  goalScopeBadge = null,
  goalScopeHint = null,
  goalPerformanceBadge = null,
  iddScoreLabel = null,
  subtitle,
  icon,
  loading = false,
}: KpiCardProps) {
  const resolvedGoal = goalLabel ?? null;
  const resolvedContext = subtitle ?? contextLabel ?? "";
  const resolvedScopeHint = goalScopeHint?.trim() || null;
  const hasBadges = Boolean(goalScopeBadge || resolvedScopeHint || goalPerformanceBadge);

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
          <h3 className="dh-kpi-value">{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className="dh-kpi-goal">
              <span className="dh-kpi-goal-prefix">Meta</span> {resolvedGoal}
            </p>
          ) : null}
          {iddScoreLabel ? (
            <p className="dh-kpi-goal dh-kpi-goal--idd">
              <span className="dh-kpi-goal-prefix">Nota IDD</span> {iddScoreLabel}
            </p>
          ) : null}
          {hasBadges ? (
            <div
              className="dh-kpi-badges"
              role="status"
              aria-label="Escopo e desempenho em relação à meta"
            >
              {goalScopeBadge ? (
                <span className="dh-kpi-badge dh-kpi-badge--scope">{goalScopeBadge.label}</span>
              ) : null}
              {resolvedScopeHint ? (
                <span className="dh-kpi-badge dh-kpi-badge--info">{resolvedScopeHint}</span>
              ) : null}
              {goalPerformanceBadge ? (
                <>
                  <span
                    className={`dh-kpi-badge dh-kpi-badge--${goalPerformanceBadge.tone}`}
                  >
                    {goalPerformanceBadge.statusLabel}
                  </span>
                  <span className="dh-kpi-badge dh-kpi-badge--direction">
                    {goalPerformanceBadge.directionLabel}
                  </span>
                </>
              ) : null}
            </div>
          ) : null}
          <span className="dh-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dh-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
