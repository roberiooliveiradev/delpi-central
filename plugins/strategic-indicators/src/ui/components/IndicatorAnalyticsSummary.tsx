import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { StatusBadge } from "./StatusBadge";
import "./IndicatorAnalyticsSummary.css";

type IndicatorAnalyticsSummaryProps = {
  indicators: IndicatorAnalyticsViewItem[];
};

function averageScore(items: IndicatorAnalyticsViewItem[]) {
  if (!items.length) return 0;

  const total = items.reduce((sum, item) => sum + item.score, 0);
  return total / items.length;
}

export function IndicatorAnalyticsSummary({
  indicators,
}: IndicatorAnalyticsSummaryProps) {
  const total = indicators.length;
  const success = indicators.filter((item) => item.status === "success").length;
  const info = indicators.filter((item) => item.status === "info").length;
  const warning = indicators.filter((item) => item.status === "warning").length;
  const danger = indicators.filter((item) => item.status === "danger").length;
  const avg = averageScore(indicators);

  return (
    <div className="si-indicator-summary-grid">
      <article className="si-indicator-summary-card">
        <span className="si-indicator-summary-card__label">
          Total de indicadores
        </span>
        <strong className="si-indicator-summary-card__value">{total}</strong>
        <p className="si-indicator-summary-card__text">
          Total de indicadores oficiais mapeados no MVP analítico.
        </p>
      </article>

      <article className="si-indicator-summary-card">
        <span className="si-indicator-summary-card__label">Nota média</span>
        <strong className="si-indicator-summary-card__value">
          {avg.toFixed(1)}
        </strong>
        <p className="si-indicator-summary-card__text">
          Média atual das notas analíticas exibidas na tabela.
        </p>
      </article>

      <article className="si-indicator-summary-card">
        <span className="si-indicator-summary-card__label">Distribuição</span>
        <div className="si-indicator-summary-card__badges">
          <StatusBadge label={`${success} alto desempenho`} variant="success" />
          <StatusBadge label={`${info} satisfatórios`} variant="info" />
          <StatusBadge label={`${warning} atenção`} variant="warning" />
          <StatusBadge label={`${danger} críticos`} variant="danger" />
        </div>
        <p className="si-indicator-summary-card__text">
          Resumo rápido por faixa de status.
        </p>
      </article>
    </div>
  );
}