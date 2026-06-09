import type { ReactNode } from "react";

type KpiCardProps = {
  title: string;
  value: string;
  subtitle?: string;
  icon: ReactNode;
  loading?: boolean;
  wide?: boolean;
  valueTone?: "default" | "danger";
};

export function KpiCard({
  title,
  value,
  subtitle,
  icon,
  loading = false,
  wide = false,
  valueTone = "default",
}: KpiCardProps) {
  const valueClassName =
    valueTone === "danger"
      ? "pva-kpi-card__value pva-kpi-card__value--danger"
      : "pva-kpi-card__value";

  return (
    <article
      className={`pva-card pva-kpi-card${wide ? " pva-kpi-card--wide" : ""}`}
    >
      <div className="pva-kpi-card__header">
        <div className="pva-kpi-card__body">
          <p className="pva-kpi-card__title">{title}</p>
          <h3 className={valueClassName}>{loading ? "…" : value}</h3>
          {subtitle ? <span className="pva-kpi-card__subtitle">{subtitle}</span> : null}
        </div>
        <div className="pva-kpi-card__icon" aria-hidden="true">
          {icon}
        </div>
      </div>
    </article>
  );
}
