import type { DepartmentIndicator } from "../../data/mocks/departmentsMock";

type IndicatorDetailCardProps = {
  indicator: DepartmentIndicator;
};

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
        <span className="si-indicator-card__goal-label">Meta 2026</span>
        <strong className="si-indicator-card__goal-value">
          {indicator.goal2026}
        </strong>
      </div>

      <p className="si-indicator-card__description">
        {indicator.strategicDescription}
      </p>
    </article>
  );
}