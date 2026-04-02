type PresentationExecutiveStripProps = {
  currentIgd: number;
  previousIgd: number;
  topDepartment: string;
  topRisk: string;
};

export function PresentationExecutiveStrip({
  currentIgd,
  previousIgd,
  topDepartment,
  topRisk,
}: PresentationExecutiveStripProps) {
  const variation = currentIgd - previousIgd;

  return (
    <section className="si-presentation-strip">
      <div className="si-presentation-strip__item">
        <span>IGD atual</span>
        <strong>{currentIgd.toFixed(1)}</strong>
      </div>

      <div className="si-presentation-strip__item">
        <span>Variação</span>
        <strong>
          {variation > 0 ? "+" : ""}
          {variation.toFixed(1)}
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