import { StatusBadge } from "./StatusBadge";

type TrendHeroCardProps = {
  current: number;
  previous: number;
  classification: string;
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
  previous: number
): "success" | "warning" | "neutral" {
  const diff = getVariation(current, previous);

  if (diff > 0.09) return "success";
  if (diff < -0.09) return "warning";
  return "neutral";
}

export function TrendHeroCard({
  current,
  previous,
  classification,
}: TrendHeroCardProps) {
  const variation = getVariation(current, previous);
  const directionLabel = getDirectionLabel(current, previous);
  const directionVariant = getDirectionVariant(current, previous);

  return (
    <section className="si-trend-hero">
      <div className="si-trend-hero__header">
        <div>
          <p className="si-trend-hero__eyebrow">Tendência do IGD</p>
          <h2 className="si-trend-hero__value">{current.toFixed(1)}</h2>
        </div>

        <StatusBadge label={classification} variant="info" />
      </div>

      <p className="si-trend-hero__description">
        Leitura temporal do índice global com comparação direta contra o período
        anterior.
      </p>

      <div className="si-trend-hero__metrics">
        <div className="si-trend-hero__metric">
          <span className="si-trend-hero__metric-label">Período anterior</span>
          <strong className="si-trend-hero__metric-value">
            {previous.toFixed(1)}
          </strong>
        </div>

        <div className="si-trend-hero__metric">
          <span className="si-trend-hero__metric-label">Variação</span>
          <strong className="si-trend-hero__metric-value">
            {variation > 0 ? "+" : ""}
            {variation.toFixed(1)}
          </strong>
        </div>

        <div className="si-trend-hero__metric">
          <span className="si-trend-hero__metric-label">Direção</span>
          <StatusBadge label={directionLabel} variant={directionVariant} />
        </div>
      </div>
    </section>
  );
}