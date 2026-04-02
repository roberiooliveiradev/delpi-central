import type { DepartmentTrendItem } from "../../data/mocks/trendsMock";
import { StatusBadge } from "./StatusBadge";

type TrendPriorityListProps = {
  departments: DepartmentTrendItem[];
};

export function TrendPriorityList({
  departments,
}: TrendPriorityListProps) {
  const priorities = [...departments]
    .filter((department) => department.direction === "down")
    .sort((a, b) => (a.current - a.previous) - (b.current - b.previous));

  if (!priorities.length) {
    return (
      <div className="si-trend-priority-list si-trend-priority-list--empty">
        Nenhuma área em queda no recorte temporal atual.
      </div>
    );
  }

  return (
    <div className="si-trend-priority-list">
      {priorities.map((department) => {
        const delta = department.current - department.previous;

        return (
          <article key={department.id} className="si-trend-priority-item">
            <div className="si-trend-priority-item__top">
              <div>
                <h3 className="si-trend-priority-item__title">{department.name}</h3>
                <p className="si-trend-priority-item__subtitle">
                  Queda frente ao período anterior
                </p>
              </div>

              <StatusBadge label="Acompanhar" variant="warning" />
            </div>

            <div className="si-trend-priority-item__metrics">
              <span>Atual: {department.current.toFixed(1)}</span>
              <span>Anterior: {department.previous.toFixed(1)}</span>
              <span>
                Variação: {delta > 0 ? "+" : ""}
                {delta.toFixed(1)}
              </span>
            </div>
          </article>
        );
      })}
    </div>
  );
}