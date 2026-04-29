import { StatusBadge } from "./StatusBadge";
import "./TrendHeroCard.css";

type TrendHeroCardProps = {
  current: number;
  previous: number;
  classification: string;
  currentPeriod?: string;
  previousPeriod?: string;
};

function getVariation(current: number, previous: number) {
  return current - previous;
}

function getDirectionLabel(current: number, previous: number) {
  const diff = getVariation(current, previous);

  if (diff > 0.09) return "Melhora";
  if (diff < -0.09) return "Queda";
  return "Estável";
}

function getDirectionVariant(
  current: number,
  previous: number,
): "success" | "warning" | "neutral" {
  const diff = getVariation(current, previous);

  if (diff > 0.09) return "success";
  if (diff < -0.09) return "warning";
  return "neutral";
}

function getDirectionClassName(current: number, previous: number) {
  const diff = getVariation(current, previous);

  if (diff > 0.09) return "si-trend-hero si-trend-hero--up";
  if (diff < -0.09) return "si-trend-hero si-trend-hero--down";
  return "si-trend-hero si-trend-hero--stable";
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatVariation(value: number) {
  const formatted = Math.abs(value).toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });

  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;
  return "0,0";
}

export function TrendHeroCard({
  current,
  previous,
  classification,
  currentPeriod,
  previousPeriod,
}: TrendHeroCardProps) {
  const variation = getVariation(current, previous);
  const directionLabel = getDirectionLabel(current, previous);
  const directionVariant = getDirectionVariant(current, previous);

  return (
    <section className={getDirectionClassName(current, previous)}>
      <div className="si-trend-hero__glow" />

      <div className="si-trend-hero__header">
        <div className="si-trend-hero__headline">
          <p className="si-trend-hero__eyebrow">Tendência do IGD</p>
          <h2 className="si-trend-hero__value">{formatScore(current)}</h2>
          <p className="si-trend-hero__classification">{classification}</p>
        </div>

        <StatusBadge label={directionLabel} variant={directionVariant} />
      </div>

      <p className="si-trend-hero__description">
        Leitura temporal do índice global com comparação direta contra o período
        anterior, destacando velocidade de recuperação, queda ou estabilidade do
        desempenho estratégico.
      </p>

      <div className="si-trend-hero__metrics">
        <div className="si-trend-hero__metric">
          <span className="si-trend-hero__metric-label">
            {previousPeriod ? `Anterior · ${previousPeriod}` : "Período anterior"}
          </span>
          <strong className="si-trend-hero__metric-value">
            {formatScore(previous)}
          </strong>
        </div>

        <div className="si-trend-hero__metric">
          <span className="si-trend-hero__metric-label">Variação</span>
          <strong className="si-trend-hero__metric-value">
            {formatVariation(variation)}
          </strong>
        </div>

        <div className="si-trend-hero__metric">
          <span className="si-trend-hero__metric-label">
            {currentPeriod ? `Atual · ${currentPeriod}` : "Direção"}
          </span>
          <strong className="si-trend-hero__metric-value">
            {directionLabel}
          </strong>
        </div>
      </div>
    </section>
  );
}