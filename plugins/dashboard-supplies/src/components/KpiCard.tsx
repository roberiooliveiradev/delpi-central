import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  contextLabel?: string;
  goalLabel?: string | null;
  goalScopeLabel?: string | null;
  goalStatusLabel?: string | null;
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
  goalStatusLabel = null,
  subtitle,
  icon,
  loading = false,
}: KpiCardProps) {
  const resolvedGoal = goalLabel ?? null;
  const resolvedScope = goalScopeLabel?.trim() || null;
  const resolvedStatus = goalStatusLabel?.trim() || null;
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
          {resolvedStatus ? (
            <p className="ds-kpi-goal-status" role="status">
              {resolvedStatus}
            </p>
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
