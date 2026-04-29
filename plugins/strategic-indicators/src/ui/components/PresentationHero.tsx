import { PresentationClassificationBand } from "./PresentationClassificationBand";
import "./PresentationHero.css";

type PresentationHeroProps = {
  igd: number;
  classification: string;
  trendLabel: string;
  bestDepartment?: string;
  primaryRisk?: string;
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function buildExecutiveMessage(params: {
  igd: number;
  classification: string;
}) {
  const { igd, classification } = params;

  if (igd < 4) {
    return `O período exige reação imediata. O IGD está em faixa crítica, com leitura executiva de ${classification.toLowerCase()}.`;
  }

  if (igd < 6) {
    return "O desempenho ainda exige ação estruturada. A companhia permanece em zona de atenção e precisa acelerar correções no curto prazo.";
  }

  if (igd < 8) {
    return "O resultado segue competitivo, porém com alertas relevantes. A liderança deve acompanhar os pontos de maior pressão no curto prazo.";
  }

  if (igd < 9) {
    return "A companhia mantém um nível consistente de execução, com desempenho sólido e espaço para evolução seletiva nas áreas de maior impacto.";
  }

  return "O período encerra com leitura de excelência, sustentando uma narrativa positiva de desempenho, disciplina operacional e execução consistente.";
}

function buildOpportunityMessage(bestDepartment?: string) {
  if (!bestDepartment) {
    return "Área com melhor tração operacional no período.";
  }

  return `${bestDepartment} lidera a leitura positiva atual.`;
}

function buildRiskMessage(primaryRisk?: string) {
  if (!primaryRisk) {
    return "Principal ponto de atenção executiva.";
  }

  return `${primaryRisk} exige acompanhamento mais próximo.`;
}

export function PresentationHero({
  igd,
  classification,
  trendLabel,
  bestDepartment,
  primaryRisk,
}: PresentationHeroProps) {
  const executiveMessage = buildExecutiveMessage({
    igd,
    classification,
  });
  const opportunityMessage = buildOpportunityMessage(bestDepartment);
  const riskMessage = buildRiskMessage(primaryRisk);

  return (
    <section className="si-presentation-hero">
      <div className="si-presentation-hero__content">
        <p className="si-presentation-hero__eyebrow">Índice Global Delpi</p>

        <div className="si-presentation-hero__headline-block">
          <div className="si-presentation-hero__headline-copy">
            <h1 className="si-presentation-hero__value">IGD: {formatScore(igd)}</h1>
            <p className="si-presentation-hero__classification">
              {classification}
            </p>
          </div>

          <div className="si-presentation-hero__trend-badge">
            <span className="si-presentation-hero__trend-label">Tendência</span>
            <strong className="si-presentation-hero__trend-value">
              {trendLabel}
            </strong>
          </div>
        </div>

        <p className="si-presentation-hero__description">{executiveMessage}</p>

        <div className="si-presentation-hero__highlights">
          <article className="si-presentation-hero__highlight">
            <span className="si-presentation-hero__highlight-label">
              Vetor positivo
            </span>
            <strong className="si-presentation-hero__highlight-value">
              {bestDepartment || "Sem destaque"}
            </strong>
            <p className="si-presentation-hero__highlight-text">
              {opportunityMessage}
            </p>
          </article>

          <article className="si-presentation-hero__highlight">
            <span className="si-presentation-hero__highlight-label">
              Principal risco
            </span>
            <strong className="si-presentation-hero__highlight-value">
              {primaryRisk || "Monitoramento executivo"}
            </strong>
            <p className="si-presentation-hero__highlight-text">
              {riskMessage}
            </p>
          </article>
        </div>

        <div className="si-presentation-hero__band-shell">
          <PresentationClassificationBand value={igd} />
        </div>
      </div>
    </section>
  );
}