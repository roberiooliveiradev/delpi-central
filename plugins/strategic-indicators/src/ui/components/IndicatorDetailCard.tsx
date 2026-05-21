import type { DepartmentIndicator } from "../../data/types/departmentDetails";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import {
  formatIndicatorGapDisplay,
  formatIndicatorGoalValue,
  formatIndicatorRealizedDisplay,
  formatIndicatorScore,
  isMissingValueClassification,
} from "../shared/indicatorValueFormatter";
import "./IndicatorDetailCard.css";

type IndicatorDetailCardProps = {
  indicator: DepartmentIndicator;
  competence?: string | null;
};

function getValueFormat(indicator: DepartmentIndicator) {
  return {
    valueUnit: indicator.valueUnit,
    valuePrefix: indicator.valuePrefix,
    valueSuffix: indicator.valueSuffix,
    valueDecimals: indicator.valueDecimals,
  };
}

export function IndicatorDetailCard({
  indicator,
  competence,
}: IndicatorDetailCardProps) {
  return (
    <article className="si-indicator-card">
      <div className="si-indicator-card__header">
        <h3 className="si-indicator-card__title">{indicator.name}</h3>
        <span className="si-indicator-card__weight">
          peso {indicator.weightPct}%
        </span>
      </div>

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Meta</span>
        <strong className="si-indicator-card__goal-value">
          {formatIndicatorGoalValue(indicator, competence)}
        </strong>
      </div>

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

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Realizado</span>
        <strong className="si-indicator-card__goal-value">
          {formatIndicatorRealizedDisplay(indicator, getValueFormat(indicator))}
        </strong>
      </div>

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Score</span>
        <strong
          className={`si-indicator-card__goal-value${
            !indicator.hasValue ? " si-indicator-card__goal-value--missing" : ""
          }`}
        >
          {formatIndicatorScore(indicator.score)}
        </strong>
      </div>

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Gap</span>
        <strong
          className={`si-indicator-card__goal-value${
            !indicator.hasValue ? " si-indicator-card__goal-value--missing" : ""
          }`}
        >
          {formatIndicatorGapDisplay(indicator, getValueFormat(indicator))}
        </strong>
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