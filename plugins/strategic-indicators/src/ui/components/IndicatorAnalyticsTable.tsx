import type { IndicatorAnalyticsItem } from "../../data/mocks/indicatorsMock";
import { StatusBadge } from "./StatusBadge";

type IndicatorAnalyticsTableProps = {
  indicators: IndicatorAnalyticsItem[];
  selectedIndicatorId?: string;
  onSelectIndicator: (indicator: IndicatorAnalyticsItem) => void;
};

function getStatusLabel(status: IndicatorAnalyticsItem["status"]) {
  if (status === "success") return "Alto desempenho";
  if (status === "info") return "Satisfatório";
  if (status === "warning") return "Exige atenção";
  return "Crítico";
}

export function IndicatorAnalyticsTable({
  indicators,
  selectedIndicatorId,
  onSelectIndicator,
}: IndicatorAnalyticsTableProps) {
  if (!indicators.length) {
    return (
      <div className="si-indicator-table__empty">
        Nenhum indicador encontrado para os filtros aplicados.
      </div>
    );
  }

  return (
    <div className="si-indicator-table">
      <div className="si-indicator-table__row si-indicator-table__row--head">
        <span>Indicador</span>
        <span>Departamento</span>
        <span>Peso</span>
        <span>Meta 2026</span>
        <span>Nota</span>
        <span>Status</span>
      </div>

      {indicators.map((indicator) => {
        const isSelected = indicator.id === selectedIndicatorId;

        return (
          <button
            key={indicator.id}
            type="button"
            className={`si-indicator-table__row si-indicator-table__row--interactive ${
              isSelected ? "si-indicator-table__row--selected" : ""
            }`}
            onClick={() => onSelectIndicator(indicator)}
          >
            <div className="si-indicator-table__indicator">
              <strong>{indicator.indicatorName}</strong>
              <span>{indicator.strategicDescription}</span>
            </div>

            <span>{indicator.departmentName}</span>
            <span>{indicator.weightPct}%</span>
            <span>{indicator.goal2026}</span>
            <strong className="si-indicator-table__score">
              {indicator.simulatedScore.toFixed(1)}
            </strong>
            <StatusBadge
              label={getStatusLabel(indicator.status)}
              variant={indicator.status}
            />
          </button>
        );
      })}
    </div>
  );
}