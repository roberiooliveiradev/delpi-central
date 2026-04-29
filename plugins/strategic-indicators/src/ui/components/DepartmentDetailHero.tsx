import type { DepartmentDetails } from "../../data/types/departmentDetails";
import { StatusBadge } from "./StatusBadge";
import "./DepartmentDetailHero.css";

type DepartmentDetailHeroProps = {
  department: DepartmentDetails;
};

function getVariant(score: number): "success" | "warning" | "danger" | "info" {
  if (score >= 8) return "success";
  if (score >= 7) return "info";
  if (score >= 6) return "warning";
  return "danger";
}

function getDirectionLabel(direction: string) {
  if (direction === "up") return "Alta";
  if (direction === "down") return "Queda";
  return "Estável";
}

export function DepartmentDetailHero({
  department,
}: DepartmentDetailHeroProps) {
  const variationValue = department.variation.value;
  const variationPrefix = variationValue > 0 ? "+" : "";

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
          <span className="si-department-hero__metric-label">Variação</span>
          <strong className="si-department-hero__metric-value">
            {variationPrefix}
            {variationValue.toFixed(1)}
          </strong>
          <span className="si-department-hero__metric-helper">
            {getDirectionLabel(department.variation.direction)}
          </span>
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