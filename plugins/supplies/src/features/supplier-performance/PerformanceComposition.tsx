import { scoreLabel } from "./supplierPerformancePresentation";

export function PerformanceComposition({
  quality,
  delivery,
  score,
  qualityPoints,
  deliveryPoints,
  weights,
}: {
  quality: number | null;
  delivery: number | null;
  score: number | null;
  qualityPoints?: number | null;
  deliveryPoints?: number | null;
  weights: { quality_weight: number; delivery_weight: number };
}) {
  return (
    <div className="sp-idf-composition">
      <div className="sp-idf-composition__score">
        <span className="sp-idf-eyebrow">Índice de desempenho</span>
        <div>
          <strong>{scoreLabel(score)}</strong>
          <span> / 100</span>
        </div>
        <p>
          {score == null
            ? "Aguardando base completa"
            : "Qualidade e entrega na mesma escala"}
        </p>
      </div>
      <div className="sp-idf-composition__components">
        <Component
          label="Qualidade"
          kind="quality"
          value={quality}
          points={qualityPoints}
          weight={weights.quality_weight}
        />
        <Component
          label="Entrega"
          kind="delivery"
          value={delivery}
          points={deliveryPoints}
          weight={weights.delivery_weight}
        />
        <p className="sp-idf-caption">
          IDF = (Qualidade × {(weights.quality_weight / 100).toLocaleString("pt-BR")}) + (Entrega ×{" "}
          {(weights.delivery_weight / 100).toLocaleString("pt-BR")})
        </p>
      </div>
    </div>
  );
}

function Component({
  label,
  kind,
  value,
  points,
  weight,
}: {
  label: string;
  kind: string;
  value: number | null;
  points?: number | null;
  weight: number;
}) {
  return (
    <div className={`sp-idf-component sp-idf-component--${kind}`}>
      <div className="sp-idf-component__label">
        <span>
          {label} <small>peso {weight}%</small>
        </span>
        <strong>
          {scoreLabel(value)}
          {value != null ? "%" : ""}
        </strong>
      </div>
      <div
        className="sp-idf-component__track"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value ?? 0}
        aria-valuetext={
          value == null
            ? "Sem base para cálculo"
            : `${scoreLabel(value)} por cento`
        }
      >
        <div style={{ width: `${value ?? 0}%` }} />
      </div>
      {points !== undefined ? (
        <small>
          {points == null
            ? "Sem contribuição calculável"
            : `${scoreLabel(points)} pontos na composição`}
        </small>
      ) : null}
    </div>
  );
}
