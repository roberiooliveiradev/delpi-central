import type { DeviceReading } from "../../types/detail";
import {
  formatDateTime,
  formatDeltaValue,
  formatMetricValue,
  primaryMetricKey,
  sourceLabel,
} from "../../utils/detailDisplay";

type ReadingCardProps = {
  reading: DeviceReading;
  metricKey: string | null;
};

export function ReadingCard({ reading, metricKey }: ReadingCardProps) {
  const key = metricKey ?? primaryMetricKey(reading.metrics);
  return (
    <article className="pp-reading-card">
      <header className="pp-reading-card__header">
        <span>{formatDateTime(reading.recordedAt)}</span>
        <span className="pp-reading-card__source">{sourceLabel(reading.source)}</span>
      </header>
      <div className="pp-reading-card__metrics">
        {key ? (
          <>
            <div>
              <span className="pp-reading-card__label">{key}</span>
              <strong>{formatMetricValue(key, reading.metrics[key])}</strong>
            </div>
            <div>
              <span className="pp-reading-card__label">Delta</span>
              <strong>{formatDeltaValue(key, reading.deltaMetrics?.[key])}</strong>
            </div>
          </>
        ) : (
          <p className="pp-detail-muted">Sem métricas nesta leitura.</p>
        )}
      </div>
    </article>
  );
}
