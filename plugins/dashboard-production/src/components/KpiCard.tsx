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
    <article className="dp-card dp-kpi-card">
      <div className="dp-kpi-header">
        <div>
          <p className="dp-kpi-title">{title}</p>
          <h3 className="dp-kpi-value">{loading ? "…" : value}</h3>
          <span className="dp-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="dp-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
