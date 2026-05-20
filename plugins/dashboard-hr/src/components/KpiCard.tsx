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
    <article className="dh-card dh-kpi-card">
      <div className="dh-kpi-header">
        <div>
          <p className="dh-kpi-title">{title}</p>
          <h3 className="dh-kpi-value">{loading ? "…" : value}</h3>
          <span className="dh-kpi-subtitle">{subtitle}</span>
        </div>
        <div className="dh-kpi-icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
