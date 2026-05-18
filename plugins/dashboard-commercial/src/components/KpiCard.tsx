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
    <article className="dc-card dc-kpi-card">
      <div className="dc-kpi-header">
        <div>
          <p className="dc-kpi-title">{title}</p>
          <h3 className="dc-kpi-value">{loading ? "…" : value}</h3>
          <span className="dc-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="dc-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
