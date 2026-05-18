import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  subtitle: string;
  icon: ReactNode;
  loading?: boolean;
  footer?: ReactNode;
};

export function KpiCard({
  title,
  value,
  subtitle,
  icon,
  loading = false,
  footer,
}: KpiCardProps) {
  return (
    <article className="dq-card dq-kpi-card">
      <div className="dq-kpi-header">
        <div>
          <p className="dq-kpi-title">{title}</p>
          <h3 className="dq-kpi-value">{loading ? "…" : value}</h3>
          <span className="dq-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="dq-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
      {footer ? <div className="dq-kpi-footer">{footer}</div> : null}
    </article>
  );
}
