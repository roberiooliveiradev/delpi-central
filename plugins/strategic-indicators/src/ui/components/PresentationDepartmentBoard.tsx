import { PresentationDepartmentSparkline } from "./PresentationDepartmentSparkline";
import type {
  PresentationDepartmentSnapshot,
  PresentationTrendSnapshot,
} from "../../data/types/presentation";
import "./PresentationDepartmentBoard.css";

type PresentationDepartmentBoardProps = {
  departments: PresentationDepartmentSnapshot[];
  trendDepartments?: PresentationTrendSnapshot["departments"];
};

function formatScore(value: number) {
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
}

function formatPct(value: number) {
  return `${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

function getDirectionLabel(direction: "up" | "down" | "stable") {
  if (direction === "up") return "Melhora";
  if (direction === "down") return "Queda";
  return "Estável";
}

function getDirectionVariant(direction: "up" | "down" | "stable") {
  if (direction === "up") return "success";
  if (direction === "down") return "warning";
  return "neutral";
}

export function PresentationDepartmentBoard({
  departments,
  trendDepartments = [],
}: PresentationDepartmentBoardProps) {
  const rankedDepartments = [...departments].sort((a, b) => b.score - a.score);

  const bestDepartment = rankedDepartments[0] ?? null;
  const criticalDepartment =
    [...rankedDepartments].sort((a, b) => a.score - b.score)[0] ?? null;
  const highestContributionDepartment =
    [...rankedDepartments].sort((a, b) => b.contribution - a.contribution)[0] ??
    null;

  const trendMap = new Map(
    trendDepartments.map((department) => [department.id, department]),
  );

  const maxContribution =
    rankedDepartments.reduce((highest, department) => {
      return Math.max(highest, department.contribution);
    }, 0) || 1;

  return (
    <section className="si-presentation-board">
      <div className="si-presentation-board__header">
        <h2 className="si-presentation-board__title">
          Panorama dos departamentos
        </h2>
        <span className="si-presentation-board__subtitle">
          ranking executivo, contribuição no IGD e direção por área
        </span>
      </div>

      <div className="si-presentation-board__summary-grid">
        <article className="si-presentation-board__summary-card">
          <span>Área destaque</span>
          <strong>{bestDepartment?.name ?? "—"}</strong>
          <p>
            {bestDepartment
              ? `Melhor score do período: ${formatScore(bestDepartment.score)}.`
              : "Sem dados suficientes para identificar a área destaque."}
          </p>
        </article>

        <article className="si-presentation-board__summary-card">
          <span>Principal ponto de atenção</span>
          <strong>{criticalDepartment?.name ?? "—"}</strong>
          <p>
            {criticalDepartment
              ? `Menor score atual do recorte: ${formatScore(criticalDepartment.score)}.`
              : "Sem dados suficientes para identificar a área mais pressionada."}
          </p>
        </article>
      </div>

      <div className="si-contribution-ranking">
        <div className="si-contribution-ranking__header">
          <h3 className="si-contribution-ranking__title">Contribuição no IGD</h3>
          <span className="si-contribution-ranking__subtitle">
            {highestContributionDepartment
              ? `${highestContributionDepartment.name} lidera o impacto atual`
              : "Sem dados disponíveis"}
          </span>
        </div>

        <div className="si-contribution-ranking__list">
          {rankedDepartments.map((department) => {
            const contributionWidth = Math.max(
              10,
              (department.contribution / maxContribution) * 100,
            );

            return (
              <div
                key={`contribution-${department.id}`}
                className="si-contribution-ranking__item"
              >
                <div className="si-contribution-ranking__top">
                  <div className="si-contribution-ranking__identity">
                    <strong>{department.name}</strong>
                    <span>{department.classification}</span>
                  </div>

                  <span className="si-contribution-ranking__value">
                    {formatScore(department.contribution)}
                  </span>
                </div>

                <div className="si-contribution-ranking__bar">
                  <div
                    className="si-contribution-ranking__fill"
                    style={{ width: `${contributionWidth}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="si-department-grid">
        {rankedDepartments.map((department) => {
          const trendDepartment = trendMap.get(department.id);
          const previousScore =
            trendDepartment?.previous ??
            Math.max(0, department.score - department.variation.value);

          const sparklinePoints =
            trendDepartment?.series?.length
              ? trendDepartment.series.map((point) => ({
                  period: point.period,
                  value: point.value,
                }))
              : [
                  { period: "Anterior", value: previousScore },
                  { period: "Atual", value: department.score },
                ];

          return (
            <article key={department.id} className="si-department-card">
              <div className="si-department-card__top">
                <div className="si-department-card__identity">
                  <div className="si-department-card__short">
                    {department.shortName}
                  </div>

                  <div>
                    <h3 className="si-department-card__title">
                      {department.name}
                    </h3>
                    <p className="si-department-card__weight">
                      Peso no IGD: {formatPct(department.weightInIgd)}
                    </p>
                  </div>
                </div>

                <span
                  className={`si-status-badge si-status-badge--${getDirectionVariant(
                    department.variation.direction,
                  )}`}
                >
                  {getDirectionLabel(department.variation.direction)}
                </span>
              </div>

              <div className="si-department-card__metrics">
                <div className="si-department-card__metric">
                  <span className="si-department-card__metric-label">
                    Score atual
                  </span>
                  <strong className="si-department-card__metric-value">
                    {formatScore(department.score)}
                  </strong>
                </div>

                <div className="si-department-card__metric">
                  <span className="si-department-card__metric-label">
                    Período anterior
                  </span>
                  <strong className="si-department-card__metric-value">
                    {formatScore(previousScore)}
                  </strong>
                </div>

                <div className="si-department-card__metric">
                  <span className="si-department-card__metric-label">
                    Variação
                  </span>
                  <strong className="si-department-card__metric-value">
                    {department.variation.value > 0 ? "+" : ""}
                    {formatScore(department.variation.value)}
                  </strong>
                </div>

                <div className="si-department-card__metric">
                  <span className="si-department-card__metric-label">
                    Contribuição
                  </span>
                  <strong className="si-department-card__metric-value">
                    {formatScore(department.contribution)}
                  </strong>
                </div>
              </div>

              <PresentationDepartmentSparkline
                direction={trendDepartment?.direction ?? department.variation.direction}
                points={sparklinePoints}
              />

              <p className="si-department-card__summary">
                {department.strategicSummary}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}