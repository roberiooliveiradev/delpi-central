import type { DataRoutePreviewMetric, DataRoutePreviewPayload } from "./dataRouteSamplePreview";

type Props = {
  payload: DataRoutePreviewPayload;
  className?: string;
};

const KIND_LABELS: Record<DataRoutePreviewPayload["kind"], string> = {
  kpi: "KPI",
  table: "Tabela",
  series: "Série",
};

function SeriesMiniChart({ points }: { points: Array<{ label: string; value: number }> }) {
  const max = Math.max(...points.map((point) => point.value), 1);
  const width = 220;
  const height = 72;
  const pad = 6;
  const step = points.length > 1 ? (width - pad * 2) / (points.length - 1) : 0;
  const coords = points.map((point, index) => {
    const x = pad + index * step;
    const y = height - pad - (point.value / max) * (height - pad * 2);
    return `${x},${y}`;
  });

  return (
    <svg
      className="delpi-ui-data-route-preview__chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Prévia de série"
    >
      <polyline
        fill="none"
        stroke="var(--delpi-ui-accent, #089bdb)"
        strokeWidth="2.5"
        points={coords.join(" ")}
      />
      {points.map((point, index) => {
        const [x, y] = coords[index]!.split(",").map(Number);
        return <circle key={`${point.label}-${index}`} cx={x} cy={y} r="2.5" fill="var(--delpi-ui-accent, #089bdb)" />;
      })}
    </svg>
  );
}

function KpiMetricCard({ metric }: { metric: DataRoutePreviewMetric }) {
  return (
    <div className="delpi-ui-data-route-preview__kpi">
      <span className="delpi-ui-data-route-preview__kpi-label">{metric.label}</span>
      <span className="delpi-ui-data-route-preview__kpi-value">{metric.value}</span>
    </div>
  );
}

function PreviewSlice({
  kind,
  kpi,
  metrics,
  table,
  series,
  compact = false,
}: {
  kind: DataRoutePreviewPayload["kind"];
  kpi?: DataRoutePreviewMetric;
  metrics?: DataRoutePreviewMetric[];
  table?: DataRoutePreviewPayload["table"];
  series?: DataRoutePreviewPayload["series"];
  compact?: boolean;
}) {
  const metricList =
    metrics && metrics.length > 1 ? metrics : kpi ? [kpi] : [];

  return (
    <div
      className={
        compact
          ? "delpi-ui-data-route-preview__slice delpi-ui-data-route-preview__slice--compact"
          : "delpi-ui-data-route-preview__slice"
      }
    >
      {kind === "kpi" && metricList.length > 0 ? (
        <div
          className={
            metricList.length > 1
              ? "delpi-ui-data-route-preview__kpi-grid"
              : "delpi-ui-data-route-preview__kpi-single"
          }
          aria-label={metricList.length > 1 ? "Prévia KPI summary" : "Prévia KPI"}
        >
          {metricList.map((metric, index) => (
            <KpiMetricCard key={`${metric.label}-${index}`} metric={metric} />
          ))}
        </div>
      ) : null}

      {kind === "table" && table ? (
        <div className="delpi-ui-data-route-preview__table-wrap">
          <table className="delpi-ui-data-route-preview__table">
            <thead>
              <tr>
                {table.columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, index) => (
                <tr key={index}>
                  {table.columns.map((column) => (
                    <td key={column.key}>{row[column.key] ?? "—"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {kind === "series" && series ? (
        <div className="delpi-ui-data-route-preview__series">
          <SeriesMiniChart points={series.points} />
          {!compact ? (
            <ul className="delpi-ui-data-route-preview__series-legend">
              {series.points.map((point) => (
                <li key={point.label}>
                  <span>{point.label}</span>
                  <strong>{point.value}</strong>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function DataRouteSamplePreview({ payload, className = "" }: Props) {
  const sourceLabel = payload.source === "live" ? "Resultado do teste" : "Exemplo de uso";
  const extras = payload.extraSlices ?? [];

  return (
    <div
      className={["delpi-ui-data-route-preview", className].filter(Boolean).join(" ")}
      data-source={payload.source}
    >
      <p className="delpi-ui-data-route-catalog__detail-section-label">{sourceLabel}</p>

      {payload.error ? (
        <p className="delpi-ui-data-route-preview__error" role="alert">
          {payload.error}
        </p>
      ) : null}

      {!payload.error ? (
        <PreviewSlice
          kind={payload.kind}
          kpi={payload.kpi}
          metrics={payload.metrics}
          table={payload.table}
          series={payload.series}
        />
      ) : null}

      {!payload.error && extras.length > 0 ? (
        <div className="delpi-ui-data-route-preview__extras">
          <p className="delpi-ui-data-route-preview__extras-label">
            Também disponível nesta fonte (qualquer visual pode usar)
          </p>
          {extras.map((slice) => (
            <section key={slice.kind} className="delpi-ui-data-route-preview__extra">
              <h4 className="delpi-ui-data-route-preview__extra-title">{KIND_LABELS[slice.kind]}</h4>
              <PreviewSlice
                kind={slice.kind}
                kpi={slice.kpi}
                metrics={slice.metrics}
                table={slice.table}
                series={slice.series}
                compact
              />
            </section>
          ))}
        </div>
      ) : null}
    </div>
  );
}
