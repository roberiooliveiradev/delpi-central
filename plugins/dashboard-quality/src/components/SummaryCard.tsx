import type { ReactNode } from "react";

type SummaryMetric = {
  label: string;
  value: string;
};

type SummaryCardProps = {
  title: string;
  description: string;
  icon: ReactNode;
  metrics: SummaryMetric[];
  loading?: boolean;
};

export function SummaryCard({
  title,
  description,
  icon,
  metrics,
  loading = false,
}: SummaryCardProps) {
  return (
    <article className="dq-card dq-summary-card">
      <div className="dq-summary-card__header">
        <div className="dq-summary-card__icon" aria-hidden="true">
          {icon}
        </div>
        <div>
          <h2 className="dq-summary-card__title">{title}</h2>
          <p className="dq-summary-card__description">{description}</p>
        </div>
      </div>

      <dl className="dq-summary-metrics">
        {metrics.map((metric) => (
          <div key={metric.label} className="dq-summary-metric">
            <dt>{metric.label}</dt>
            <dd>{loading ? "…" : metric.value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
