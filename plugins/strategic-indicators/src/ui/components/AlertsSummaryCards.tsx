import type { AlertsDashboardViewData } from "../../data/types/alerts";
import { StatusBadge } from "./StatusBadge";
import "./AlertsSummaryCards.css";

type AlertsSummaryCardsProps = {
  data: AlertsDashboardViewData;
};

function countBySeverity(
  items: { severity: "high" | "medium" | "low" }[],
  severity: "high" | "medium" | "low"
) {
  return items.filter((item) => item.severity === severity).length;
}

export function AlertsSummaryCards({
  data,
}: AlertsSummaryCardsProps) {
  const allItems = [
    ...data.executiveAlerts,
    ...data.departmentAlerts,
    ...data.indicatorAlerts,
  ];

  const high = countBySeverity(allItems, "high");
  const medium = countBySeverity(allItems, "medium");
  const low = countBySeverity(allItems, "low");

  return (
    <div className="si-alert-summary-grid">
      <article className="si-alert-summary-card">
        <span className="si-alert-summary-card__label">Faixa atual do IGD</span>
        <strong className="si-alert-summary-card__value">
          {data.igdClassification}
        </strong>
        <p className="si-alert-summary-card__text">
          Leitura executiva da condição atual do índice global.
        </p>
      </article>

      <article className="si-alert-summary-card">
        <span className="si-alert-summary-card__label">Criticidade</span>
        <div className="si-alert-summary-card__badges">
          <StatusBadge label={`${high} alta`} variant="danger" />
          <StatusBadge label={`${medium} média`} variant="warning" />
          <StatusBadge label={`${low} baixa`} variant="neutral" />
        </div>
        <p className="si-alert-summary-card__text">
          Distribuição rápida dos alertas executivos, departamentais e analíticos.
        </p>
      </article>

      <article className="si-alert-summary-card">
        <span className="si-alert-summary-card__label">Total de alertas</span>
        <strong className="si-alert-summary-card__value">
          {allItems.length}
        </strong>
        <p className="si-alert-summary-card__text">
          Quantidade total de sinais priorizados no recorte atual.
        </p>
      </article>
    </div>
  );
}