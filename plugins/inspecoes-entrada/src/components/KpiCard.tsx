import type { ReactNode } from "react";

export type KpiCardVariant = "default" | "info" | "warning" | "success" | "danger";

type KpiCardProps = {
  title: string;
  value: string;
  subtitle?: string;
  icon: ReactNode;
  loading?: boolean;
  variant?: KpiCardVariant;
};

export function KpiCard({
  title,
  value,
  subtitle,
  icon,
  loading = false,
  variant = "default",
}: KpiCardProps) {
  return (
    <article className={`ie-card ie-kpi-card ie-kpi-card--${variant}`}>
      <div className="ie-kpi-card__icon" aria-hidden="true">
        {icon}
      </div>
      <div className="ie-kpi-card__body">
        <p className="ie-kpi-card__title">{title}</p>
        <p className="ie-kpi-card__value">{loading ? "…" : value}</p>
        {subtitle ? <span className="ie-kpi-card__subtitle">{subtitle}</span> : null}
      </div>
    </article>
  );
}
