import type { AlertsDashboardViewData } from "../../data/types/alerts";
import { formatIndicatorGoalValue } from "../shared/indicatorValueFormatter";
import { resolveStrategicIndicatorsBranch, getFilterViewScopeLabel } from "../shared/strategicIndicatorsFilters";
import type { StrategicIndicatorsViewMode } from "../shared/strategicIndicatorsFilters";
import { ScopeMetricBadges } from "./ScopeMetricBadges";
import { StatusBadge } from "./StatusBadge";
import "./AlertsPriorityHighlights.css";

type AlertsPriorityHighlightsProps = {
  data: AlertsDashboardViewData;
  competence?: string | null;
  viewMode?: StrategicIndicatorsViewMode;
  branch?: string;
};

export function AlertsPriorityHighlights({
  data,
  competence,
  viewMode = "consolidated",
  branch = "01",
}: AlertsPriorityHighlightsProps) {
  const topDepartment = data.departmentAlerts[0] ?? null;
  const topIndicator = data.indicatorAlerts[0] ?? null;
  const displayContext = {
    filterViewScopeLabel: getFilterViewScopeLabel(viewMode, branch),
    activeBranch: resolveStrategicIndicatorsBranch(viewMode, branch),
  };

  return (
    <div className="si-alert-highlights">
      <article className="si-alert-highlight-card">
        <div className="si-alert-highlight-card__top">
          <span className="si-alert-highlight-card__label">
            Área mais prioritária
          </span>
          <StatusBadge label="Foco executivo" variant="warning" />
        </div>

        {topDepartment ? (
          <>
            <h3 className="si-alert-highlight-card__title">
              {topDepartment.departmentName}
            </h3>
            <p className="si-alert-highlight-card__text">{topDepartment.reason}</p>
            <p className="si-alert-highlight-card__meta">
              Atual: {topDepartment.currentScore.toFixed(1)} · Anterior:{" "}
              {topDepartment.previousScore.toFixed(1)}
            </p>
          </>
        ) : null}
      </article>

      <article className="si-alert-highlight-card">
        <div className="si-alert-highlight-card__top">
          <span className="si-alert-highlight-card__label">
            Indicador mais crítico
          </span>
          <StatusBadge label="Ação prioritária" variant="danger" />
        </div>

        {topIndicator ? (
          <>
            <h3 className="si-alert-highlight-card__title">
              {topIndicator.indicatorName}
            </h3>
            <p className="si-alert-highlight-card__text">
              {topIndicator.departmentName} · {topIndicator.reason}
            </p>
            <p className="si-alert-highlight-card__meta">
              Nota: {topIndicator.simulatedScore.toFixed(1)} · Meta:{" "}
              <ScopeMetricBadges
                values={topIndicator.goals}
                format={{
                  valueUnit: topIndicator.valueUnit,
                  valuePrefix: topIndicator.valuePrefix,
                  valueSuffix: topIndicator.valueSuffix,
                  valueDecimals: topIndicator.valueDecimals,
                }}
                displayContext={displayContext}
                layout="compact"
                maxVisible={2}
                emptyLabel={formatIndicatorGoalValue(topIndicator, competence, displayContext)}
              />
            </p>
          </>
        ) : null}
      </article>
    </div>
  );
}