import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  icon?: ReactNode;
  loading?: boolean;
};

export function KpiCard({ title, value, icon, loading = false }: KpiCardProps) {
  return (
    <article className={`sm-kpi-card${loading ? " sm-kpi-card--loading" : ""}`}>
      <div className="sm-kpi-card__icon" aria-hidden="true">
        {icon}
      </div>
      <div className="sm-kpi-card__body">
        <p className="sm-kpi-card__title">{title}</p>
        <p className="sm-kpi-card__value">{loading ? "…" : value}</p>
      </div>
    </article>
  );
}
