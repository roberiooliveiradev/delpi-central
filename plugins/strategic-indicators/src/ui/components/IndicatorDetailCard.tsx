import type { DepartmentIndicator } from "../../data/types/departmentDetails";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import {
  isMissingValueClassification,
  type IndicatorDisplayContext,
} from "../shared/indicatorValueFormatter";
import {
  getFilterViewScopeLabel,
  resolveStrategicIndicatorsBranch,
  type StrategicIndicatorsViewMode,
} from "../shared/strategicIndicatorsFilters";
import { IndicatorMetricGoalsGrid } from "./IndicatorMetricGoalsGrid";
import "./IndicatorDetailCard.css";

type IndicatorDetailCardProps = {
  indicator: DepartmentIndicator;
  competence?: string | null;
  viewMode?: StrategicIndicatorsViewMode;
  branch?: string;
};

export function IndicatorDetailCard({
  indicator,
  competence,
  viewMode = "consolidated",
  branch = "",
}: IndicatorDetailCardProps) {
  const displayContext: IndicatorDisplayContext = {
    filterViewScopeLabel: getFilterViewScopeLabel(viewMode, branch),
    activeBranch: resolveStrategicIndicatorsBranch(viewMode, branch),
  };

  return (
    <article className="si-indicator-card">
      <div className="si-indicator-card__header">
        <h3 className="si-indicator-card__title">{indicator.name}</h3>
        <span className="si-indicator-card__weight">
          peso {indicator.weightPct}%
        </span>
      </div>

      <IndicatorMetricGoalsGrid
        indicator={{
          ...indicator,
          goalLabel: indicator.goalLabel,
          goalValue: indicator.goalValue,
          goalMode: indicator.goalMode,
          monthlyTargets: indicator.monthlyTargets,
        }}
        competence={competence}
        displayContext={displayContext}
        scoreLabel="Score"
      />

      <div className="si-indicator-card__metadata">
        <div className="si-indicator-card__goal">
          <span className="si-indicator-card__goal-label">Escopo</span>
          <strong className="si-indicator-card__goal-value">
            {getScopeTypeLabel(indicator.scopeType)}
          </strong>
        </div>

        <div className="si-indicator-card__goal">
          <span className="si-indicator-card__goal-label">Periodicidade</span>
          <strong className="si-indicator-card__goal-value">
            {getGoalPeriodicityLabel(indicator.goalPeriodicity)}
          </strong>
        </div>

        <div className="si-indicator-card__goal">
          <span className="si-indicator-card__goal-label">Modo da meta</span>
          <strong className="si-indicator-card__goal-value">
            {getGoalModeLabel(indicator.goalMode)}
          </strong>
        </div>

        <div className="si-indicator-card__goal">
          <span className="si-indicator-card__goal-label">Direção</span>
          <strong className="si-indicator-card__goal-value">
            {getPerformanceDirectionLabel(indicator.performanceDirection)}
          </strong>
        </div>

        {indicator.goalMode === "monthly_curve" ? (
          <div className="si-indicator-card__goal">
            <span className="si-indicator-card__goal-label">Curva mensal</span>
            <strong className="si-indicator-card__goal-value">
              {indicator.monthlyTargets.length} meses configurados
            </strong>
          </div>
        ) : null}
      </div>

      {!indicator.hasValue ||
      isMissingValueClassification(indicator.classification) ? (
        <p className="si-indicator-card__missing-data">
          Sem dados preenchidos para o período selecionado.
        </p>
      ) : null}

      <p className="si-indicator-card__description">
        {indicator.strategicDescription}
      </p>
    </article>
  );
}
