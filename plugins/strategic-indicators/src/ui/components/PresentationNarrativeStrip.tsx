type PresentationNarrativeStripProps = {
  classification: string;
  trendLabel: string;
  topDepartment?: string;
  topRisk?: string;
  highlightedDepartment?: string;
  riskLabel?: string;
};

function buildPrimaryNarrative(classification: string, trendLabel: string) {
  const normalizedTrend = trendLabel.toLowerCase();

  if (normalizedTrend.includes("queda")) {
    return `${classification} com pressão no período.`;
  }

  if (
    normalizedTrend.includes("alta") ||
    normalizedTrend.includes("melhora") ||
    normalizedTrend.includes("crescimento")
  ) {
    return `${classification} com evolução positiva no período.`;
  }

  return `${classification} com estabilidade no período.`;
}

function buildPositiveNarrative(highlightedDepartment: string) {
  return highlightedDepartment
    ? `${highlightedDepartment} lidera o desempenho atual.`
    : "Há sinais positivos relevantes no período.";
}

function buildRiskNarrative(riskLabel: string) {
  return riskLabel
    ? `${riskLabel} concentra a principal pressão executiva.`
    : "Os riscos seguem distribuídos e exigem acompanhamento.";
}

function buildRecommendationNarrative(params: {
  trendLabel: string;
  highlightedDepartment: string;
  riskLabel: string;
}) {
  const { trendLabel, highlightedDepartment, riskLabel } = params;
  const normalizedTrend = trendLabel.toLowerCase();

  if (normalizedTrend.includes("queda") && riskLabel) {
    return `Atuar primeiro em ${riskLabel.toLowerCase()} e preservar os ganhos de ${highlightedDepartment.toLowerCase()}.`;
  }

  if (
    normalizedTrend.includes("alta") ||
    normalizedTrend.includes("melhora") ||
    normalizedTrend.includes("crescimento")
  ) {
    return `Consolidar o ritmo atual e ampliar as práticas de maior tração.`;
  }

  return "Manter disciplina de acompanhamento e resposta rápida nos pontos críticos.";
}

export function PresentationNarrativeStrip({
  classification,
  trendLabel,
  topDepartment,
  topRisk,
  highlightedDepartment,
  riskLabel,
}: PresentationNarrativeStripProps) {
  const resolvedHighlightedDepartment =
    highlightedDepartment ?? topDepartment ?? "Sem destaque";
  const resolvedRiskLabel = riskLabel ?? topRisk ?? "Monitoramento executivo";

  const primaryNarrative = buildPrimaryNarrative(classification, trendLabel);
  const positiveNarrative = buildPositiveNarrative(
    resolvedHighlightedDepartment,
  );
  const riskNarrative = buildRiskNarrative(resolvedRiskLabel);
  const recommendationNarrative = buildRecommendationNarrative({
    trendLabel,
    highlightedDepartment: resolvedHighlightedDepartment,
    riskLabel: resolvedRiskLabel,
  });

  return (
    <section className="si-presentation-narrative-strip">
      <article className="si-presentation-narrative-strip__item">
        <span className="si-presentation-narrative-strip__label">
          Leitura principal
        </span>
        <strong className="si-presentation-narrative-strip__value">
          {classification}
        </strong>
        <p className="si-presentation-narrative-strip__text">
          {primaryNarrative}
        </p>
      </article>

      <article className="si-presentation-narrative-strip__item">
        <span className="si-presentation-narrative-strip__label">
          Vetor positivo
        </span>
        <strong className="si-presentation-narrative-strip__value">
          {resolvedHighlightedDepartment}
        </strong>
        <p className="si-presentation-narrative-strip__text">
          {positiveNarrative}
        </p>
      </article>

      <article className="si-presentation-narrative-strip__item">
        <span className="si-presentation-narrative-strip__label">
          Vetor de risco
        </span>
        <strong className="si-presentation-narrative-strip__value">
          {resolvedRiskLabel}
        </strong>
        <p className="si-presentation-narrative-strip__text">
          {riskNarrative}
        </p>
      </article>

      <article className="si-presentation-narrative-strip__item">
        <span className="si-presentation-narrative-strip__label">
          Recomendação
        </span>
        <strong className="si-presentation-narrative-strip__value">
          Ação executiva
        </strong>
        <p className="si-presentation-narrative-strip__text">
          {recommendationNarrative}
        </p>
      </article>
    </section>
  );
}