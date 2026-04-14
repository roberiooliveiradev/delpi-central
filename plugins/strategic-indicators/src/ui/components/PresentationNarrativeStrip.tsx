type PresentationNarrativeStripProps = {
  classification: string;
  topDepartment: string;
  topRisk: string;
  trendLabel: string;
};

export function PresentationNarrativeStrip({
  classification,
  topDepartment,
  topRisk,
  trendLabel,
}: PresentationNarrativeStripProps) {
  return (
    <section className="si-presentation-narrative">
      <div className="si-presentation-narrative__block">
        <span className="si-presentation-narrative__label">
          Leitura executiva
        </span>
        <strong className="si-presentation-narrative__value">
          {classification}
        </strong>
      </div>

      <div className="si-presentation-narrative__block">
        <span className="si-presentation-narrative__label">
          Direção do período
        </span>
        <strong className="si-presentation-narrative__value">
          {trendLabel}
        </strong>
      </div>

      <div className="si-presentation-narrative__block">
        <span className="si-presentation-narrative__label">
          Área destaque
        </span>
        <strong className="si-presentation-narrative__value">
          {topDepartment}
        </strong>
      </div>

      <div className="si-presentation-narrative__block">
        <span className="si-presentation-narrative__label">
          Risco prioritário
        </span>
        <strong className="si-presentation-narrative__value">
          {topRisk}
        </strong>
      </div>
    </section>
  );
}