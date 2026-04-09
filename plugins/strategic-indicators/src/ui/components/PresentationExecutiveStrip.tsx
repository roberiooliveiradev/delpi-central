type PresentationExecutiveStripProps = {
  currentIgd: number;
  previousIgd: number;
  variationValue: number;
  topDepartment: string;
  topRisk: string;
};

export function PresentationExecutiveStrip({
  currentIgd,
  previousIgd,
  variationValue,
  topDepartment,
  topRisk,
}: PresentationExecutiveStripProps) {
  return (
    <section className="si-presentation-strip">
      <div className="si-presentation-strip__item">
        <span>IGD atual</span>
        <strong>{currentIgd.toFixed(1)}</strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>IGD anterior</span>
        <strong>{previousIgd.toFixed(1)}</strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>Variação</span>
        <strong>
          {variationValue > 0 ? "+" : ""}
          {variationValue.toFixed(1)}
        </strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>Melhor área</span>
        <strong>{topDepartment}</strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>Maior risco</span>
        <strong>{topRisk}</strong>
      </div>
    </section>
  );
}