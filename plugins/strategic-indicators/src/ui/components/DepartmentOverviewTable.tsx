import type { DepartmentOverviewViewItem } from "../../data/types/departments";
import { StatusBadge } from "./StatusBadge";

type DepartmentOverviewTableProps = {
  departments: DepartmentOverviewViewItem[];
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

export function DepartmentOverviewTable({
  departments,
}: DepartmentOverviewTableProps) {
  return (
    <div className="si-department-overview">
      <div className="si-department-overview__row si-department-overview__row--head">
        <span>Departamento</span>
        <span>Peso</span>
        <span>IDD</span>
        <span>Variação</span>
        <span>Classificação</span>
        <span>Ação</span>
      </div>

      {departments.map((department) => {
        const variationValue = department.variation.value;
        const variationPrefix = variationValue > 0 ? "+" : "";

        return (
          <div
            key={department.id}
            className="si-department-overview__row"
          >
            <div className="si-department-overview__department">
              <strong>{department.name}</strong>
              <span>{department.strategicSummary}</span>
            </div>

            <span className="si-department-overview__cell">
              {department.weightInIgd}%
            </span>

            <strong className="si-department-overview__score">
              {department.score.toFixed(1)}
            </strong>

            <div className="si-department-overview__variation">
              <strong>
                {variationPrefix}
                {variationValue.toFixed(1)}
              </strong>
              <span>{getDirectionLabel(department.variation.direction)}</span>
            </div>

            <div className="si-department-overview__status">
              <StatusBadge
                label={department.classification}
                variant={getVariant(department.score)}
              />
            </div>

            <div className="si-department-overview__action">
              <a
                href={`/apps/strategic-indicators/departments/${department.id}`}
                className="si-link-button"
              >
                Ver detalhe
              </a>
            </div>
          </div>
        );
      })}
    </div>
  );
}