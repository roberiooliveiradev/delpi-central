type PresentationClosingPanelProps = {
  currentPeriod: string;
  previousPeriod: string;
  classification: string;
  trendLabel: string;
  topDepartment: string;
  topRisk: string;
  igd: number;
  recommendation: string;
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function PresentationClosingPanel({
  currentPeriod,
  previousPeriod,
  classification,
  trendLabel,
  topDepartment,
  topRisk,
  igd,
  recommendation,
}: PresentationClosingPanelProps) {
  return (
    <section className="si-presentation-closing">
      <div className="si-presentation-closing__hero">
        <article className="si-presentation-closing__headline-card">
          <span className="si-presentation-closing__eyebrow">
            Fechamento do período
          </span>
          <h2 className="si-presentation-closing__title">
            Síntese final pronta para encerramento executivo
          </h2>
          <p className="si-presentation-closing__summary">
            O período encerra com desempenho global em faixa{" "}
            <strong>{classification}</strong>, com leitura de{" "}
            <strong>{trendLabel.toLowerCase()}</strong> entre{" "}
            <strong>{previousPeriod}</strong> e <strong>{currentPeriod}</strong>.
            O destaque positivo permanece em <strong>{topDepartment}</strong>,
            enquanto o principal ponto de atenção continua concentrado em{" "}
            <strong>{topRisk}</strong>.
          </p>
        </article>

        <article className="si-presentation-closing__status-card">
          <span className="si-presentation-closing__eyebrow">
            Status final do IGD
          </span>
          <strong className="si-presentation-closing__status-value">
            {formatScore(igd)}
          </strong>
          <span className="si-presentation-closing__status-classification">
            {classification}
          </span>
          <p className="si-presentation-closing__status-support">
            Tendência observada: {trendLabel.toLowerCase()}.
          </p>
        </article>
      </div>

      <div className="si-presentation-closing__decision-grid">
        <article className="si-presentation-closing__decision-card si-presentation-closing__decision-card--positive">
          <span>Maior ponto positivo</span>
          <strong>{topDepartment}</strong>
          <p>Área com melhor leitura executiva no fechamento atual.</p>
        </article>

        <article className="si-presentation-closing__decision-card si-presentation-closing__decision-card--risk">
          <span>Principal risco</span>
          <strong>{topRisk}</strong>
          <p>Concentra a principal pressão sobre o resultado global.</p>
        </article>

        <article className="si-presentation-closing__decision-card si-presentation-closing__decision-card--action">
          <span>Direcionamento recomendado</span>
          <strong>Ação imediata</strong>
          <p>{recommendation}</p>
        </article>
      </div>
    </section>
  );
}