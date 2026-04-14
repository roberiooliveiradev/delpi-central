type PresentationHeroProps = {
  igd: number;
  classification: string;
  trendLabel: string;
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function PresentationHero({
  igd,
  classification,
  trendLabel,
}: PresentationHeroProps) {
  return (
    <section className="si-presentation-hero">
      <div className="si-presentation-hero__content">
        <p className="si-presentation-hero__eyebrow">Painel Estratégico DELPI</p>
        <h1 className="si-presentation-hero__value">{formatScore(igd)}</h1>
        <p className="si-presentation-hero__classification">{classification}</p>
        <p className="si-presentation-hero__description">
          Síntese executiva do IGD, com leitura consolidada do período e foco
          imediato nos principais movimentos do resultado.
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