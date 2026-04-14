type PresentationExecutiveStripProps = {
  currentIgd: number;
  previousIgd: number;
  variationValue: number;
  topDepartment: string;
  topRisk: string;
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function PresentationExecutiveStrip({
  currentIgd,
  previousIgd,
  variationValue,
  topRisk,
}: PresentationExecutiveStripProps) {
  return (
    <section className="si-presentation-strip">
      <div className="si-presentation-strip__item">
        <span>IGD atual</span>
        <strong>{formatScore(currentIgd)}</strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>IGD anterior</span>
        <strong>{formatScore(previousIgd)}</strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>Variação</span>
        <strong>
          {variationValue > 0 ? "+" : ""}
          {formatScore(variationValue)}
        </strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>Maior risco</span>
        <strong>{topRisk}</strong>
      </div>
    </section>
  );
}