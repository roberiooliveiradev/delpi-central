import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  icon: ReactNode;
  loading?: boolean;
};

export function KpiCard({ title, value, icon, loading = false }: KpiCardProps) {
  return (
    <article className="cr-card cr-kpi-card">
      <div className="cr-kpi-card__icon" aria-hidden="true">{icon}</div>
      <div>
        <p className="cr-kpi-card__title">{title}</p>
        <h3 className="cr-kpi-card__value">{loading ? "…" : value}</h3>
      </div>
    </article>
  );
}
