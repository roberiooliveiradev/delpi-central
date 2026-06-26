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
  footer?: ReactNode;
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
  footer,
}: KpiCardProps) {
  const resolvedGoal = goalLabel ?? null;
  const resolvedContext = subtitle ?? contextLabel ?? "";
  const resolvedScopeHint = goalScopeHint?.trim() || null;
  const hasBadges = Boolean(goalScopeBadge || resolvedScopeHint || goalPerformanceBadge);

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
          <h3 className="dq-kpi-value">{loading ? "…" : value}</h3>
          {resolvedGoal ? (
            <p className="dq-kpi-goal">
              <span className="dq-kpi-goal-prefix">Meta</span> {resolvedGoal}
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
                  <span
                    className={`dq-kpi-badge dq-kpi-badge--${goalPerformanceBadge.tone}`}
                  >
                    {goalPerformanceBadge.statusLabel}
                  </span>
                  <span className="dq-kpi-badge dq-kpi-badge--direction">
                    {goalPerformanceBadge.directionLabel}
                  </span>
                </>
              ) : null}
            </div>
          ) : null}
          <span className="dq-kpi-context">{resolvedContext}</span>
        </div>
        <div className="dq-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
      {footer ? <div className="dq-kpi-footer">{footer}</div> : null}
    </article>
  );
}
