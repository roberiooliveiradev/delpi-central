import type { DepartmentIndicator } from "../../data/types/departmentDetails";

type IndicatorDetailCardProps = {
  indicator: DepartmentIndicator;
};

function formatRealized(realized: Record<string, number>) {
  return Object.entries(realized)
    .map(([key, value]) => `${key}: ${value}`)
    .join(" · ");
}

function getGoalModeLabel(value: DepartmentIndicator["goalMode"]) {
  return value === "monthly_curve" ? "Curva mensal" : "Meta padrão";
}

function getPerformanceDirectionLabel(
  value: DepartmentIndicator["performanceDirection"],
) {
  return value === "lower_is_better"
    ? "Quanto menor, melhor"
    : "Quanto maior, melhor";
}

export function IndicatorDetailCard({
  indicator,
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
          {indicator.goalLabel}
        </strong>
      </div>

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Periodicidade</span>
        <strong className="si-indicator-card__goal-value">
          {indicator.goalPeriodicity}
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
          {formatRealized(indicator.realized)}
        </strong>
      </div>

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Score</span>
        <strong className="si-indicator-card__goal-value">
          {indicator.score.toFixed(2)}
        </strong>
      </div>

      <div className="si-indicator-card__goal">
        <span className="si-indicator-card__goal-label">Gap</span>
        <strong className="si-indicator-card__goal-value">
          {indicator.gap.toFixed(2)}
        </strong>
      </div>

      <p className="si-indicator-card__description">
        {indicator.strategicDescription}
      </p>
    </article>
  );
}