type PresentationHeroProps = {
  igd: number;
  classification: string;
  trendLabel: string;
};

export function PresentationHero({
  igd,
  classification,
  trendLabel,
}: PresentationHeroProps) {
  return (
    <section className="si-presentation-hero">
      <div className="si-presentation-hero__content">
        <p className="si-presentation-hero__eyebrow">Painel Estratégico DELPI</p>
        <h1 className="si-presentation-hero__value">{igd.toFixed(1)}</h1>
        <p className="si-presentation-hero__classification">{classification}</p>
        <p className="si-presentation-hero__description">
          Síntese executiva do índice global, da tendência recente e das
          prioridades mais relevantes do período.
        </p>
      </div>

      <div className="si-presentation-hero__trend">
        <span className="si-presentation-hero__trend-label">Tendência</span>
        <strong className="si-presentation-hero__trend-value">
          {trendLabel}
        </strong>
      </div>
    </section>
  );
}