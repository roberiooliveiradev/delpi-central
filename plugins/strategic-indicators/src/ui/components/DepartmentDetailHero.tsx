import type { DepartmentDetails } from "../../data/types/departmentDetails";
import { StatusBadge } from "./StatusBadge";

type DepartmentDetailHeroProps = {
  department: DepartmentDetails;
};

function getVariant(score: number): "success" | "warning" | "danger" | "info" {
  if (score >= 8) return "success";
  if (score >= 7) return "info";
  if (score >= 6) return "warning";
  return "danger";
}

export function DepartmentDetailHero({
  department,
}: DepartmentDetailHeroProps) {
  return (
    <section className="si-department-hero">
      <div className="si-department-hero__left">
        <p className="si-department-hero__eyebrow">IDD Departamental</p>
        <div className="si-department-hero__title-row">
          <h2 className="si-department-hero__title">{department.name}</h2>
          <StatusBadge
            label={department.classification}
            variant={getVariant(department.score)}
          />
        </div>

        <p className="si-department-hero__summary">
          {department.strategicSummary}
        </p>
      </div>

      <div className="si-department-hero__metrics">
        <div className="si-department-hero__metric">
          <span className="si-department-hero__metric-label">Peso no IGD</span>
          <strong className="si-department-hero__metric-value">
            {department.weightInIgd}%
          </strong>
        </div>

        <div className="si-department-hero__metric">
          <span className="si-department-hero__metric-label">Nota IDD</span>
          <strong className="si-department-hero__metric-value">
            {department.score.toFixed(1)}
          </strong>
        </div>

        <div className="si-department-hero__metric">
          <span className="si-department-hero__metric-label">
            Indicadores no IDD
          </span>
          <strong className="si-department-hero__metric-value">
            {department.indicators.length}
          </strong>
        </div>
      </div>
    </section>
  );
}