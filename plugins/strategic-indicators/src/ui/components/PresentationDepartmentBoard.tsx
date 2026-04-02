import type { DepartmentTrendItem } from "../../data/mocks/trendsMock";

type PresentationDepartmentBoardProps = {
  departments: DepartmentTrendItem[];
};

function getDirectionLabel(direction: DepartmentTrendItem["direction"]) {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

export function PresentationDepartmentBoard({
  departments,
}: PresentationDepartmentBoardProps) {
  return (
    <section className="si-presentation-board">
      <div className="si-presentation-board__header">
        <h2 className="si-presentation-board__title">Departamentos</h2>
        <span className="si-presentation-board__subtitle">
          leitura executiva do período
        </span>
      </div>

      <div className="si-presentation-department-grid">
        {departments.map((department) => {
          const delta = department.current - department.previous;

          return (
            <article
              key={department.id}
              className="si-presentation-department-card"
            >
              <h3>{department.name}</h3>
              <strong>{department.current.toFixed(1)}</strong>
              <p>
                {getDirectionLabel(department.direction)} ·{" "}
                {delta > 0 ? "+" : ""}
                {delta.toFixed(1)}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}