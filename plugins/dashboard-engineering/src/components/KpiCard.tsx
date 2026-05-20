import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  subtitle: string;
  icon: ReactNode;
  loading?: boolean;
};

export function KpiCard({
  title,
  value,
  subtitle,
  icon,
  loading = false,
}: KpiCardProps) {
  return (
    <article className="ds-card ds-kpi-card">
      <div className="ds-kpi-header">
        <div>
          <p className="ds-kpi-title">{title}</p>
          <h3 className="ds-kpi-value">{loading ? "…" : value}</h3>
          <span className="ds-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="ds-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
