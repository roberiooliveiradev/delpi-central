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
    <div className="si-indicator-table__list">
      {indicators.map((indicator) => {
        const displayContext = buildDisplayContext(indicator, viewMode, branch);
        const valueFormat = {
          valueUnit: indicator.valueUnit,
          valuePrefix: indicator.valuePrefix,
          valueSuffix: indicator.valueSuffix,
          valueDecimals: indicator.valueDecimals,
        };

        return (
          <article key={indicator.id} className="si-indicator-table__card">
            <div className="si-indicator-table__card-header">
              <h3 className="si-indicator-table__card-title">
                {indicator.indicatorName}
              </h3>
              <StatusBadge
                label={getStatusLabel(indicator.status)}
                variant={indicator.status}
              />
            </div>

            <div className="si-indicator-table__card-meta">
              <div className="si-indicator-table__meta-item">
                <span>Departamento</span>
                <strong>{indicator.departmentName}</strong>
              </div>

              <div className="si-indicator-table__meta-item">
                <span>Escopo</span>
                <strong>{indicator.viewScopeLabel}</strong>
              </div>

              <div className="si-indicator-table__meta-item">
                <span>Peso interno</span>
                <strong>{indicator.weightPct}%</strong>
              </div>

              <div className="si-indicator-table__meta-item si-indicator-table__meta-item--wide">
                <span>Meta</span>
                <strong>
                  <ScopeMetricBadges
                    values={indicator.goals}
                    format={valueFormat}
                    displayContext={displayContext}
                    layout="compact"
                    maxVisible={3}
                    emptyLabel={formatIndicatorGoalValue(
                      indicator,
                      competence,
                      displayContext,
                    )}
                  />
                </strong>
              </div>

              <div className="si-indicator-table__meta-item">
                <span>Periodicidade</span>
                <strong>
                  {getGoalPeriodicityLabel(indicator.goalPeriodicity)}
                </strong>
              </div>

              <div className="si-indicator-table__meta-item">
                <span>Modo da meta</span>
                <strong>{getGoalModeLabel(indicator.goalMode)}</strong>
              </div>

              <div className="si-indicator-table__meta-item">
                <span>Direção</span>
                <strong>
                  {getPerformanceDirectionLabel(indicator.performanceDirection)}
                </strong>
              </div>

              <div className="si-indicator-table__meta-item">
                <span>Nota atual</span>
                <strong
                  className={
                    !indicator.hasValue
                      ? "si-indicator-table__score--missing"
                      : undefined
                  }
                >
                  {formatIndicatorScore(indicator.score)}
                </strong>
              </div>

              <div className="si-indicator-table__meta-item si-indicator-table__meta-item--wide">
                <span>Valor atual</span>
                <strong>
                  <ScopeMetricBadges
                    values={indicator.realized}
                    format={valueFormat}
                    displayContext={displayContext}
                    layout="compact"
                    maxVisible={3}
                    emptyLabel={formatIndicatorRealizedDisplay(
                      indicator,
                      valueFormat,
                      displayContext,
                    )}
                  />
                </strong>
              </div>

              <div className="si-indicator-table__meta-item si-indicator-table__meta-item--wide">
                <span>Gap</span>
                <strong>
                  <ScopeMetricBadges
                    values={indicator.gaps}
                    format={valueFormat}
                    displayContext={displayContext}
                    layout="compact"
                    maxVisible={3}
                    emptyLabel={formatIndicatorGapDisplay(
                      indicator,
                      valueFormat,
                      displayContext,
                    )}
                  />
                </strong>
              </div>

              {indicator.goalMode === "monthly_curve" ? (
                <div className="si-indicator-table__meta-item">
                  <span>Curva mensal</span>
                  <strong>
                    {indicator.monthlyTargets.length} meses parametrizados
                  </strong>
                </div>
              ) : null}
            </div>

            <div className="si-indicator-table__card-reading">
              <span>Leitura estratégica</span>
              <p>{indicator.strategicDescription}</p>
            </div>
          </article>
        );
      })}
    </div>
  );
}
