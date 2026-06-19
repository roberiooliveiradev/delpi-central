import type { IndicatorAnalyticsViewItem } from "../../data/types/indicatorAnalyticsView";
import { StatusBadge } from "./StatusBadge";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getPerformanceDirectionLabel,
} from "../presentation/labels";
import {
  formatIndicatorGapDisplay,
  formatIndicatorGoalValue,
  formatIndicatorRealizedDisplay,
  formatIndicatorScore,
  type IndicatorDisplayContext,
} from "../shared/indicatorValueFormatter";
import {
  resolveStrategicIndicatorsBranch,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import { ScopeMetricBadges } from "./ScopeMetricBadges";
import "./IndicatorAnalyticsTable.css";

type IndicatorAnalyticsTableProps = {
  indicators: IndicatorAnalyticsViewItem[];
  competence?: string | null;
  viewMode?: StrategicIndicatorsViewMode;
  branch?: string;
};

function getStatusLabel(status: IndicatorAnalyticsViewItem["status"]) {
  if (status === "success") return "Alto desempenho";
  if (status === "info") return "Satisfatório";
  if (status === "warning") return "Exige atenção";
  return "Crítico";
}

function buildDisplayContext(
  indicator: IndicatorAnalyticsViewItem,
  viewMode: StrategicIndicatorsViewMode,
  branch: string,
): IndicatorDisplayContext {
  return {
    filterViewScopeLabel: indicator.viewScopeLabel,
    activeBranch: resolveStrategicIndicatorsBranch(viewMode, branch),
  };
}

export function IndicatorAnalyticsTable({
  indicators,
  competence,
  viewMode = "consolidated",
  branch = "01",
}: IndicatorAnalyticsTableProps) {
  if (!indicators.length) {
    return (
      <div className="si-indicator-table__empty">
        Nenhum indicador encontrado para os filtros aplicados.
      </div>
    );
  }

  return (
    <div className="si-indicator-table__scroll">
      <div className="si-indicator-table">
        <div className="si-indicator-table__row si-indicator-table__row--head">
          <span>Indicador</span>
          <span>Departamento</span>
          <span>Escopo</span>
          <span>Peso</span>
          <span>Meta</span>
          <span>Periodicidade</span>
          <span>Modo</span>
          <span>Direção</span>
          <span>Nota</span>
          <span>Valor atual</span>
          <span>Gap</span>
          <span>Status</span>
        </div>

        {indicators.map((indicator) => {
          const displayContext = buildDisplayContext(indicator, viewMode, branch);
          const valueFormat = {
            valueUnit: indicator.valueUnit,
            valuePrefix: indicator.valuePrefix,
            valueSuffix: indicator.valueSuffix,
            valueDecimals: indicator.valueDecimals,
          };

          return (
            <div key={indicator.id} className="si-indicator-table__row">
              <div className="si-indicator-table__indicator">
                <strong>{indicator.indicatorName}</strong>
                <span>{indicator.strategicDescription}</span>
              </div>

              <span>{indicator.departmentName}</span>
              <span>{indicator.viewScopeLabel}</span>
              <span>{indicator.weightPct}%</span>

              <span className="si-indicator-table__metrics">
                <ScopeMetricBadges
                  values={indicator.goals}
                  format={valueFormat}
                  displayContext={displayContext}
                  layout="compact"
                  maxVisible={2}
                  emptyLabel={formatIndicatorGoalValue(
                    indicator,
                    competence,
                    displayContext,
                  )}
                />
              </span>

              <span>{getGoalPeriodicityLabel(indicator.goalPeriodicity)}</span>
              <span>
                {indicator.goalMode === "monthly_curve"
                  ? `${getGoalModeLabel(indicator.goalMode)} (${indicator.monthlyTargets.length}m)`
                  : getGoalModeLabel(indicator.goalMode)}
              </span>
              <span className="si-indicator-table__direction">
                {getPerformanceDirectionLabel(indicator.performanceDirection)}
              </span>

              <strong
                className={`si-indicator-table__score${
                  !indicator.hasValue ? " si-indicator-table__score--missing" : ""
                }`}
              >
                {formatIndicatorScore(indicator.score)}
              </strong>

              <span className="si-indicator-table__metrics">
                <ScopeMetricBadges
                  values={indicator.realized}
                  format={valueFormat}
                  displayContext={displayContext}
                  layout="compact"
                  maxVisible={2}
                  emptyLabel={formatIndicatorRealizedDisplay(
                    indicator,
                    valueFormat,
                    displayContext,
                  )}
                />
              </span>

              <span className="si-indicator-table__metrics">
                <ScopeMetricBadges
                  values={indicator.gaps}
                  format={valueFormat}
                  displayContext={displayContext}
                  layout="compact"
                  maxVisible={2}
                  emptyLabel={formatIndicatorGapDisplay(
                    indicator,
                    valueFormat,
                    displayContext,
                  )}
                />
              </span>

              <span className="si-indicator-table__status">
                <StatusBadge
                  label={getStatusLabel(indicator.status)}
                  variant={indicator.status}
                />
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
