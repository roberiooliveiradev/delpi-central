type PresentationClassificationBandProps = {
  value: number;
  max?: number;
};

type ClassificationStep = {
  label: string;
  from: number;
  to: number;
};

const CLASSIFICATION_STEPS: ClassificationStep[] = [
  { label: "Crítico", from: 0, to: 6 },
  { label: "Regular, Exige Ação", from: 6, to: 7 },
  { label: "Satisfatório com Alertas", from: 7, to: 8 },
  { label: "Alto Desempenho", from: 8, to: 9 },
  { label: "Excelência Integrada", from: 9, to: 10 },
];

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatRangeValue(value: number) {
  return value.toFixed(1);
}

export function PresentationClassificationBand({
  value,
  max = 10,
}: PresentationClassificationBandProps) {
  const safeValue = clamp(value, 0, max);
  const markerLeft = `${(safeValue / max) * 100}%`;

  return (
    <section className="si-presentation-classification-band">
      <div className="si-presentation-classification-band__header">
        <h3 className="si-presentation-classification-band__title">
          Faixa de classificação
        </h3>
        <strong className="si-presentation-classification-band__value">
          {formatScore(safeValue)}
        </strong>
      </div>

      <div className="si-presentation-classification-band__track">
        <div
          className="si-presentation-classification-band__marker"
          style={{ left: markerLeft }}
          aria-hidden="true"
        />
      </div>

      <div className="si-presentation-classification-band__segments">
        {CLASSIFICATION_STEPS.map((step) => (
          <div
            key={step.label}
            className="si-presentation-classification-band__segment-card"
          >
            <span className="si-presentation-classification-band__segment-label">
              {step.label}
            </span>
            <span className="si-presentation-classification-band__segment-range">
              {formatRangeValue(step.from)}–{formatRangeValue(step.to)}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}