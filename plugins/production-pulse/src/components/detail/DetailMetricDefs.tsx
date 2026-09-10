import type { DriverMetricDef } from "../../api/productionPulseApi";

type DetailMetricDefsProps = {
  metrics: DriverMetricDef[];
  emptyLabel?: string;
};

export function DetailMetricDefs({
  metrics,
  emptyLabel = "Sem métricas.",
}: DetailMetricDefsProps) {
  if (metrics.length === 0) {
    return <p className="pp-muted">{emptyLabel}</p>;
  }
  return (
    <ul className="pp-detail-metric-list" aria-label="Métricas do driver">
      {metrics.map((metric) => (
        <li key={metric.key} className="pp-detail-metric-row">
          <span className="pp-detail-metric-row__label">
            {metric.labelPt || metric.key}
            {metric.primary ? (
              <span className="pp-detail-metric-row__primary">primária</span>
            ) : null}
          </span>
          <span className="pp-detail-metric-row__meta">
            <code>{metric.key}</code>
            <span aria-hidden>·</span>
            {metric.type}
            {metric.unit ? (
              <>
                <span aria-hidden>·</span>
                {metric.unit}
              </>
            ) : null}
          </span>
        </li>
      ))}
    </ul>
  );
}
