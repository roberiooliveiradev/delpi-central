import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { StatusBadge } from "./StatusBadge";
import "./IndicatorPriorityList.css";

type IndicatorPriorityListProps = {
  indicators: IndicatorAnalyticsViewItem[];
};

function getStatusLabel(status: IndicatorAnalyticsViewItem["status"]) {
  if (status === "success") return "Alto desempenho";
  if (status === "info") return "Satisfatório";
  if (status === "warning") return "Exige atenção";
  return "Crítico";
}

export function IndicatorPriorityList({
  indicators,
}: IndicatorPriorityListProps) {
  const prioritized = [...indicators]
    .filter((item) => item.status === "warning" || item.status === "danger")
    .sort((a, b) => a.score - b.score)
    .slice(0, 5);

  if (!prioritized.length) {
    return (
      <div className="si-indicator-priority-list si-indicator-priority-list--empty">
        Nenhum indicador prioritário encontrado para os filtros aplicados.
      </div>
    );
  }

  return (
    <div className="si-indicator-priority-list">
      {prioritized.map((indicator) => (
        <article key={indicator.id} className="si-indicator-priority-item">
          <div className="si-indicator-priority-item__top">
            <div>
              <h3 className="si-indicator-priority-item__title">
                {indicator.indicatorName}
              </h3>
              <p className="si-indicator-priority-item__department">
                {indicator.departmentName}
              </p>
            </div>

            <StatusBadge
              label={getStatusLabel(indicator.status)}
              variant={indicator.status}
            />
          </div>

          <div className="si-indicator-priority-item__meta">
            <span>Peso interno: {indicator.weightPct}%</span>
            <span>Meta: {indicator.goalLabel}</span>
            <span>Nota: {indicator.score.toFixed(1)}</span>
          </div>

          <p className="si-indicator-priority-item__description">
            {indicator.strategicDescription}
          </p>
        </article>
      ))}
    </div>
  );
}