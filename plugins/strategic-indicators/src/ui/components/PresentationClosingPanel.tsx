type PresentationClosingPanelProps = {
  currentPeriod: string;
  previousPeriod: string;
  classification: string;
  trendLabel: string;
  topDepartment: string;
  topRisk: string;
};

export function PresentationClosingPanel({
  currentPeriod,
  previousPeriod,
  classification,
  trendLabel,
  topDepartment,
  topRisk,
}: PresentationClosingPanelProps) {
  return (
    <section className="si-presentation-closing">
      <div className="si-presentation-closing__header">
        <h2 className="si-presentation-closing__title">
          Fechamento executivo do período
        </h2>
        <span className="si-presentation-closing__subtitle">
          síntese final para reunião
        </span>
      </div>

      <div className="si-presentation-closing__grid">
        <div className="si-presentation-closing__item">
          <span>Competência analisada</span>
          <strong>{currentPeriod}</strong>
          <p>Comparativo direto com {previousPeriod}.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Leitura do IGD</span>
          <strong>{classification}</strong>
          <p>Classificação executiva consolidada do índice.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Direção do período</span>
          <strong>{trendLabel}</strong>
          <p>Comportamento recente do índice global.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Maior destaque</span>
          <strong>{topDepartment}</strong>
          <p>Área com melhor leitura no recorte atual.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Maior risco</span>
          <strong>{topRisk}</strong>
          <p>Área que exige maior atenção imediata.</p>
        </div>
      </div>
    </section>
  );
}