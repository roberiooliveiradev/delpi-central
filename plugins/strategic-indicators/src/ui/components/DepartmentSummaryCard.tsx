import type { ExecutiveDepartmentSummary } from "../../data/types/executiveSummaryView";
import { StatusBadge } from "./StatusBadge";
import "./DepartmentSummaryCard.css";
type DepartmentSummaryCardProps = {
  department: ExecutiveDepartmentSummary;
};

function getVariant(score: number): "success" | "warning" | "danger" | "info" {
  if (score >= 8) return "success";
  if (score >= 7) return "info";
  if (score >= 6) return "warning";
  return "danger";
}

export function DepartmentSummaryCard({
  department,
}: DepartmentSummaryCardProps) {
  const contribution = department.contribution;
  const variant = getVariant(department.score);

  return (
    <article className="si-department-card">
      <div className="si-department-card__top">
        <div className="si-department-card__identity">
          <span className="si-department-card__short">{department.shortName}</span>
          <div>
            <h3 className="si-department-card__title">{department.name}</h3>
            <p className="si-department-card__weight">
              peso no IGD: {department.weightPct}%
            </p>
          </div>
        </div>

        <StatusBadge label={department.score.toFixed(1)} variant={variant} />
      </div>

      <p className="si-department-card__summary">
        {department.strategicSummary}
      </p>

      <div className="si-department-card__goal">
        <span className="si-department-card__goal-label">Referência executiva</span>
        <strong className="si-department-card__goal-value">
          {department.executiveGoal}
        </strong>
      </div>

      <div className="si-department-card__metrics">
        <div className="si-department-card__metric">
          <span className="si-department-card__metric-label">IDD</span>
          <strong className="si-department-card__metric-value">
            {department.score.toFixed(1)}
          </strong>
        </div>

        <div className="si-department-card__metric">
          <span className="si-department-card__metric-label">Contribuição</span>
          <strong className="si-department-card__metric-value">
            {contribution.toFixed(3)}
          </strong>
        </div>
      </div>

      <div className="si-department-card__indicators">
        <span className="si-department-card__indicators-label">
          Indicadores-chave
        </span>

        <ul className="si-department-card__indicator-list">
          {department.keyIndicators.map((indicator) => (
            <li key={indicator}>{indicator}</li>
          ))}
        </ul>
      </div>
    </article>
  );
}