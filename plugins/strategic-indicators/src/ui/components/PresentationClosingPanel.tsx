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
          síntese final para reunião da direção
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
          <p>Classificação executiva consolidada do índice global do período.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Direção do período</span>
          <strong>{trendLabel}</strong>
          <p>Comportamento recente do índice e da leitura consolidada da organização.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Área destaque</span>
          <strong>{topDepartment}</strong>
          <p>Departamento com melhor leitura executiva no recorte atual.</p>
        </div>

        <div className="si-presentation-closing__item">
          <span>Risco prioritário</span>
          <strong>{topRisk}</strong>
          <p>Ponto que exige maior atenção imediata na sequência da reunião.</p>
        </div>
      </div>
    </section>
  );
}