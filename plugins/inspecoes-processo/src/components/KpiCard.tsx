import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  subtitle?: string;
  icon?: ReactNode;
};

export function KpiCard({ title, value, subtitle, icon }: KpiCardProps) {
  return (
    <article className="ip-kpi-card">
      <div className="ip-kpi-card__header">
        {icon ? (
          <span className="ip-kpi-card__icon" aria-hidden="true">
            {icon}
          </span>
        ) : null}
        <h3 className="ip-kpi-card__title">{title}</h3>
      </div>
      <p className="ip-kpi-card__value">{value}</p>
      {subtitle ? <p className="ip-kpi-card__subtitle">{subtitle}</p> : null}
    </article>
  );
}
