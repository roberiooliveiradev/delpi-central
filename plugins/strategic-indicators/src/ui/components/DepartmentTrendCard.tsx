import type { DepartmentTrendItem } from "../../data/mocks/trendsMock";
import { StatusBadge } from "./StatusBadge";

type DepartmentTrendCardProps = {
  department: DepartmentTrendItem;
};

function getLabel(direction: DepartmentTrendItem["direction"]) {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function getVariant(
  direction: DepartmentTrendItem["direction"]
): "success" | "warning" | "neutral" {
  if (direction === "up") return "success";
  if (direction === "down") return "warning";
  return "neutral";
}

export function DepartmentTrendCard({
  department,
}: DepartmentTrendCardProps) {
  const delta = department.current - department.previous;

  return (
    <article className="si-department-trend-card">
      <div className="si-department-trend-card__top">
        <h3 className="si-department-trend-card__title">{department.name}</h3>
        <StatusBadge
          label={getLabel(department.direction)}
          variant={getVariant(department.direction)}
        />
      </div>

      <div className="si-department-trend-card__metrics">
        <div className="si-department-trend-card__metric">
          <span>Atual</span>
          <strong>{department.current.toFixed(1)}</strong>
        </div>

        <div className="si-department-trend-card__metric">
          <span>Anterior</span>
          <strong>{department.previous.toFixed(1)}</strong>
        </div>

        <div className="si-department-trend-card__metric">
          <span>Variação</span>
          <strong>
            {delta > 0 ? "+" : ""}
            {delta.toFixed(1)}
          </strong>
        </div>
      </div>
    </article>
  );
}