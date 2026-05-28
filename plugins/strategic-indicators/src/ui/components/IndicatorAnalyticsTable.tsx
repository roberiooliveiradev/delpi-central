import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { StatusBadge } from "./StatusBadge";
import {
  formatIndicatorGoalValue,
  formatIndicatorScore,
  type IndicatorDisplayContext,
} from "../shared/indicatorValueFormatter";
import {
  getFilterViewScopeLabel,
  resolveStrategicIndicatorsBranch,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import { ScopeMetricBadges } from "./ScopeMetricBadges";
import "./IndicatorAnalyticsTable.css";

type IndicatorAnalyticsTableProps = {
  indicators: IndicatorAnalyticsViewItem[];
  selectedIndicatorId?: string;
  competence?: string | null;
  viewMode?: StrategicIndicatorsViewMode;
  branch?: string;
  onSelectIndicator: (indicator: IndicatorAnalyticsViewItem) => void;
};

function getStatusLabel(status: IndicatorAnalyticsViewItem["status"]) {
  if (status === "success") return "Alto desempenho";
  if (status === "info") return "Satisfatório";
  if (status === "warning") return "Exige atenção";
  return "Crítico";
}

export function IndicatorAnalyticsTable({
  indicators,
  selectedIndicatorId,
  competence,
  viewMode = "consolidated",
  branch = "01",
  onSelectIndicator,
}: IndicatorAnalyticsTableProps) {
  const displayContext: IndicatorDisplayContext = {
    filterViewScopeLabel: getFilterViewScopeLabel(viewMode, branch),
    activeBranch: resolveStrategicIndicatorsBranch(viewMode, branch),
  };
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
        <span>Escopo</span>
        <span>Peso</span>
        <span>Meta</span>
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
            <span>{indicator.viewScopeLabel}</span>
            <span>{indicator.weightPct}%</span>
            <span>
              <ScopeMetricBadges
                values={indicator.goals}
                format={{
                  valueUnit: indicator.valueUnit,
                  valuePrefix: indicator.valuePrefix,
                  valueSuffix: indicator.valueSuffix,
                  valueDecimals: indicator.valueDecimals,
                }}
                displayContext={displayContext}
                maxVisible={2}
                emptyLabel={formatIndicatorGoalValue(indicator, competence, displayContext)}
              />
            </span>
            <strong
              className={`si-indicator-table__score${
                !indicator.hasValue ? " si-indicator-table__score--missing" : ""
              }`}
            >
              {formatIndicatorScore(indicator.score)}
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