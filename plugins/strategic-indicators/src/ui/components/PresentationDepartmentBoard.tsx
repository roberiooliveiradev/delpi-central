import type { PresentationDepartmentBoardItem } from "../../data/types/presentation";

type PresentationDepartmentBoardProps = {
  departments: PresentationDepartmentBoardItem[];
};

function getDirectionLabel(direction: PresentationDepartmentBoardItem["direction"]) {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function getDirectionVariant(direction: PresentationDepartmentBoardItem["direction"]) {
  if (direction === "up") return "success";
  if (direction === "down") return "warning";
  return "neutral";
}

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

export function PresentationDepartmentBoard({
  departments,
}: PresentationDepartmentBoardProps) {
  const rankedDepartments = [...departments]
    .sort((a, b) => b.current - a.current)
    .slice(0, 6);

  const bestDepartment = rankedDepartments[0] ?? null;
  const needsAttention =
    [...rankedDepartments].sort(
      (a, b) => a.current - a.previous - (b.current - b.previous),
    )[0] ?? null;

  return (
    <section className="si-presentation-board">
      <div className="si-presentation-board__header">
        <h2 className="si-presentation-board__title">Panorama dos departamentos</h2>
        <span className="si-presentation-board__subtitle">
          leitura executiva consolidada do período
        </span>
      </div>

      <div className="si-presentation-board__summary-grid">
        <article className="si-presentation-board__summary-card">
          <span>Área destaque</span>
          <strong>{bestDepartment?.name ?? "—"}</strong>
          <p>
            {bestDepartment
              ? `Melhor score do período: ${formatScore(bestDepartment.current)}.`
              : "Sem dados suficientes para identificar a área destaque."}
          </p>
        </article>

        <article className="si-presentation-board__summary-card">
          <span>Área que exige atenção</span>
          <strong>{needsAttention?.name ?? "—"}</strong>
          <p>
            {needsAttention
              ? "Maior pressão na comparação com o período anterior."
              : "Sem dados suficientes para identificar a área mais pressionada."}
          </p>
        </article>
      </div>

      <div className="si-presentation-department-grid">
        {rankedDepartments.map((department) => {
          const delta = department.current - department.previous;
          const directionLabel = getDirectionLabel(department.direction);
          const variant = getDirectionVariant(department.direction);

          return (
            <article
              key={department.id}
              className="si-presentation-department-card"
              data-variant={variant}
            >
              <div className="si-presentation-department-card__header">
                <h3>{department.name}</h3>
                <strong>{formatScore(department.current)}</strong>
              </div>

              <div className="si-presentation-department-card__meta">
                <p>
                  <strong>Direção:</strong> {directionLabel}
                </p>

                <p>
                  <strong>Variação:</strong> {delta > 0 ? "+" : ""}
                  {formatScore(delta)}
                </p>

                <p>
                  <strong>Período anterior:</strong> {formatScore(department.previous)}
                </p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}