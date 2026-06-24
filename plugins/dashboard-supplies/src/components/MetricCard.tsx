type MetricCardProps = {
  label: string;
  value: string;
  hint?: string;
};

export function MetricCard({ label, value, hint }: MetricCardProps) {
  return (
    <article className="ds-card ds-metric-card">
      <p className="ds-metric-card__label">{label}</p>
      <p className="ds-metric-card__value">{value}</p>
      {hint ? <p className="ds-metric-card__hint">{hint}</p> : null}
    </article>
  );
}
